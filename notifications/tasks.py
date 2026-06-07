from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_order_confirmation_email(order_id):
    """Sends confirmation email to buyer after successful payment"""
    from orders.models import Order  # import inside task to avoid circular imports
    try:
        order = Order.objects.get(id=order_id)
        buyer = order.buyer
        items_text = "\n".join(
            f"- {item.product.name} x{item.quantity} @ ₹{item.price_at_purchase}"
            for item in order.items.all()
        )
        message = f"""
Hi {buyer.username},

Your order #{order.id} has been confirmed! 🎉

Items:
{items_text}

Total: ₹{order.total_amount}
Shipping to: {order.shipping_address}

Thank you for shopping with us!
        """
        send_mail(
            subject=f"Order Confirmed — #{order.id}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[buyer.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email failed for order {order_id}: {e}")

@shared_task
def check_low_stock(product_id):
    """Alerts seller if product stock is below threshold"""
    from products.models import Product
    try:
        product = Product.objects.get(id=product_id)
        if product.is_low_stock():
            seller = product.seller
            send_mail(
                subject=f"Low Stock Alert: {product.name}",
                message=f"""
Hi {seller.username},

Your product "{product.name}" is running low on stock.

Current stock: {product.stock} units
Threshold: {product.low_stock_threshold} units

Please restock soon to avoid missing orders.
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller.email],
                fail_silently=False,
            )
    except Exception as e:
        print(f"Low stock alert failed for product {product_id}: {e}")

@shared_task
def send_daily_seller_report():
    """
    Scheduled task — runs every day via Celery Beat.
    Sends each seller their daily order summary.
    """
    from users.models import User
    from orders.models import Order
    from django.utils import timezone
    from datetime import timedelta

    yesterday = timezone.now() - timedelta(days=1)
    sellers = User.objects.filter(role='seller')

    for seller in sellers:
        orders = Order.objects.filter(
            items__product__seller=seller,
            created_at__gte=yesterday,
            is_paid=True
        ).distinct()

        if not orders.exists():
            continue

        total_revenue = sum(
            item.get_subtotal()
            for order in orders
            for item in order.items.filter(product__seller=seller)
        )

        send_mail(
            subject="Your Daily Sales Report",
            message=f"""
Hi {seller.username},

Here's your summary for {yesterday.date()}:

Orders received: {orders.count()}
Total revenue: ₹{total_revenue}

Keep it up!
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[seller.email],
            fail_silently=True,
        )