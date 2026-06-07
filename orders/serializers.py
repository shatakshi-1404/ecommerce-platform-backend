from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(
        source='get_subtotal', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(
        source='get_total', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(
        source='get_subtotal', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'price_at_purchase', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer_name', 'status', 'total_amount',
            'shipping_address', 'razorpay_order_id', 'razorpay_payment_id',
            'is_paid', 'items', 'created_at'
        ]
        read_only_fields = ['buyer_name', 'razorpay_order_id', 'razorpay_payment_id', 'is_paid']