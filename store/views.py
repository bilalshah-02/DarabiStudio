from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F
from .models import Product, Category, Order, OrderItem, Testimonial
from .cart import Cart
from .notifications import send_order_emails, send_order_whatsapp


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest = Product.objects.filter(is_active=True)[:12]
    categories = Category.objects.all()[:8]
    testimonials = Testimonial.objects.filter(is_featured=True)[:6]
    return render(request, "store/home.html", {
        "featured": featured, "latest": latest, "categories": categories, "testimonials": testimonials,
    })


def catalog(request):
    products = Product.objects.filter(is_active=True)
    category_slug = request.GET.get("category")
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest")
    categories = Category.objects.all()

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query))

    sort_map = {
        "newest": "-created_at",
        "price_low": "price",
        "price_high": "-price",
        "name": "name",
    }
    products = products.order_by(sort_map.get(sort, "-created_at"))

    active_category_obj = categories.filter(slug=category_slug).first() if category_slug else None

    return render(request, "store/catalog.html", {
        "products": products, "categories": categories, "active_category": category_slug,
        "active_category_obj": active_category_obj, "query": query, "sort": sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, "store/product_detail.html", {"product": product, "related": related})


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    qty = int(request.POST.get("quantity", 1))
    already_in_cart = cart.cart.get(str(product.id), {}).get("quantity", 0)
    if already_in_cart + qty > product.stock:
        messages.error(request, f"Only {product.stock} of {product.name} in stock.")
        return redirect(request.POST.get("next", "cart_detail"))
    cart.add(product, quantity=qty)
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.POST.get("next", "cart_detail"))


def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    return redirect("cart_detail")


def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty = int(request.POST.get("quantity", 1))
    Cart(request).set_quantity(product, qty)
    return redirect("cart_detail")


def cart_detail(request):
    return render(request, "store/cart.html", {"cart": Cart(request)})


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("catalog")

    if request.method == "POST":
        required = ["customer_name", "phone", "address", "city", "payment_method"]
        missing = [f for f in required if not request.POST.get(f, "").strip()]
        if missing:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "store/checkout.html", {
                "cart": cart, "payment_methods": Order.PaymentMethod.choices, "form_data": request.POST,
            })
        if request.POST.get("payment_method") not in Order.PaymentMethod.values:
            messages.error(request, "Please choose a valid payment method.")
            return redirect("checkout")

        try:
            with transaction.atomic():
                # Lock the rows we're about to sell to prevent two customers
                # overselling the same last piece at the same time, and always
                # price from the live database — never trust a price cached
                # in the customer's session cart, in case it changed since.
                product_ids = [item["product"].id for item in cart]
                locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)}

                if len(locked) != len(product_ids):
                    messages.error(request, "One or more items in your cart are no longer available.")
                    return redirect("cart_detail")

                for item in cart:
                    product = locked[item["product"].id]
                    if product.stock < item["quantity"]:
                        messages.error(request, f"Sorry, only {product.stock} of {product.name} left in stock.")
                        return redirect("cart_detail")

                subtotal = sum(locked[item["product"].id].price * item["quantity"] for item in cart)
                city_value = request.POST.get("city").strip()
                delivery_fee = 200 if city_value.lower() == "lahore" else 250
                order = Order.objects.create(
                    customer_name=request.POST.get("customer_name").strip(),
                    phone=request.POST.get("phone").strip(),
                    email=request.POST.get("email", "").strip(),
                    address=request.POST.get("address").strip(),
                    city=city_value,
                    payment_method=request.POST.get("payment_method"),
                    notes=request.POST.get("notes", "").strip(),
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total=subtotal + delivery_fee,
                )
                for item in cart:
                    product = locked[item["product"].id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=item["quantity"],
                    )
                    product.stock = F("stock") - item["quantity"]
                    product.save(update_fields=["stock"])
                cart.clear()
        except KeyError:
            messages.error(request, "Something went wrong with your cart. Please try again.")
            return redirect("cart_detail")

        send_order_emails(order)
        send_order_whatsapp(order)
        return redirect("order_confirmation", order_number=order.order_number)

    return render(request, "store/checkout.html", {"cart": cart, "payment_methods": Order.PaymentMethod.choices})


def track_order(request):
    order = None
    error = None
    steps = []
    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip().upper()
        phone = request.POST.get("phone", "").strip()
        order = Order.objects.filter(order_number=order_number, phone=phone).first()
        if not order:
            error = "No matching order found. Double-check your order number and the phone number used at checkout."
        elif order.status != Order.Status.CANCELLED:
            order_flow = [Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.SHIPPED, Order.Status.DELIVERED]
            current_index = order_flow.index(order.status) if order.status in order_flow else 0
            steps = [{"label": Order.Status(s).label, "done": i <= current_index} for i, s in enumerate(order_flow)]
    return render(request, "store/track_order.html", {"order": order, "error": error, "steps": steps})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "store/order_confirmation.html", {"order": order})


def about(request):
    return render(request, "store/about.html")


def contact(request):
    return render(request, "store/contact.html")


def error_404(request, exception):
    return render(request, "store/404.html", status=404)


def error_500(request):
    return render(request, "store/500.html", status=500)


def privacy_policy(request):
    return render(request, "store/legal/privacy.html")


def terms(request):
    return render(request, "store/legal/terms.html")


def returns_policy(request):
    return render(request, "store/legal/returns.html")


def shipping_policy(request):
    return render(request, "store/legal/shipping.html")
