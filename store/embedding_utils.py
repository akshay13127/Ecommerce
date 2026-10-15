# store/embedding_utils.py

from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from .models import *

model = SentenceTransformer('all-MiniLM-L6-v2')
es = Elasticsearch("http://localhost:9200")

INDEX_NAME = "products"

def create_semantic_index():
    mapping = {
        "settings": {
            "analysis": {
                "filter": {
                    "autocomplete_filter": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20
                    }
                },
                "analyzer": {
                    "autocomplete_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "autocomplete_filter"
                        ]
                    },
                    "autocomplete_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "autocomplete_analyzer",
                    "search_analyzer": "autocomplete_search_analyzer",
                    "fields": {
                        "suggest": {
                            "type": "completion"
                        }
                    }
                },
                "description": {"type": "text"},
                "price": {"type": "float"},
                "sku": {"type": "keyword"},
                "category": {"type": "keyword"},
                "brand": {"type": "keyword"},
                "weight": {"type": "float"},
                "image_url": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)

    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"✅ Created index `{INDEX_NAME}` with autocomplete and suggest support")



def index_all_products():
    for product in Product.objects.select_related('category').all():
        text = f"{product.name} {product.description}"
        embedding = model.encode(text).tolist()

        doc = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": ensure_decimal(product.price),
            "sku": product.sku,
            "category": product.category.name if product.category else None,
            "brand": product.brand,
            "weight": float(product.weight) if product.weight else None,
            "image_url": product.image_url.url if product.image_url else None,
            "embedding": embedding,
            "suggest": {
                "input": [product.name]  # for the completion suggester
            }
        }

        es.index(index=INDEX_NAME, id=str(product.id), body=doc)

    print("✅ All products indexed with embeddings and suggest field.")




from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text):
    return model.encode(text).tolist()



import time
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from .embedding_utils import generate_embedding  # Assuming you have a utility for this

# Logger setup
logger = logging.getLogger(__name__)

class SemanticSearchService:
    def __init__(self, es: Elasticsearch, index: str):
        self.es = es
        self.index = index

    def search(self, query: str, filters=None, k=50, rescore=False, include_facets=False, sort=None, page=1, per_page=9):
        start_time = time.time()
        try:
            embedding = generate_embedding(query)
            from_ = (page - 1) * per_page
            es_query = self.build_query(query, embedding, filters, k, rescore, include_facets, sort)
            response = self.es.search(index=self.index, body=es_query, size=per_page, from_=from_)
            duration = time.time() - start_time
            logger.info(f"Search took {duration:.3f}s")
            return response
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise

    def build_query(self, query, embedding, filters, k, rescore, include_facets, sort=None):
        es_query = {
            "knn": {
                "field": "embedding",
                "k": k,
                "num_candidates": 100,
                "query_vector": embedding,
                "filter": self.apply_filters(filters)
            },
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "name": query
                            }
                        }
                    ]
                }
            }
        }

        if sort:
            if sort == "price_asc":
                es_query["sort"] = [{"price": {"order": "asc"}}]
            elif sort == "price_desc":
                es_query["sort"] = [{"price": {"order": "desc"}}]
            elif sort == "newest":
                es_query["sort"] = [{"created_at": {"order": "desc"}}]

        # Optional facet aggregations
        if include_facets:
            es_query["aggs"] = self.build_facets(filters)

        import json
        # print(json.dumps(es_query, indent=2))
        return es_query


    def apply_filters(self, filters):
        """Apply filters like category, price range, brand, etc."""
        filter_list = []
        if not filters:
            return filter_list

        for field, value in filters.items():
            if value is None:
                continue

            if field == "price":
                # Handle price range if needed in future
                try:
                    price = float(value)
                    filter_list.append({
                        "range": {
                            "price": {
                                "lte": price
                            }
                        }
                    })
                except ValueError:
                    pass
            else:
                # For category, brand, or any other keyword fields
                filter_list.append({
                    "term": {
                        field: value
                    }
                })

        return filter_list



    def build_facets(self, filters):
        """Generate aggregations for facets."""
        aggs = {}
        if filters and 'category' in filters:
            aggs['category'] = {
                "terms": {"field": "category", "size": 10}  # Use the .keyword subfield
            }
        if filters and 'price' in filters:
            aggs['price'] = {
                "range": {
                    "field": "price",
                    "ranges": [{"to": 100}, {"from": 100, "to": 500}, {"from": 500}]
                }
            }
        return aggs

    def autocomplete(self, prefix: str, size: int = 10):
        """
        Returns product names matching the given prefix using match_phrase_prefix.
        Ideal for autocomplete dropdowns.
        """
        try:
            query = {
                "query": {
                    "match_phrase_prefix": {
                        "name": {
                            "query": prefix
                        }
                    }
                },
                "_source": ["name"],
                "size": size
            }
            response = self.es.search(index=self.index, body=query)
            return [hit["_source"]["name"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Autocomplete error: {str(e)}")
            return []

    def suggest(self, text: str, size: int = 5):
        """
        Returns suggestions using the completion suggester on name.suggest.
        Ideal for spelling corrections or query suggestions.
        """
        try:
            suggest_query = {
                "suggest": {
                    "product-suggest": {
                        "prefix": text,
                        "completion": {
                            "field": "name.suggest",
                            "size": size
                        }
                    }
                }
            }
            response = self.es.search(index=self.index, body=suggest_query)
            suggestions = response.get("suggest", {}).get("product-suggest", [])
            if suggestions and suggestions[0]["options"]:
                return [option["text"] for option in suggestions[0]["options"]]
            return []
        except Exception as e:
            logger.error(f"Suggest error: {str(e)}")
            return []