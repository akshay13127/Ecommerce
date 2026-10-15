from django.core.management.base import BaseCommand
from store.models import Product
from store.documents import ProductDocument

class Command(BaseCommand):
    help = "Reindex products with semantic embeddings"

    def handle(self, *args, **options):
        for product in Product.objects.all():
            ProductDocument().update(product)
        self.stdout.write(self.style.SUCCESS("Products reindexed with embeddings"))