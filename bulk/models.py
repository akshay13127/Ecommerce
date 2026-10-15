from django.db import models

# Create your models here.
from djongo import models
from datetime import datetime


class BaseModel(models.Model):
    _id = models.ObjectIdField(primary_key=True, auto_created=True, serialize=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField('created_at', default=datetime.now)
    updated_at = models.DateTimeField('updated_at', default=datetime.now)
    created_by = models.CharField(max_length=256, null=True, blank=True)
    updated_by = models.CharField(max_length=256, null=True, blank=True)

    objects = models.DjongoManager()

    class Meta:
        abstract = True



class BulkUpload(BaseModel):
    QUEUE = 'queue'
    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'
    PARTIAL = "partially success"
    STATUS_CHOICES = ((QUEUE, 'Queue'),
                      (PROCESSING, 'Processing'),
                      (SUCCESS, 'Success'),
                      (PARTIAL, 'Partially Success'),
                      (FAILED, 'Failed')
                      )
    PRODUCT_BULK_UPLOAD = "product_bulk_upload"
    task_name = models.CharField(max_length=256)
    file_name = models.CharField(max_length=256, null=True, blank=True)
    file_path = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=64, choices=STATUS_CHOICES)
    msg = models.CharField(max_length=256, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    error_report = models.CharField(max_length=256, null=True, blank=True)
    success_report = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.task_name
