from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.product_list_view, name='home'),
    path('products/', views.product_list_view, name='product_list'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('buy-now/<int:product_id>/', views.buy_now_view, name='buy_now'),
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart_quantity_view, name='update_cart_quantity'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('return-order/<int:order_id>/', views.return_order_view, name='return_order'),
    path('cancel-order/<int:order_id>/', views.cancel_order_view, name='cancel_order'),
    path('add-review/<int:product_id>/', views.add_review_view, name='add_review'),
    path('orders/', views.orders_view, name='orders'),
    path('user-dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('seller-dashboard/', views.seller_dashboard_view, name='seller_dashboard'),
    path('seller/create-product/', views.seller_create_product_view, name='seller_create_product'),
    path('seller/edit-product/<int:product_id>/', views.seller_edit_product_view, name='seller_edit_product'),
    path('seller/delete-product/<int:product_id>/', views.seller_delete_product_view, name='seller_delete_product'),
    path('seller/update-order-status/<int:order_id>/', views.seller_update_order_status_view, name='seller_update_order_status'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('password_reset/', views.custom_password_reset_view, name='password_reset'),
]
