# filter_config.py
from store.models import ManageFilters

RANGE_FILTERS = ["price", "karat"]
BOOLEAN_FILTERS = ["express", "quick_ship"]
SEARCH_FILTERS = ["search"]


def get_filter_type(field_name):
    if field_name in RANGE_FILTERS:
        return ManageFilters.RANGE
    if field_name in BOOLEAN_FILTERS:
        return ManageFilters.BOOLEAN
    if field_name in SEARCH_FILTERS:
        return ManageFilters.SEARCH
    return ManageFilters.DEFAULT

def parse_range(value):
    parts = value.split("__")
    return {"gte": float(parts[0]), "lte": float(parts[1])} if len(parts) == 2 else {}

def get_filter_field(key, view=None):
    # view.post_filter_fields may map query param names to field names
    if view:
        mapping = view.post_filter_fields.get(key, key)
        if isinstance(mapping, dict):
            return mapping.get("field", key)
        return mapping
    return key
