from rest_framework import serializers, viewsets
from .models import *

# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

# Product Variant Serializer
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"

# Inventory Serializer
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = "__all__"

# Review Serializer
# class ProductReviewSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductReview
#         fields = "__all__"




# serializers.py
from rest_framework import serializers
from .models import Cart, CartItem # Adjust path if needed

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'created_at']
        read_only_fields = ['user', 'total', 'created_at']

    def get_total(self, obj):
        return obj.total()


    
from rest_framework import serializers
from .documents import ProductDocument
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer


class  ProductListDocumentSerializer(DocumentSerializer):
    """Serializer for product listing view."""
    
    class Meta:
        document = ProductDocument
        fields = ['sku', 'name', 'description', 'price', 'category', 'brand', 'image_url']
        # You can add more fields based on your model

