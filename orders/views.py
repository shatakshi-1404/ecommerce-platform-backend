import razorpay
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from products.models import Product
from users.permissions import IsBuyer
from notifications.tasks import send_order_confirmation_email, check_low_stock

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# ─── Cart Views ───────────────────────────────────────────────

class CartView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """Add item to cart"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=404)

        if product.stock < quantity:
            return Response({'error': f'Only {product.stock} in stock.'}, status=400)

        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartSerializer(cart).data, status=201)

    def delete(self, request):
        """Remove item from cart"""
        item_id = request.data.get('item_id')
        try:
            item = CartItem.objects.get(id=item_id, cart__buyer=request.user)
            item.delete()
            return Response({'message': 'Item removed.'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=404)

# ─── Checkout & Payment ───────────────────────────────────────

class CheckoutView(APIView):
    permission_classes = [IsBuyer]

    def post(self, request):
        """
        Creates a Razorpay order and returns the order_id to the frontend.
        The frontend then opens Razorpay payment modal.
        """
        cart = Cart.objects.filter(buyer=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty.'}, status=400)

        shipping_address = request.data.get('shipping_address', '')
        if not shipping_address:
            return Response({'error': 'Shipping address is required.'}, status=400)

        total = int(cart.get_total() * 100)  # Razorpay needs amount in paise

        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': total,
            'currency': 'INR',
            'payment_capture': '1'  # auto-capture payment
        })

        # Save a pending Order in our DB
        with transaction.atomic():
            order = Order.objects.create(
                buyer=request.user,
                total_amount=cart.get_total(),
                shipping_address=shipping_address,
                razorpay_order_id=razorpay_order['id'],
            )
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_purchase=item.product.price
                )

        return Response({
            'razorpay_order_id': razorpay_order['id'],
            'amount': total,
            'currency': 'INR',
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'order_id': order.id,
        })

class PaymentVerifyView(APIView):
    permission_classes = [IsBuyer]

    def post(self, request):
        """
        Called after user completes Razorpay payment.
        Verifies signature, deducts stock, clears cart.
        """
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')

        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
        except razorpay.errors.SignatureVerificationError:
            return Response({'error': 'Payment verification failed.'}, status=400)

        with transaction.atomic():
            order = Order.objects.get(razorpay_order_id=order_id, buyer=request.user)
            order.razorpay_payment_id = payment_id
            order.is_paid = True
            order.status = 'confirmed'
            order.save()

            # Deduct stock for each item
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                product.save()
                # Trigger low stock check as async Celery task
                check_low_stock.delay(product.id)

            # Clear buyer's cart
            Cart.objects.filter(buyer=request.user).delete()

        # Send confirmation email async
        send_order_confirmation_email.delay(order.id)

        return Response({'message': 'Payment successful! Order confirmed.', 'order_id': order.id})

# ─── Order Management ─────────────────────────────────────────

class BuyerOrderListView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        orders = Order.objects.filter(buyer=request.user).prefetch_related('items__product')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class SellerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Sellers only.'}, status=403)
        # Orders that contain at least one product from this seller
        orders = Order.objects.filter(
            items__product__seller=request.user
        ).distinct().prefetch_related('items__product')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Seller updates their order status"""
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)

        # Only sellers whose products are in this order can update it
        seller_in_order = order.items.filter(product__seller=request.user).exists()
        if not seller_in_order and request.user.role != 'admin':
            return Response({'error': 'Not authorized.'}, status=403)

        new_status = request.data.get('status')
        valid_statuses = ['confirmed', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return Response({'error': f'Invalid status. Choose from {valid_statuses}'}, status=400)

        order.status = new_status
        order.save()
        return Response({'message': f'Order status updated to {new_status}.'})