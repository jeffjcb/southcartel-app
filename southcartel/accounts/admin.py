from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile, RefundRequests, FavoriteItem, Preferences

# Register your models here.


class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'phone_number', 'last_login', 'date_joined', 'is_active')
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    ordering = ('date_joined',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'district', 'province', 'country')


class PreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating')

admin.site.register(Account,AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(RefundRequests)
admin.site.register(FavoriteItem)
admin.site.register(Preferences,PreferencesAdmin)