from django import forms
from bulk.models import BulkUpload

from bulk.forms import BaseFormMeta

class ProductBulkUploadForm(forms.ModelForm):
    file_path = forms.FileField()

    class Meta(BaseFormMeta):
        exclude = ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by', 'task_name', 'file_name',
                   'status', 'error', 'error_report', 'success_report', 'msg')
        model = BulkUpload