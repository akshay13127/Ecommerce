import os

from bson import ObjectId
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from bulk.forms import BulkUploadForm
from bulk.models import BulkUpload
from django.conf import settings


class BaseBulkUploadAdmin(admin.ModelAdmin):
    form = BulkUploadForm
    list_per_page = 20
    list_display = ("_id", "task_name", "file_name", "status", "msg", "download_uploaded_file",
                    "success_file", "error_file", "error", "created_by", "created_at", "updated_at")

    def _serve_file_response(self, request, file_path):
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError
            with open(file_path, 'rb') as export_data:
                file_name = os.path.basename(file_path)
                response = HttpResponse(export_data, content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename={file_name}'
                return response
        except Exception:
            messages.error(request, 'Something went wrong while downloading the file.')
            return redirect('/'.join(request.path.split("/")[:4]) + '/')

    def download_file(self, request, _id):
        try:
            bulk_obj = BulkUpload.objects.get(_id=ObjectId(_id))
            local_path = os.path.join(settings.LOCAL_FILE_PATH, os.path.basename(bulk_obj.file_path))
            return self._serve_file_response(request, local_path)
        except Exception:
            messages.error(request, 'Something went wrong while downloading the uploaded file.')
            return redirect('/'.join(request.path.split("/")[:4]) + '/')

    def download_uploaded_file(self, obj):
        return format_html(
            '<a class="button" target="_blank" href="{}">Download</a>',
            reverse('admin:file-download', args=[str(obj._id)])
        )

    def download_error_file(self, request, _id):
        try:
            bulk_obj = BulkUpload.objects.get(_id=ObjectId(_id))
            local_path = os.path.join(settings.LOCAL_FILE_PATH, os.path.basename(bulk_obj.error_report))
            return self._serve_file_response(request, local_path)
        except Exception:
            messages.error(request, 'Something went wrong while downloading the error file.')
            return redirect('/'.join(request.path.split("/")[:4]) + '/')

    def error_file(self, obj):
        if obj.error_report:
            return format_html(
                '<a class="button" target="_blank" href="{}">Download</a>',
                reverse('admin:error-file-download', args=[str(obj._id)])
            )
        return ""

    def download_success_file(self, request, _id):
        try:
            bulk_obj = BulkUpload.objects.get(_id=ObjectId(_id))
            local_path = os.path.join(settings.LOCAL_FILE_PATH, os.path.basename(bulk_obj.success_report))
            return self._serve_file_response(request, local_path)
        except Exception:
            messages.error(request, 'Something went wrong while downloading the success file.')
            return redirect('/'.join(request.path.split("/")[:4]) + '/')

    def success_file(self, obj):
        if obj.success_report:
            return format_html(
                '<a class="button" target="_blank" href="{}">Download</a>',
                reverse('admin:success-file-download', args=[str(obj._id)])
            )
        return ""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<str:_id>/file-download/', self.admin_site.admin_view(self.download_file), name='file-download'),
            path('<str:_id>/error-file-download/', self.admin_site.admin_view(self.download_error_file),
                 name='error-file-download'),
            path('<str:_id>/success-file-download/', self.admin_site.admin_view(self.download_success_file),
                 name='success-file-download'),
        ]
        return custom_urls + urls


admin.site.register(BulkUpload, BaseBulkUploadAdmin)
