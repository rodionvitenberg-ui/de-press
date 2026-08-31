from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from api.main import api

# Admin chrome in English regardless of user-facing locale.
admin.site.site_header = "de-press admin"
admin.site.site_title = "de-press admin"
admin.site.index_title = "Operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
