from django.shortcuts import render
from django.http import HttpResponse
from orders.models import *
import csv

# Create your views here.
def exportOrders(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['order_number', 'user', 'address_line_1','region', 'city','order_total', 'created_at' ])

    for record in Order.objects.all().values_list('order_number', 'user', 'address_line_1', 'region', 'city',
                                                   'order_total', 'created_at'):
        record = list(record)
        writer.writerow(record)
    response['Content-Disposition'] = "attachment; filename=Orders.csv"
    return response


def exportOrderProducts(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['order__order_number', 'user', 'product','variations', 'quantity', 'product_price', 'created_at' ])

    for record in OrderProduct.objects.all().values_list('order', 'user', 'product__product_name',
                                                   'variations__variation_value','quantity','product_price', 'created_at'):
        record = list(record)
        writer.writerow(record)
    response['Content-Disposition'] = "attachment; filename=OrderProducts.csv"
    return response