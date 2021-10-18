from django.urls import path
from . import views

urlpatterns = [
    path('exportorders/', views.exportOrders, name='exportOrders'),
    path('exportorderproduct/', views.exportOrderProducts, name='exportOrderProducts'),

]