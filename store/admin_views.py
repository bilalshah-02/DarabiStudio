from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Order, Product, OrderItem


@staff_member_required
def dashboard(request):
    now = timezone.now()
    last_30_days = now - timedelta(days=30)

    orders_qs = Order.objects.exclude(status=Order.Status.CANCELLED)

    total_revenue = orders_qs.aggregate(total=Sum("total"))["total"] or 0
    revenue_30d = orders_qs.filter(created_at__gte=last_30_days).aggregate(total=Sum("total"))["total"] or 0
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    unpaid_orders = Order.objects.exclude(status=Order.Status.CANCELLED).filter(payment_status=Order.PaymentStatus.UNPAID).count()

    low_stock = Product.objects.filter(is_active=True, stock__gt=0, stock__lte=3).order_by("stock")
    out_of_stock = Product.objects.filter(is_active=True, stock=0)

    recent_orders = Order.objects.all()[:8]

    best_sellers = (
        OrderItem.objects.exclude(order__status=Order.Status.CANCELLED)
        .values("product_name")
        .annotate(units_sold=Sum("quantity"))
        .order_by("-units_sold")[:5]
    )

    context = {
        "total_revenue": total_revenue,
        "revenue_30d": revenue_30d,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "unpaid_orders": unpaid_orders,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "recent_orders": recent_orders,
        "best_sellers": best_sellers,
        "title": "Dashboard",
    }
    return render(request, "admin/store_dashboard.html", context)


@staff_member_required
def customers(request):
    """Customers aren't a separate model — every order carries the customer's
    details, so this aggregates by phone number (the one field guaranteed at
    every checkout) to build a lightweight customer list without changing
    the existing architecture.
    """
    query = request.GET.get("q", "").strip()

    rows = (
        Order.objects.exclude(status=Order.Status.CANCELLED)
        .values("phone")
        .annotate(orders_count=Count("id"), total_spent=Sum("total"))
        .order_by("-total_spent")
    )

    # Attach the most recent name/email/city seen for each phone number.
    customer_rows = []
    for row in rows:
        phone = row["phone"]
        if query and query.lower() not in phone.lower():
            latest = Order.objects.filter(phone=phone, customer_name__icontains=query).order_by("-created_at").first()
            if not latest:
                continue
        else:
            latest = Order.objects.filter(phone=phone).order_by("-created_at").first()
        if not latest:
            continue
        customer_rows.append({
            "name": latest.customer_name,
            "phone": phone,
            "email": latest.email,
            "city": latest.city,
            "orders_count": row["orders_count"],
            "total_spent": row["total_spent"] or 0,
            "last_order_id": latest.id,
            "last_order_number": latest.order_number,
        })

    context = {"customers": customer_rows, "query": query, "title": "Customers"}
    return render(request, "admin/store_customers.html", context)
