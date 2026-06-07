from django.urls import path
from .views import (
    CartView, CheckoutView, PaymentVerifyView,
    BuyerOrderListView, SellerOrderListView, UpdateOrderStatusView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('my-orders/', BuyerOrderListView.as_view(), name='buyer-orders'),
    path('seller/orders/', SellerOrderListView.as_view(), name='seller-orders'),
    path('orders/<int:pk>/status/', UpdateOrderStatusView.as_view(), name='update-order-status'),
]