from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Product, Category, ProductReview
from .serializers import ProductSerializer, CategorySerializer, ProductReviewSerializer
from users.permissions import IsSeller, IsAdminUser

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]  # only admin creates/deletes categories

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('seller', 'category')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'seller']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'stock']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsSeller()]

    def perform_create(self, serializer):
        # Automatically assign the logged-in seller as the product owner
        serializer.save(seller=self.request.user)

    def get_queryset(self):
        # Sellers can see their own inactive products too
        if self.request.user.is_authenticated and self.request.user.role == 'seller':
            return Product.objects.filter(seller=self.request.user).select_related('seller', 'category')
        return Product.objects.filter(is_active=True).select_related('seller', 'category')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        product = self.get_object()
        if request.user.role != 'buyer':
            return Response({'error': 'Only buyers can leave reviews.'}, status=403)
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, buyer=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[IsSeller])
    def my_products(self, request):
        products = Product.objects.filter(seller=request.user)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsSeller])
    def low_stock_alerts(self, request):
        """Returns seller's products that are below low_stock_threshold"""
        products = Product.objects.filter(
            seller=request.user,
            stock__lte=F('low_stock_threshold')
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)