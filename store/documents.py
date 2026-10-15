from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from sentence_transformers import SentenceTransformer
from .models import Product
from decimal import Decimal

model = SentenceTransformer('all-MiniLM-L6-v2')

@registry.register_document
class ProductDocument(Document):
    name = fields.TextField(fields={"keyword": {"type": "keyword", "ignore_above": 256}})
    description = fields.TextField(fields={"keyword": {"type": "keyword", "ignore_above": 256}})
    price = fields.FloatField()
    created_at = fields.DateField()
    updated_at = fields.DateField()
    sku = fields.KeywordField()
    # embedding = fields.DenseVectorField(dims=384)

    # Foreign Key to Category
    category = fields.TextField(
        fields={'keyword': fields.KeywordField()}  
    )
    brand = fields.TextField(
        fields={'keyword': fields.KeywordField()}  
    )
    weight = fields.FloatField()
    image_url = fields.KeywordField()

    class Index:
        name = 'products'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 2
        }

    class Django:
        model = Product
        queryset_pagination = 1000

    def prepare_category(self, instance):
        return instance.category.name if instance.category else ''

    def prepare_sku(self, instance):
        return instance.sku

    def prepare_name(self, instance):
        return instance.name

    def prepare_price(self, instance):
        # Ensure the price is a valid Decimal and then convert to float
        if isinstance(instance.price, Decimal):
            return float(instance.price)
        elif hasattr(instance.price, 'to_decimal'):
            # If price is a Decimal128 (e.g., MongoDB)
            return float(instance.price.to_decimal())
        return 0.0

    def prepare_description(self, instance):
        return instance.description

    def prepare_brand(self, instance):
        return instance.brand or "Unknown"
    
    def prepare_weight(self, instance):
        return float(instance.weight) if instance.weight else None

    def prepare_image_url(self, instance):
        return instance.image_url.url if instance.image_url else ''
    
    # def prepare_embedding(self, instance):
    #     text = f"{instance.name} {instance.description}"
    #     embedding = model.encode(text)
    #     return embedding.tolist()

    @classmethod
    def generate_id(cls, object_instance):
        return object_instance.sku
