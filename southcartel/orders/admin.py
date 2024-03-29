from django.contrib import admin
from .models import Payment, Order, OrderProduct, ShippingMethod, Vouchers
# Register your models here.

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'variations','quantity', 'product_price', 'ordered')
    extra = 0



class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'full_name', 'phone', 'email', 'region', 'city', 'status', 'order_total','tracking_number', 'created_at']
    list_filter = ['status']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email', 'address_line_1']
    list_editable = ('status', 'tracking_number',)
    list_per_page = 30
    inlines = [OrderProductInline]
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_add_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_delete_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

class PaymentAdmin(admin.ModelAdmin):
    list_per_page = 30
    def has_view_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_add_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_delete_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True


class OrderProductAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_add_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True

    def has_delete_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Staff').exists():
            return True



admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(ShippingMethod)
admin.site.register(Vouchers)

