"""
URL configuration for the Django project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    # path('accounts/', include('apps.accounts.urls')), no need for auth for now
    path('', include('apps.property.urls')),
]

urlpatterns = [
    # Admin
    path(settings.ADMIN_URL if hasattr(settings, 'ADMIN_URL') else 'admin/', admin.site.urls),

    # Public frontend pages (served from Frontend folder)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index2/', TemplateView.as_view(template_name='index2.html'), name='index2'),
    path('index3/', TemplateView.as_view(template_name='index3.html'), name='index3'),
    path('index4/', TemplateView.as_view(template_name='index4.html'), name='index4'),
    path('index5/', TemplateView.as_view(template_name='index5.html'), name='index5'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('shop-grid/', TemplateView.as_view(template_name='shop-grid.html'), name='shop_grid'),
    path('product-details/', TemplateView.as_view(template_name='product-details.html'), name='product_details'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('404/', TemplateView.as_view(template_name='404.html'), name='page_404'),

    # API v1
    path('api/v1/', include(api_v1_patterns)),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    # Serve existing frontend assets directly from the Frontend folder
    urlpatterns += [
        path(
            'style.css',
            serve,
            {
                'document_root': settings.BASE_DIR.parent / 'Frontend',
                'path': 'style.css',
            },
            name='frontend-style',
        ),
    ]
    urlpatterns += static(
        '/assets/',
        document_root=settings.BASE_DIR.parent / 'Frontend' / 'assets',
    )

    # Media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
