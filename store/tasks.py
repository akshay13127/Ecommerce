import pandas as pd
import os
import requests
from urllib.parse import urlparse
from django.core.files import File
from tempfile import NamedTemporaryFile
from celery import shared_task
from django.conf import settings
from bulk.models import BulkUpload
from .models import Product, Category, ProductVariant, Inventory
from bson import ObjectId


@shared_task
def process_product_bulk_upload(task_id):
    try:
        bulk_obj = BulkUpload.objects.get(_id=ObjectId(task_id))
        file_path = bulk_obj.file_path

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            bulk_obj.status = BulkUpload.FAILED
            bulk_obj.msg = "Unsupported file format"
            bulk_obj.save()
            return

        success_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                category_name = row.get("category")
                category, _ = Category.objects.get_or_create(name=category_name)

                # Create or update product
                product, created = Product.objects.update_or_create(
                    sku=row["sku"],
                    defaults={
                        "name": row.get("name"),
                        "description": row.get("description"),
                        "price": row.get("price"),
                        "category": category,
                        "brand": row.get("brand", ""),
                        "weight": row.get("weight", None),
                    }
                )

                # Handle product image
                image_url = row.get("image_url")
                if image_url:
                    if image_url.startswith('http://') or image_url.startswith('https://'):
                        # Download image from URL
                        img_temp = NamedTemporaryFile(delete=True)
                        img_resp = requests.get(image_url, timeout=10)
                        img_temp.write(img_resp.content)
                        img_temp.flush()
                        file_name = os.path.basename(urlparse(image_url).path)
                        product.image_url.save(file_name, File(img_temp))
                    else:
                        # Assume local file
                        local_img_path = os.path.join(settings.MEDIA_ROOT, "bulk_images", image_url)
                        if os.path.exists(local_img_path):
                            with open(local_img_path, 'rb') as f:
                                product.image_url.save(image_url, File(f), save=True)

                product.save()

                # Inventory
                Inventory.objects.update_or_create(
                    product=product,
                    variant=None,
                    defaults={
                        "stock_quantity": int(row.get("stock_quantity", 0))
                    }
                )

                # Optional Variant
                if row.get("variant_attribute") and row.get("variant_value"):
                    variant, _ = ProductVariant.objects.get_or_create(
                        product=product,
                        attribute=row["variant_attribute"],
                        value=row["variant_value"],
                        defaults={"extra_price": row.get("extra_price", 0.00)}
                    )

                success_count += 1

            except Exception as e:
                failed_rows.append({"row": index + 2, "error": str(e)})

        bulk_obj.status = BulkUpload.COMPLETED if not failed_rows else BulkUpload.PARTIALLY_COMPLETED
        bulk_obj.msg = f"Processed {success_count} products with {len(failed_rows)} errors."
        bulk_obj.save()

        if failed_rows:
            error_file = os.path.join(settings.LOCAL_FILE_PATH, f"{task_id}_errors.csv")
            pd.DataFrame(failed_rows).to_csv(error_file, index=False)
            bulk_obj.error_report = error_file
            bulk_obj.save()

    except Exception as e:
        bulk_obj.status = BulkUpload.FAILED
        bulk_obj.msg = f"Unexpected error: {str(e)}"
        bulk_obj.save()
