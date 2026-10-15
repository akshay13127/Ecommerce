from django.core.management.base import BaseCommand
from store.models import Category, Product
import uuid  # For generating unique SKU

class Command(BaseCommand):
    help = "Populate database with sample categories and products"

    def handle(self, *args, **kwargs):
        categories = [
            {"name": "Electronics", "description": "Electronic gadgets and devices"},
            {"name": "Fashion", "description": "Clothing and accessories"},
            {"name": "Home Appliances", "description": "Appliances for home use"}
        ]

        products = [
            {"name": "Smartphone", "description": "Latest model with high-end specs", "price": 699.99, "category": "Electronics"},
            {"name": "Laptop", "description": "Powerful laptop for gaming and work", "price": 1299.99, "category": "Electronics"},
            {"name": "T-shirt", "description": "Cotton t-shirt with a modern fit", "price": 19.99, "category": "Fashion"},
            {"name": "Washing Machine", "description": "Automatic washing machine with AI features", "price": 499.99, "category": "Home Appliances"}
        ]

        # Create categories
        category_map = {}
        for cat in categories:
            obj, created = Category.objects.get_or_create(name=cat["name"], defaults={"description": cat["description"]})
            category_map[cat["name"]] = obj

        # Create products
        for prod in products:
            Product.objects.get_or_create(
                name=prod["name"],
                defaults={
                    "description": prod["description"],
                    "price": prod["price"],
                    "category": category_map[prod["category"]],
                    "sku": str(uuid.uuid4()),  # Generate a unique SKU for each product
                    "brand": None,  # You can add a brand if needed
                    "weight": None,  # You can add a weight if needed
                    "image_url": None  # You can add an image URL if needed
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully populated database with categories and products"))
