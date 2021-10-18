import django_filters
from orders.models import *
from store.models import *
from django_filters import DateFilter

class OrderFilter(django_filters.FilterSet):
    start_date = DateFilter(field_name='created_at', lookup_expr ='gte')
    end_date = DateFilter(field_name='created_at', lookup_expr ='lte')
    class Meta:
        model = OrderProduct
        fields = ['product', 'product__brand__brand_name']
        exclude = ['updated_at', 'order','payment', 'user', 'variations', 'quantity', 'product_price', 'ordered', 'created_at']


class StockFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = ['product_name', 'brand__brand_name']