from apps.property.mixins import TenantFilterMixin
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from config.pagination import StandardPagination

from .models import Property
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
)





class PropertyViewSet(TenantFilterMixin, viewsets.ReadOnlyModelViewSet):
   
    queryset = Property.objects.filter(is_published=True).select_related(
        'agency', 'property_type', 'wilaya', 'commune'
    ).prefetch_related('media')
    permission_classes = []
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardPagination
    

    filterset_fields = {
        'listing_type': ['exact'],
        'status': ['exact'],
        'property_type': ['exact'],
        'wilaya': ['exact'],
        'commune': ['exact'],
        'price': ['gte', 'lte'],
        'area_m2': ['gte', 'lte'],
        'bedrooms': ['exact', 'gte'],
        'bathrooms': ['exact', 'gte'],
        'furnished': ['exact'],
        'parking': ['exact'],
        'is_featured': ['exact'],
        'is_published': ['exact'],
    }
    

    search_fields = ['title', 'description', 'address', 'reference']
    

    ordering_fields = ['created_at', 'price', 'area_m2', 'views_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        return PropertyDetailSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        queryset = self.get_queryset().filter(
            is_featured=True,
            is_published=True,
            status=Property.ACTIVE
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
