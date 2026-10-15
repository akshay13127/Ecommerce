from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'variants', ProductVariantViewSet)
router.register(r'inventory', InventoryViewSet)
router.register(r'products', ProductListView, basename='product-list')
# router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', home, name='home'),
    path('products/', product_listing, name='product_listing'),
    path('products/<int:product_id>/', product_detail, name='product_detail'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path("cart-items/", CartItemListCreateView.as_view(), name="cart_items_api"),
    path('cart/<int:pk>/', CartDetailView.as_view(), name='cart-detail'),
    path('cart-page/', cart_view, name='cart-page'),
    path('cart/items/<int:product_id>/update/', CartItemUpdateView.as_view(), name='update_cart_item'),
    path('cart/items/<int:product_id>/delete/', CartItemDeleteView.as_view(), name='delete_cart_item'),
    path('api/semantic-search/', ProductsListView.as_view(), name='semantic_search'),
    path('products/autocomplete/', ProductAutocompleteView.as_view(), name='product-autocomplete'),
    path('products/suggest/', ProductSuggestView.as_view(), name='product-suggest'),

]
