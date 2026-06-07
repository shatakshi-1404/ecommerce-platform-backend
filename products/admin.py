from django.contrib import admin
from .models import Product, Category, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'stock', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'seller__username']

@admin.register(ProductReview)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'buyer', 'rating']