"""machadoproject URL configuration."""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

# machado URLs are automatically appended by machado.apps.MachadoConfig.ready()
