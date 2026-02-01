from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')

app_name = 'property'

urlpatterns = [
    path('', include(router.urls)),
]
