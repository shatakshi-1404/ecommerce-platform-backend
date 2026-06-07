from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('buyer', 'Buyer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def is_seller(self):
        return self.role == 'seller'

    def is_buyer(self):
        return self.role == 'buyer'

    def is_admin(self):
        return self.role == 'admin'

    def __str__(self):
        return f"{self.username} ({self.role})"