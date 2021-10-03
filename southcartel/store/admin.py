from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, ViewedProduct
import admin_thumbnails
# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','price', 'stock', 'category', 'tags','modified_date','created_date', 'is_available')
    list_editable = ('is_available',)
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline]
    

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product','variation_category', 'variation_value', 'stock', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('variation_category',  'variation_value', 'is_active',)

admin.site.site_header = 'South Cartel'
admin.site.register(Product, ProductAdmin)
admin.site.register(ReviewRating)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ProductGallery)
admin.site.register(ViewedProduct)




