# store/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product
from .search import ProductDocument

@receiver(post_save, sender=Product)
def update_elasticsearch(sender, instance, **kwargs):
    document = ProductDocument(meta={'id': instance.id}, name=instance.name, description=instance.description, price=instance.price)
    document.save()


@receiver(post_save, sender=Product)
def index_product(sender, instance, **kwargs):
    doc = ProductDocument(
        meta={'id': instance.id},
        name=instance.name,
        description=instance.description,
        brand=instance.brand,
        category=str(instance.category.name),
        price=float(instance.price),
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        sku=instance.sku
    )
    doc.save()

@receiver(post_delete, sender=Product)
def delete_product(sender, instance, **kwargs):
    try:
        ProductDocument.get(id=instance.id).delete()
    except:
        pass
