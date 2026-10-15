# search_backend.py

from django_elasticsearch_dsl_drf.filter_backends.faceted_search import FacetedSearchFilterBackend
from elasticsearch_dsl.query import Q, Bool
from six import iteritems
from store.filter_config import get_filter_type, parse_range, get_filter_field
import logging

logger = logging.getLogger(__name__)

class CustomFacetedSearchFilterBackend(FacetedSearchFilterBackend):
    def aggregate(self, request, queryset, view):
        query_params = getattr(request, '_filtered_querydict', request.GET)
        query_params = {k: v for k, v in query_params.items() if k not in ["pincode", "page", "page_size"]}
        filters = {}
        applied_keys = []
        for param_key, value in query_params.items():
            if not value:
                continue

            field_name = get_filter_field(param_key, view)
            filter_type = get_filter_type(field_name)
            applied_keys.append(field_name)

            if filter_type == "range":
                filters[field_name] = Q("range", **{field_name: parse_range(value)})
            elif filter_type == "boolean":
                filters[field_name] = Q("term", **{field_name: value.lower() in ["true", "1"]})
            elif filter_type == "search":
                # Skip or handle in main query
                continue
            else:
                filters[field_name] = Q("terms", **{field_name: value.split("__")})

        # Apply custom facet logic
        facets = self.construct_facets(request, view)
        for facet_key, facet_conf in iteritems(facets):
            agg = facet_conf["facet"].get_aggregation()
            agg_filter = Bool(filter=[q for k, q in filters.items() if k != agg.field])

            if agg.field in applied_keys and len(applied_keys) == 1:
                queryset.aggs.bucket(f"_filter_{facet_key}", "global").bucket(facet_key, agg)
            else:
                queryset.aggs.bucket(f"_filter_{facet_key}", "filter", filter=agg_filter).bucket(facet_key, agg)
        print(queryset.to_dict())
        return queryset
    
    def get_facets(self, search, view):
        # Trigger execution to get aggregation results
        results = search.execute()
        return results.aggregations.to_dict()
    
    def filter_queryset(self, request, queryset, view):
        print("➡️ CustomFacetedSearchFilterBackend.filter_queryset called")
        queryset = super().filter_queryset(request, queryset, view)
        print("➡️ After super().filter_queryset")
        queryset = self.aggregate(request, queryset, view)
        print("➡️ After self.aggregate")
        view._facet_data = self.get_facets(queryset, view)
        print("➡️ After get_facets")
        return queryset
