from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import F
from .models import Category, Product, ProductImage, Order, OrderItem, Testimonial


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "preview", "alt_text", "is_primary", "sort_order")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;" />', obj.image.url)
        return "—"
    preview.short_description = "Preview"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "slug", "product_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px;" />', obj.image.url)
        return mark_safe('<div style="height:40px;width:40px;background:#222;border-radius:4px;"></div>')
    thumb.short_description = ""

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


class LowStockFilter(admin.SimpleListFilter):
    title = "stock level"
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return [("low", "Low stock (1–3)"), ("out", "Out of stock"), ("ok", "Well stocked (4+)")]

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(stock__gt=0, stock__lte=3)
        if self.value() == "out":
            return queryset.filter(stock=0)
        if self.value() == "ok":
            return queryset.filter(stock__gt=3)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "brand", "category", "price", "stock_badge", "is_active", "is_featured")
    list_display_links = ("thumb", "name")
    list_editable = ("is_active",)
    list_filter = ("category", "is_active", "is_featured", "brand", LowStockFilter)
    search_fields = ("name", "brand", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    list_per_page = 25
    save_on_top = True
    actions = ["mark_featured", "mark_not_featured", "mark_active", "mark_inactive"]
    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "category", "brand")}),
        ("Description", {"fields": ("description",)}),
        ("Pricing & Stock", {"fields": ("price", "compare_at_price", "stock")}),
        ("Visibility", {"fields": ("is_active", "is_featured")}),
    )

    def thumb(self, obj):
        first = obj.images.first()
        if first:
            return format_html('<img src="{}" style="height:44px;width:44px;object-fit:cover;border-radius:4px;" />', first.image.url)
        return mark_safe('<div style="height:44px;width:44px;background:#222;border-radius:4px;"></div>')
    thumb.short_description = ""

    def stock_badge(self, obj):
        color = "#7f9c6f" if obj.stock > 3 else ("#c6a15b" if obj.stock > 0 else "#b5563f")
        label = f"{obj.stock} in stock" if obj.stock > 0 else "Out of stock"
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, label)
    stock_badge.short_description = "Stock"

    @admin.action(description="Mark selected as Featured")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Remove from Featured")
    def mark_not_featured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description="Mark selected as Active")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected as Inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_name", "unit_price", "quantity", "line_total")
    readonly_fields = ("product_name", "unit_price", "quantity", "line_total")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def line_total(self, obj):
        return f"Rs. {obj.line_total}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "phone", "city", "payment_method",
                     "payment_status_badge", "status_badge", "total", "created_at")
    list_filter = ("status", "payment_status", "payment_method", "city", "created_at")
    search_fields = ("order_number", "customer_name", "phone", "email")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "subtotal", "total", "created_at", "updated_at")
    list_per_page = 30
    date_hierarchy = "created_at"
    save_on_top = True
    actions = ["mark_confirmed", "mark_shipped", "mark_delivered", "mark_cancelled", "mark_paid"]
    fieldsets = (
        ("Order Info", {"fields": ("order_number", "status", "created_at", "updated_at")}),
        ("Customer", {"fields": ("customer_name", "phone", "email", "address", "city")}),
        ("Payment", {"fields": ("payment_method", "payment_status", "payment_reference")}),
        ("Totals", {"fields": ("subtotal", "total")}),
        ("Notes", {"fields": ("notes", "internal_notes")}),
    )

    def status_badge(self, obj):
        colors = {
            "PENDING": "#c6a15b", "CONFIRMED": "#7f9c6f",
            "SHIPPED": "#5b8dc6", "DELIVERED": "#7f9c6f", "CANCELLED": "#b5563f",
        }
        return format_html('<span style="color:{};font-weight:600;">{}</span>', colors.get(obj.status, "#888"), obj.get_status_display())
    status_badge.short_description = "Status"

    def payment_status_badge(self, obj):
        colors = {"UNPAID": "#c6a15b", "PAID": "#7f9c6f", "REFUNDED": "#b5563f"}
        return format_html('<span style="color:{};font-weight:600;">{}</span>', colors.get(obj.payment_status, "#888"), obj.get_payment_status_display())
    payment_status_badge.short_description = "Payment"

    @admin.action(description="Mark as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.exclude(status=Order.Status.CANCELLED).update(status=Order.Status.CONFIRMED)

    @admin.action(description="Mark as Shipped")
    def mark_shipped(self, request, queryset):
        queryset.exclude(status=Order.Status.CANCELLED).update(status=Order.Status.SHIPPED)

    @admin.action(description="Mark as Delivered")
    def mark_delivered(self, request, queryset):
        queryset.exclude(status=Order.Status.CANCELLED).update(status=Order.Status.DELIVERED)

    @admin.action(description="Mark as Paid")
    def mark_paid(self, request, queryset):
        queryset.update(payment_status=Order.PaymentStatus.PAID)

    @admin.action(description="Cancel order(s) and restore stock")
    def mark_cancelled(self, request, queryset):
        restored = 0
        for order in queryset.exclude(status=Order.Status.CANCELLED):
            for item in order.items.all():
                if item.product_id:
                    Product.objects.filter(id=item.product_id).update(stock=F("stock") + item.quantity)
                    restored += 1
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status"])
        self.message_user(request, f"Cancelled order(s) and restored stock for {restored} line item(s).")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "city", "rating", "is_featured", "created_at")
    list_editable = ("is_featured",)
    list_filter = ("rating", "is_featured")
    search_fields = ("customer_name", "quote")
