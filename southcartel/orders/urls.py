from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('shipping/', views.shipping, name='shipping'),
    path('payments/', views.payments, name='payments'),
    path('payment_process/', views.payment_process, name='payment_process'),
    path('order_complete/', views.order_complete, name='order_complete'),

]