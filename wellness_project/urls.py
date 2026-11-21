from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

handler403 = 'core.views.auth_views.custom_permission_denied_view'
handler404 = 'core.views.auth_views.custom_not_found_view'
handler500 = 'core.views.auth_views.custom_server_error_view'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
