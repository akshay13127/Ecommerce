from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Category, Product, ProductVariant, Inventory
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer, InventorySerializer

# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Product Variant ViewSet
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer

# Inventory ViewSet
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

# Review ViewSet
# class ReviewViewSet(viewsets.ModelViewSet):
#     queryset = Review.objects.all()
#     serializer_class = ReviewSerializer

def home(request):
    featured_products = Product.objects.filter()[:6]  # Get featured products
    categories = Category.objects.all()  # Get all categories
    # promotions = Promotion.objects.all()  # Get all promotions

    context = {
        'featured_products': featured_products,
        'categories': categories,
        # 'promotions': promotions,
    }
    
    return render(request, 'home.html', context)

def product_listing(request):
    products = Product.objects.all()
    return render(request, 'plp.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.exclude(id=product_id)[:4]  # Mock logic
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products
    })



from rest_framework.views import APIView
from rest_framework.response import Response
from elasticsearch_dsl import Q
from .documents import ProductDocument

class ProductSearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        category = request.GET.get("category")
        brand = request.GET.get("brand")
        sort_by = request.GET.get("sort_by", "created_at")  # or price, name
        order = request.GET.get("order", "desc")

        es_query = Q("multi_match", query=query, fields=["name", "description"]) if query else Q("match_all")

        filters = []
        if category:
            filters.append(Q("term", category=category))
        if brand:
            filters.append(Q("term", brand=brand))

        final_query = Q("bool", must=es_query, filter=filters)

        s = ProductDocument.search().query(final_query)

        # Sorting
        if sort_by:
            order_prefix = "-" if order == "desc" else ""
            s = s.sort(f"{order_prefix}{sort_by}")

        response = s.execute()

        products = [
            {
                "id": hit.meta.id,
                "name": hit.name,
                "description": hit.description,
                "price": hit.price,
                "brand": hit.brand,
                "category": hit.category,
                "sku": hit.sku,
            }
            for hit in response
        ]

        return Response(products)
    

from rest_framework import generics, permissions
from .models import Cart
from .serializers import CartSerializer

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem, Product
from .serializers import CartItemSerializer


class CartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemUpdateView(generics.UpdateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product_id = self.kwargs['product_id']
        return CartItem.objects.get(cart=cart, product_id=product_id)

    def patch(self, request, *args, **kwargs):
        cart_item = self.get_object()
        quantity = request.data.get('quantity')
        if quantity is not None and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
            return Response(self.get_serializer(cart_item).data, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

class CartItemDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = self.kwargs['product_id']
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            return Response({'detail': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)
        
class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    

from django.shortcuts import render
from .models import Cart

def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if cart:
        cart_items =CartItem.objects.filter(cart=cart)
        cart_len = len(cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, "cart_len": cart_len})


from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
from .documents import ProductDocument
from .custom_facets import CustomFacetedSearchFilterBackend
from .serializers import ProductListDocumentSerializer
from django_elasticsearch_dsl_drf.pagination import QueryFriendlyPageNumberPagination
from elasticsearch_dsl.query import Q
from django_elasticsearch_dsl_drf.filter_backends import FilteringFilterBackend, OrderingFilterBackend, CompoundSearchFilterBackend, DefaultOrderingFilterBackend
from elasticsearch_dsl.query import Q
from .constants import RANGE_FILTERS, BOOLEAN_FILTERS
from collections import OrderedDict

class FilterManager:
    def build_filters(self, params):
        filters = {}
        for key, value in params.items():
            if not value:
                continue

            if key in RANGE_FILTERS:
                gte, lte = value.split("__")
                filters[key] = Q("range", **{key: {"gte": gte, "lte": lte}})
            elif key in BOOLEAN_FILTERS:
                filters[key] = Q("term", **{key: value.lower() == "true"})
            else:
                filters[key] = Q("terms", **{key: value.split("__")})
        return filters

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet


class ProductListView(BaseDocumentViewSet):
    """The Product List Document view."""
    
    document_uid_field = '_id'
    page_size_query_param = 'size'  # Pagination with size parameter
    document = ProductDocument
    serializer_class = ProductListDocumentSerializer
    pagination_class = QueryFriendlyPageNumberPagination
    lookup_field = 'sku'
    # Filter Backends
    filter_backends = [
        CustomFacetedSearchFilterBackend,
        FilteringFilterBackend,
        OrderingFilterBackend,
        CompoundSearchFilterBackend,
        DefaultOrderingFilterBackend,
    ]
    
    faceted_search_fields = {
        'category': {
            'field': 'category.keyword',
            'type': 'terms',
        },
        'brand': {
            'field': 'brand.keyword',
            'type': 'terms',
        }
    ,
        'size': 'size.keyword',
        'price': {
            'field': 'price',
            'type': 'range',
            'ranges': [
                {"to": 100},
                {"from": 100, "to": 500},
                {"from": 500}
            ]
        },
    }
 

    filter_fields = {# Filter by product status
        'category': 'category',  # Filter by product category
        'brand': 'brand',  # Filter by product brand
        'price': {'field': 'price', 'lookups': ['range', 'exact']},  # Filter by price range or exact match
        'material': 'material',  # Filter by product material
    }
    
    ordering_fields = OrderedDict((field, field) for field in ['price', 'rating', 'name'])# Sorting options: price, rating, name
    ordering = 'price'  # Default sorting by price

    search_fields = ['name', 'description']  # Fields to search within

    post_filter_fields = {  # Filter by product status
        'category': 'category',  # Filter by product category
        'brand': 'brand',  # Filter by product brand
        'price': {'field': 'price', 'lookups': ['range', 'exact']},  # Filter by price range or exact match
        'material': 'material',  # Filter by product material
    }
   
    def get_queryset(self):
        qs = super().get_queryset()
        # # print("🔍 ProductListView.get_queryset called")
        # # print("🔢 Total in ES:", qs.count())
        # # for hit in qs[:3]:
        # #     print("🛒 Hit:", hit.to_dict())
        return qs
        # if self.request.GET.get("disable", False):
        #     queryset = self.search.extra(track_total_hits=True)
        # else:
        #     queryset = self.search.extra(track_total_hits=True).query(Q('term', status=True))
        # queryset.model = self.document.Django.model
        # return queryset
    # def get_queryset(self):
    #     """Get filtered and sorted queryset based on shared filter config."""
    #     queryset = self.search.extra(track_total_hits=True)
    #     # print("Using query_params:", query_params)

    #     # Default filter: status=True (unless "disable" is explicitly passed)
    #     if not self.request.GET.get("disable"):
    #         queryset = queryset.query(Q('term', status=True))

    #     # Build filters using shared FilterManager
    #     manager = FilterManager()
    #     query_params = getattr(self.request, '_filtered_querydict', self.request.GET)
    #     filters = manager.build_filters(query_params)


    #     # Combine all filters into a bool query
    #     if filters:
    #         print(f"Applying filters: {filters}")
    #         filter_query = Q("bool", filter=list(filters.values()))
    #         queryset = queryset.query(filter_query)

    #     queryset.model = self.document.Django.model
    #     return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['facets'] = getattr(self, '_facet_data', {})
        return response

    def get_paginated_response(self, data):
        """Override pagination response."""
        response = self.paginator.get_paginated_response(data)
        if hasattr(self, 'facets'):
            response.data['facets'] = self.facets
        return response





# store/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from store.embedding_utils import SemanticSearchService
from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "products"  # Your Elasticsearch index name

class ProductsListView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.es = Elasticsearch()  # Assuming Elasticsearch is running locally
        self.search_service = SemanticSearchService(self.es, index='products')

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        filters = {
            "category": request.GET.get('category', None),
            "price": request.GET.get('price', None),
        }
        rescore = request.GET.get('rescore', 'false').lower() == 'true'
        include_facets = True #request.GET.get('facets', 'false').lower() == 'true'
        sort = request.GET.get('sort', '')  # New
        page = int(request.GET.get('page', 1))  # New
        per_page = 12  # Show 9 products per page

        try:
            results = self.search_service.search(
                query=query,
                filters=filters,
                rescore=rescore,
                include_facets=include_facets,
                sort=sort,
                page=page,
                per_page=per_page
            )

            hits = results.get('hits', {}).get('hits', [])
            total = results.get('hits', {}).get('total', {}).get('value', 0)
            filtered_hits = []
            for hit in hits:
                source = hit.get("_source", {})
                score = hit.get("_score") or 0
                category = source.get("category", "")
                print(score)

                # if  score >= 0.5:
                filtered_hits.append({
                    "id": source.get("id"),
                    "name": source.get("name", "No title"),
                    "score": score,
                    "category": category,
                    "description": source.get("description"),
                    "price": source.get("price"),
                    "sku": source.get("sku"),
                    "brand": source.get("brand"),
                    "weight": source.get("weight"),
                    "image_url": source.get("image_url")
                })

            facets = results.get('aggregations', {}) if include_facets else {}
            # context['total_pages'] = range(1, paginator.num_pages + 1)
            # context['current_page'] = page_obj.number
            total_pages = (total + per_page - 1) // per_page
            context = {
                'products': filtered_hits,
                'facets': facets,
                'query': query,
                'filters': filters,
                'current_page': page,
                'total_pages': total_pages
            }
            print(context)

            return render(request, 'plp.html', context)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from elasticsearch import Elasticsearch
# from .services import SemanticSearchService


class ProductAutocompleteView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.es = Elasticsearch()
        self.search_service = SemanticSearchService(self.es, index='products')

    def get(self, request):
        prefix = request.GET.get('q', '')
        if not prefix:
            return Response({"error": "Query parameter 'q' is required."}, status=400)
        try:
            suggestions = self.search_service.autocomplete(prefix)
            return Response({"results": suggestions}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ProductSuggestView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.es = Elasticsearch()
        self.search_service = SemanticSearchService(self.es, index='products')

    def get(self, request):
        text = request.GET.get('q', '')
        if not text:
            return Response({"error": "Query parameter 'q' is required."}, status=400)
        try:
            suggestions = self.search_service.suggest(text)
            return Response({"results": suggestions}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# Set up the Elasticsearch client


    # def get(self, request, *args, **kwargs):
    #     query_vector = request.GET.get('q', None)
    #     category_filter = request.GET.get('category', None)
    #     min_score = 0.58  # Adjust this value if needed
    #     size = 10  # Number of results you want to return

    #     # Build the query
    #     search_query = {
    #         "size": size,
    #         "_source": ["id", "name", "description", "category", "price", "embedding"],
    #         "query": {
    #             "bool": {
    #                 "must": [
    #                     {
    #                         "knn": {
    #                             "field": "embedding",
    #                             "query_vector": query_vector,  # The semantic search vector
    #                             "k": 10,
    #                             "num_candidates": 100
    #                         }
    #                     }
    #                 ],
    #                 "filter": []
    #             }
    #         },
    #         "aggs": {
    #             "category": {
    #                 "terms": {
    #                     "field": "category.keyword",  # Ensure category is keyword for aggregation
    #                     "size": 10
    #                 }
    #             },
    #             "price": {
    #                 "range": {
    #                     "field": "price",
    #                     "ranges": [
    #                         {"to": 100.0},
    #                         {"from": 100.0, "to": 500.0},
    #                         {"from": 500.0}
    #                     ]
    #                 }
    #             }
    #         }
    #     }

    #     # Apply category filter if provided
    #     if category_filter:
    #         search_query['query']['bool']['filter'].append({
    #             "term": {
    #                 "category.keyword": category_filter
    #             }
    #         })

    #     # Execute the search
    #     try:
    #         es_response = es.search(index=INDEX_NAME, body=search_query)
    #         results = []
    #         for hit in es_response['hits']['hits']:
    #             results.append({
    #                 "name": hit['_source']['name'],
    #                 "score": hit['_score'],
    #                 "category": hit['_source']['category'],
    #                 "price": hit['_source']['price'],
    #                 "id": hit['_source']['id']
    #             })

    #         # Extract aggregations (facets)
    #         category_agg = es_response['aggregations']['category']['buckets']
    #         price_agg = es_response['aggregations']['price']['buckets']

    #         return Response({
    #             "results": results,
    #             "facets": {
    #                 "category": category_agg,
    #                 "price": price_agg
    #             }
    #         })

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


