from django import forms
from .models import *
from bson import ObjectId
from django.core.exceptions import (
    ValidationError,
)
from django.forms.models import ModelChoiceField


class BaseFormMeta:
    exclude = ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')


class CustomModelChoiceField(ModelChoiceField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"
            if isinstance(value, self.queryset.model):
                value = getattr(value, key)
            value = self.queryset.get(**{key: ObjectId(value)})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )
        return value


class BulkUploadForm(forms.ModelForm):
    file_path = forms.FileField()

    class Meta(BaseFormMeta):
        exclude = ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by', 'task_name', 'file_name',
                   'status', 'error', 'error_report', 'msg')
        model = BulkUpload