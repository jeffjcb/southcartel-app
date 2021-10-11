from .models import Category, Brand
from store.models import Product
from django.db.models import Min,Max
# so links can be used by all templates
# requested by templates
# returns dictionary of data as context
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links) 

def menu_three(request):
    three = Category.objects.all()[:3]
    return dict(three=three)

def brand_links(request):
    bands = Brand.objects.all()
    bands_count=bands.count()
    band_data={
		'bands':bands,
		'bands_count':bands_count,
	}
    return band_data

def get_filters(request):
	brands=Product.objects.distinct().values('brand__brand_name','brand__id')
	minMaxPrice=Product.objects.aggregate(Min('price'),Max('price'))
	data={
		'brands':brands,
		'minMaxPrice':minMaxPrice,
	}
	return data