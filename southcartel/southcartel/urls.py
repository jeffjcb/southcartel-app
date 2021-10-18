"""southcartel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('pos/', views.pos, name='pos'),
    path('searches/', views.searches, name='searches'),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accountsuser/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    # ORDERS
    path('orders/', include('orders.urls')),
    # POS
    path('pos/carts', views.cart, name='pos_cart'),
    path('pos/add_cart/<int:product_id>/', views.add_cart, name='pos_add_cart'),
    path('pos/remove_cart/<int:product_id>/<int:cart_item_id>/', views.remove_cart, name='pos_remove_cart'),
    path('pos/remove_cart_item/<int:product_id>/<int:cart_item_id>/', views.remove_cart_item, name='pos_remove_cart_item'),
    path('pos/checkout/', views.checkout, name='pos_checkout'),
    path('pos/checkout/process', views.payment_process, name='pos_payment_process'),
    # Reports
    path('reports/', include('reports.urls')),
    re_path(r'^media/(?P<path>.*)$',serve, {'document_root':settings.MEDIA_ROOT}),


] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
