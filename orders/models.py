from django.db import models
from users.models import User
from products.models import Product

class Cart(models.Model):
    buyer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.buyer.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username} — {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    # We store price at purchase time so it doesn't change if seller updates price later

    def get_subtotal(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.id})"