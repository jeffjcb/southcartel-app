from .models import Category, Brand
from store.models import Product
from django.db.models import Min,Max
from django.db.models import Sum
from accounts.models import Account
import pandas as pd
from django.db.models.functions import ExtractWeek, ExtractYear, ExtractMonth
from django.db.models import Sum, Count
from orders.models import OrderProduct, Order
from django.utils import timezone
import datetime
from accounts.models import RefundRequests
from reports.filters import StockFilter
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



def sales_generation(request):
	try:
		monthly = Order.objects.exclude(status='Cancelled').annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at')).values('month', 'year').annotate(c=Count('id'), amount = Sum('order_total')).values('year','month', 'c', 'amount').order_by('month') 
		# MONTHLY
		strs = pd.DataFrame(monthly)
		strs = strs.sort_values(["year", 'month'])
		# testing
		strs["date"] =  strs["month"].astype(str) +" - "+ strs["year"].astype(str)
		# make to list for charts js to understand
		dfx1 = strs['date'].tolist()
		dfx2 =  strs['amount'].tolist()
		datum = {
		'dfx1' : dfx1,
		'dfx2' : dfx2,
		}
		return datum
	except Exception as e:
		dfx1 = [1,2,3,4,5]
		dfx2 = [1,2,3,4,5]
		datum = {
		'dfx1' : dfx1,
		'dfx2' : dfx2,
		}
		return datum



def total_users(request):
	try:
		recent_orders = Order.objects.all().filter(created_at__range=[datetime.datetime.now(tz=timezone.utc) - datetime.timedelta(days=3),datetime.datetime.now(tz=timezone.utc)])
		orrderrs = Order.objects.all().filter(status="To Ship").order_by('-created_at')
		orrderrs_count = orrderrs.count()

		cacelledt = Order.objects.all().filter(status="Cancelled").order_by('-created_at')
		cacelledt_count = cacelledt.count()

		received_orders = Order.objects.all().filter(status="To Receive").order_by('-created_at')
		received_orders_count = received_orders.count()
		refundrequestsds = RefundRequests.objects.all().filter(processed=False)

		userss = Account.objects.all()
		userss_count = userss.count()


		orrderrs_counts = {
			'orrderrs_count':orrderrs_count,
			'userss_count':userss_count,
			'cacelledt_count':cacelledt_count,
			'recent_orders':recent_orders,
			'orrderrs':orrderrs,
			'received_orders_count':received_orders_count,
			'received_orders':received_orders,
			'refundrequestsds':refundrequestsds,
		}
	except:
		orrderrs_counts = {
		}
	return orrderrs_counts

def partner_dash(request):
	try:
		# BRAND SALES
		# brand_sales = OrderProduct.objects.values('product__brand', 'product__brand__brand_name').annotate(sold = Sum('quantity'), amount = Sum('order__order_total')).order_by('-amount')
		brand_sales = OrderProduct.objects.values('product__brand', 'product__brand__brand_name').annotate(c=Count('id'), amount = Sum('order__order_total')).values('product__brand','product__brand__brand_name', 'c', 'amount')

		bds = pd.DataFrame(brand_sales)
		bds["brand"] =  bds['product__brand__brand_name'].astype(str)
		bfx1 = bds['brand'].tolist()
		bfx2 =  bds['amount'].tolist()

		# STOCKS
		stock_products = Product.objects.all()
		# Filter
		stock_filter = StockFilter(request.GET, queryset =stock_products)
		stock_products = stock_filter.qs
		return {'stock_filter':stock_filter, 'stock_products':stock_products, 'bfx1':bfx1, 'bfx2':bfx2}
	except:
		bfx1 = ['sample1', 'sample1','sample1','sample1']
		bfx1 = [500,121,322,222]
		stock_filter = None
		stock_products = None
		return {'stock_filter':stock_filter, 'stock_products':stock_products, 'bfx1':bfx1, 'bfx2':bfx2}

