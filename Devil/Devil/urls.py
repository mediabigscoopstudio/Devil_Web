from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/profile/', include('profiles.urls')),
    path('api/v1/discovery/', include('discovery.urls')),
    path('api/v1/matches/', include('matching.urls')),
    path('api/v1/conversations/', include('messaging.urls')),
    path('api/v1/moderation/', include('moderation.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]
