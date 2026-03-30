from apps.property.mixins import TenantFilterMixin
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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


from django.views.generic import ListView
from django.db.models import Q
from .models import Property


class PropertyListView(ListView):
    model = Property
    template_name = 'shop-grid.html'
    context_object_name = 'properties'
    paginate_by = 9

    def get_queryset(self):
        queryset = Property.objects.filter(is_published=True).select_related(
            'agency', 'property_type', 'wilaya', 'commune'
        ).prefetch_related('media')

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(address__icontains=q) |
                Q(reference__icontains=q)
            )

        listing_type = self.request.GET.get('listing_type')
        if listing_type:
            queryset = queryset.filter(listing_type=listing_type)

        property_type = self.request.GET.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type_id=property_type)

        wilaya = self.request.GET.get('wilaya')
        if wilaya:
            queryset = queryset.filter(wilaya_id=wilaya)

        commune = self.request.GET.get('commune')
        if commune:
            queryset = queryset.filter(commune_id=commune)

        price_min = self.request.GET.get('price_min')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)

        price_max = self.request.GET.get('price_max')
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        area_min = self.request.GET.get('area_min')
        if area_min:
            queryset = queryset.filter(area_m2__gte=area_min)

        bedrooms = self.request.GET.get('bedrooms')
        if bedrooms:
            queryset = queryset.filter(bedrooms__gte=bedrooms)

        bathrooms = self.request.GET.get('bathrooms')
        if bathrooms:
            queryset = queryset.filter(bathrooms__gte=bathrooms)

        furnished = self.request.GET.get('furnished')
        if furnished in ('true', 'false'):
            queryset = queryset.filter(furnished=(furnished == 'true'))

        parking = self.request.GET.get('parking')
        if parking in ('true', 'false'):
            queryset = queryset.filter(parking=(parking == 'true'))

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        ordering = self.request.GET.get('ordering', '-created_at')
        allowed_orderings = ['created_at', '-created_at', 'price', '-price', 'area_m2', '-area_m2']
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop('page', None)  # remove page so pagination links work cleanly
        context['query_params'] = params.urlencode()

        from apps.property.models import PropertyType, Wilaya, Commune
        context['property_types'] = PropertyType.objects.all()
        context['wilayas'] = Wilaya.objects.all()

        context['filters'] = self.request.GET

        context['total_count'] = self.get_queryset().count()

        return context