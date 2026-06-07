from rest_framework import serializers
from .models import Product, Category, ProductReview

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'buyer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['buyer_name', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'seller_name', 'category', 'category_name',
            'name', 'description', 'price', 'stock',
            'image', 'is_active', 'low_stock_threshold',
            'is_low_stock', 'reviews', 'average_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['seller_name', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)