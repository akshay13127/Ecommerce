# products/management/commands/seed_filters.py

from django.core.management.base import BaseCommand
from store.models import ManageFilters

FILTERS = [
    {
        "title": "Price Range",
        "name": "under-10000",
        "field_name": "special_price",
        "start_value": 0,
        "end_value": 10000,
        "type": "range"
    },
    {
        "title": "Ready to Ship",
        "name": "ready-to-ship",
        "field_name": "quick_ship",
        "value": "ready+to+ship",
        "type": "boolean"
    },
    {
        "title": "Sort by Popular",
        "name": "sort-by-popular",
        "field_name": "ordering",
        "value": "desc",
        "type": "ordering"
    },
]

class Command(BaseCommand):
    help = "Seed initial filter data into ManageFilters table"

    def handle(self, *args, **kwargs):
        for filter_item in FILTERS:
            ManageFilters.objects.update_or_create(
                name=filter_item["name"],
                defaults=filter_item
            )
        self.stdout.write(self.style.SUCCESS("Filters seeded successfully."))
