from django.contrib import admin
from category.models import Category, Brand


# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug')

class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('brand_name',)}
    list_display = ('id','brand_name', 'slug')
    
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)




