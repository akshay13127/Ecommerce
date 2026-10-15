# Ecommerce Platform

A Django storefront and REST API built around product search. Catalog data lives in MongoDB, Elasticsearch handles faceted, autocomplete and semantic search, and admins load whole catalogs from a spreadsheet instead of entering products one by one.

Django 3.0, Django REST Framework, MongoDB (djongo), Elasticsearch, Sentence Transformers, pandas.

## Features

**Search, three ways**

- **Faceted search.** Filter by category, brand, size and price ranges, with live bucket counts, sorting by price or name, and pagination (django-elasticsearch-dsl-drf). A custom facet backend applies every active filter except a facet's own when counting it, so picking one brand still shows how many results the other brands would give.
- **Semantic search.** Product name and description are embedded with `all-MiniLM-L6-v2` (384 dimensions) and stored as a `dense_vector`. Queries run as a hybrid: kNN on the embedding plus a keyword match on the name, so "something to dry my hair" can still find a hair dryer.
- **Autocomplete and suggestions.** Edge n-gram analyzer for search-as-you-type, plus an Elasticsearch completion suggester on product names.

**Catalog**

- Products with SKU, brand, weight, image and a gallery of extra images
- Nested categories (each category can have a parent)
- Variants with an attribute, a value and an extra price ("Color: Red, +$5")
- Inventory tracked per product and per variant
- Django signals reindex a product in Elasticsearch on every save and remove it on delete

**Bulk import**

Admins upload an `.xlsx` file from the Django admin. Each row becomes a product, keyed on SKU, so re-uploading the same file updates products instead of duplicating them. Missing categories are created, and stock and variants are set from the same row. Rows that fail are written to an error CSV the admin can download, and every upload is tracked with a status and a message.

Expected columns:

```
name, description, price, sku, category, brand, weight,
stock_quantity, image_url, variant_attribute, variant_value, extra_price
```

**Shopping**

- Sign up, log in and log out
- Per-user cart with add, update quantity and remove (auth required)
- Separate profile types for customers (loyalty points), vendors (company, GST number) and employees

## Architecture

```
Browser / API client
        |
     Django (templates + DRF)
     |            |              \
  MongoDB      Elasticsearch    bulk import task
  (djongo)     products index   (pandas, written
  catalog,     text + facets    as a Celery task)
  carts,       + 384-d vectors
  uploads
        ^             ^
        |  post_save  |
        +-- signals --+
```

## Run it

You'll need Python 3.9, MongoDB and Elasticsearch 8.x (see the note under Known issues).

```bash
pip install -r requirment.txt
pip install pandas openpyxl sentence-transformers
python manage.py migrate
python manage.py populate_data              # sample categories and products
python manage.py seed                       # filter definitions (price ranges and the like)
python manage.py reindex_with_embeddings    # build the search index with vectors
python manage.py runserver
```

The storefront is at http://localhost:8000 and the admin at http://localhost:8000/admin/.

## API

| Method | Path | Does |
| --- | --- | --- |
| GET, POST | `/api/products/` | Product CRUD |
| GET, POST | `/api/categories/`, `/api/variants/`, `/api/inventory/` | Catalog CRUD |
| GET | `/products/search/` | Keyword search |
| GET | `/api/semantic-search/` | Hybrid semantic search with filters and facets |
| GET | `/products/autocomplete/` | Search-as-you-type |
| GET | `/products/suggest/` | Completion suggestions |
| GET, POST | `/cart-items/` | Your cart |
| PATCH, DELETE | `/cart/items/<product_id>/update/`, `/delete/` | Change or remove a cart item |
| POST | `/account/signup/`, `/account/login/`, `/account/logout/` | Accounts |

## Known issues

I'm fixing these, but they're listed so nobody has to find them the hard way.

- **Elasticsearch version.** The top-level `knn` query in semantic search needs Elasticsearch 8.x, while `docker-compose.yml` starts 7.10.1 and `requirment.txt` pins the 7.x client. Faceted search and autocomplete work on 7.x, semantic search doesn't.
- **Docker build.** The Dockerfile copies `requirements.txt`, but the file is named `requirment.txt`. Compose also has no Redis service for Celery.
- **Missing dependencies.** `pandas`, `openpyxl` and `sentence-transformers` are used but aren't in the requirements file.
- **Bulk upload status.** The task sets `BulkUpload.COMPLETED` and `PARTIALLY_COMPLETED`, which don't exist on the model (it defines `SUCCESS` and `PARTIAL`). Rows import correctly, but the upload is then marked Failed. The admin also calls the task with `.run()`, which processes the file inside the request, and the project has no Celery app module yet, so there's no worker to hand it to.
- **Duplicate route.** `products` is registered twice on the router, so the faceted list view is shadowed by the plain CRUD view.
- **Config.** `SECRET_KEY` and `DEBUG = True` are hardcoded in settings.
