from django.contrib import admin
from .models import (
    Profile, Product, Category, Cart, CartItem, Order, OrderItem,
    DeliveryArea, Review, Wishlist, ShippingAddress,
    StoreFront, ProductVariant, Coupon, UserAddress, VendorOrder, OrderTracking, SellerEarnings
)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role')
    search_fields = ('username', 'email')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'seller_username', 'seller_email', 'stock_count')
    list_filter = ('category', 'seller_username')
    search_fields = ('name', 'description', 'seller_username', 'seller_email')

    def save_model(self, request, obj, form, change):
        if not obj.seller_username:
            obj.seller_username = request.user.username
        if not obj.seller_email:
            obj.seller_email = request.user.email
        super().save_model(request, obj, form, change)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'seller_username', 'seller_email')

    def save_model(self, request, obj, form, change):
        if not obj.seller_username:
            obj.seller_username = request.user.username
        if not obj.seller_email:
            obj.seller_email = request.user.email
        super().save_model(request, obj, form, change)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'selected_size')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'status', 'shipping_address', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('username', 'email', 'id')
    inlines = [OrderItemInline]
    readonly_fields = ('delivery_address_details',)

    def delivery_address_details(self, obj):
        if obj.shipping_address:
            addr = obj.shipping_address
            from django.utils.html import format_html
            return format_html(
                "<strong>Name:</strong> {}<br>"
                "<strong>Phone:</strong> {}<br>"
                "<strong>Address Line 1:</strong> {}<br>"
                "<strong>Address Line 2:</strong> {}<br>"
                "<strong>City:</strong> {}<br>"
                "<strong>State:</strong> {}<br>"
                "<strong>Pincode:</strong> {}",
                addr.full_name,
                addr.phone_number,
                addr.address_line_1,
                addr.address_line_2 or "",
                addr.city,
                addr.state,
                addr.pincode
            )
        return "No delivery address"
    delivery_address_details.short_description = 'Delivery Address Details'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'created_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'city', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('username', 'email', 'full_name', 'city')

    def save_model(self, request, obj, form, change):
        if not obj.username:
            obj.username = request.user.username
        if not obj.email:
            obj.email = request.user.email
        super().save_model(request, obj, form, change)

@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'is_active', 'estimated_days')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'username', 'email', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'username')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')

@admin.register(StoreFront)
class StoreFrontAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'seller_username', 'created_at')
    search_fields = ('store_name', 'seller_username')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'stock_count', 'extra_price')
    list_filter = ('product',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'seller_username', 'discount_percentage', 'active', 'valid_from', 'valid_to')
    list_filter = ('active', 'seller_username')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'city', 'pincode', 'is_default')
    list_filter = ('city', 'is_default')

class VendorOrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'selected_size')
    can_delete = False

@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'seller_username', 'status', 'tracking_number', 'created_at')
    list_filter = ('status', 'seller_username', 'created_at')
    inlines = [VendorOrderItemInline]

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp')

@admin.register(SellerEarnings)
class SellerEarningsAdmin(admin.ModelAdmin):
    list_display = ('seller_username', 'vendor_order', 'amount', 'status', 'paid_at')
    list_filter = ('status', 'seller_username')

