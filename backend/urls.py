from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', include('pages.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('meters/', include('meters.urls')),
    path('billing/', include('billing.urls')),
    path('payments/', include('payments.urls')),
    path('leaks/', include('leaks.urls')),
    path('schedules/', include('schedules.urls')),
    path('notifications/', include('notifications.urls')),
    path('profile/', include('accounts.urls')),
]

# Fix for password reset URL with trailing equals sign
urlpatterns += [
    path('accounts/password/reset/key/<path:invalid_path>/', 
         RedirectView.as_view(url='/accounts/password/reset/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)