# middleware.py

from store.filter_config import get_filter_type, parse_range
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from store.constants import CURRENCY_SYMBOL
import traceback
from rest_framework.response import Response


class ProductListMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            print("BEFORE:", request.GET)
            query_dict = request.GET.copy()
            print("AFTER:", query_dict)
            pincode = query_dict.get("pincode")
            currency_code = request.headers.get("Currency-Code", "INR")

            if query_dict.get("express") and pincode:
                cluster_details = cache.get(f"quick_ship_cluster_{pincode}")
                if cluster_details and cluster_details.get("cluster_name"):
                    query_dict["available_in_cluster__in"] = cluster_details["cluster_name"]
                else:
                    query_dict["karat"] = "0"
                query_dict.pop("express")

            # Save the modified query dict for later
            print("Setting request._filtered_querydict")
            request._filtered_querydict = query_dict

        except Exception as e:
            print(f"Error in CustomisedRequestMiddleware: {traceback.format_exc()}")

    def process_response(self, request, response):
        try:
            if isinstance(response, Response) and hasattr(response, "data"):
                currency_code = request.headers.get("Currency-Code", "INR")
                # response.data["currency"] = {
                #     "code": currency_code,
                #     "symbol": CURRENCY_SYMBOL.get(currency_code, "")
                # }
                # response.data["conversion_rates"] = CurrencyService().get_all_conversion_rate()
                response._is_rendered = False
                response.render()
        except Exception as e:
            print(f"Error in CustomisedRequestMiddleware response: {traceback.format_exc()}")
        return response
