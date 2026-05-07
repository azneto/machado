# Cache (optional)

The machado views are pre-configured to enable local-memory caching for 1 hour. In order to move the cache to another location, you'll need to set Django's cache framework following the [official instructions](https://docs.djangoproject.com/en/5.2/topics/cache/).

## Example

Include the following in `settings.py` to store the cache in the database:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'machado_cache_table',
    }
}
CACHE_TIMEOUT = 60 * 60 * 24  # 86400 seconds == 1 day
```

Create the cache table:

```bash
python manage.py createcachetable
```

## Clearing the Cache Table

It is a good idea to clear the cache table whenever you make changes to your machado installation. For this, install the [django-clear-cache](https://github.com/rdegges/django-clear-cache) tool:

```bash
pip install django-clear-cache
```

Then modify your `settings.py` file to add `clear_cache`:

```python
INSTALLED_APPS = (
    # ...
    'clear_cache',
)
```

Then to clear the cache just run:

```bash
python manage.py clear_cache
```
