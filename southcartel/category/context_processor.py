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
	monthly = Order.objects.annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at')).values('month', 'year').annotate(c=Count('id'), amount = Sum('order_total')).values('year','month', 'c', 'amount') 
	# MONTHLY
	strs = pd.DataFrame(monthly)
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
