from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/', views.resetPassword, name='resetPassword'),

    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order_tracking/', views.order_tracking, name='order_tracking'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('request_refund/', views.request_refund, name='request_refund'),
    path('send_refund_request/', views.send_refund_request, name='send_refund_request'),

    path('favorites/', views.favorites, name='favorites'),
    path('add_favorites/', views.add_favorites, name='add_favorites'),
    path('remove_favorites/<int:product_id>/<int:favorite_item_id>/', views.remove_favorites, name='remove_favorites'),
]