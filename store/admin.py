# from django.contrib import admin
# from .models import *
# # Register your models here.


# admin.site.register(Product)
# admin.site.register(Category)
# # admin.site.register(ProductAttribute)
# # admin.site.register(ProductReview)
from django.contrib import admin
from django.urls import path
from datetime import datetime

from .models import *
from bulk.admin import BaseBulkUploadAdmin
from .forms import ProductBulkUploadForm

from django.contrib import messages
from django.contrib.postgres import fields
from django.http import HttpResponse
from django.shortcuts import redirect
import os
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from .tasks import *


@admin.register(ProductBulkUpload)
class ProductBulkUploadAdmin(BaseBulkUploadAdmin):
    form = ProductBulkUploadForm
    list_per_page = 20
    # change_list_template = 'bulk/bulk_upload_change_list_product.html'
    list_display = ("_id", "task_name", "file_name", "status", "msg", "download_uploaded_file", "error_file", "error",
                    "created_at", "updated_at", "created_by", "updated_by")

    def get_queryset(self, request):
        qs = super(ProductBulkUploadAdmin, self).get_queryset(request)
        return qs.filter(task_name=BulkUpload.PRODUCT_BULK_UPLOAD)

    def product_sample_download(self, request):
        try:
            file_path = 'templates/products/PRODUCT_BULK_UPLOAD_SAMPLE.xlsx'
            export_data = open(file_path, 'rb')
            response = HttpResponse(export_data, content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename={}'.format("PRODUCT_BULK_UPLOAD_SAMPLE.xlsx")
            return response
        except:
            messages.error(request, 'Something went wrong while downloading document.')
            return redirect('/admin/products/productbulkupload/')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(r'product-sample-download/', self.admin_site.admin_view(self.product_sample_download),
                 name='product-sample-download'),
        ]
        return custom_urls + urls



    def save_model(self, request, obj, form, change):
        date_time = datetime.now()

        if not change:
            obj.created_at = date_time
            obj.created_by = request.user.email

        obj.updated_at = date_time
        obj.updated_by = request.user.email

        super(ProductBulkUploadAdmin, self).save_model(request, obj, form, change)

        file_obj = request.FILES.get('file_path')
        extension = file_obj.name.split('.')[-1].lower()

        obj.task_name = BulkUpload.PRODUCT_BULK_UPLOAD

        if extension == 'xlsx':
            file_name = f"{obj._id}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')}.{extension}"
            local_file_path = os.path.join(settings.LOCAL_FILE_PATH, file_name)

            # Save file locally
            with open(local_file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            obj.file_path = local_file_path
            obj.file_name = file_obj.name
            obj.status = BulkUpload.QUEUE
            obj.save()

            # Trigger async task
            process_product_bulk_upload.run(str(obj._id))
        else:
            obj.status = BulkUpload.FAILED
            obj.msg = "Please upload xlsx excel files only."
            obj.save()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    search_fields = ['name']

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value', 'extra_price']

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant', 'stock_quantity']
    search_fields = ['product__name']

@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ['product']
    search_fields = ['product']

# @admin.register(ProductReview)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ['user', 'product', 'rating', 'created_at']
#     search_fields = ['product__name', 'user__username']


# serializers.py
# admin.py
from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)

    def subtotal(self, obj):
        return obj.subtotal()


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_price')
    inlines = [CartItemInline]

    def total_price(self, obj):
        return obj.total()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'subtotal_display', 'added_at')
    readonly_fields = ('subtotal_display',)

    def subtotal_display(self, obj):
        return obj.subtotal()
