from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def api_root(request):
    return JsonResponse({
        'message': 'WorkFinder API',
        'version': '2.0.0',
        'documentation': '/api/docs/',
        'endpoints': {
            'auth': '/api/auth/',
            'jobs': '/api/jobs/',
            'categories': '/api/categories/',
            'seekers': '/api/seekers/',
            'employers': '/api/employers/',
            'applications': '/api/applications/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include('jobs.urls')),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)