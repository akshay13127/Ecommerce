from elasticsearch_dsl import Document, Text, Keyword
from .models import Product

class ProductDocument(Document):
    name = Text()
    description = Text()
    price = Keyword()

    class Index:
        name = 'product'