from django.urls import path
from . import views, qr_views

app_name = 'commande'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('place-order/', views.place_order, name='place_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/status/', views.order_status_json, name='order_status_json'),
    path('staff/dashboard/', views.dashboard, name='dashboard'),
    path('staff/order/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('staff/item/<int:item_id>/toggle/', views.toggle_item_available, name='toggle_item_available'),
    path('staff/qr/', qr_views.qr_display, name='qr_display'),
    path('staff/qr/download/', qr_views.qr_download, name='qr_download'),
]
