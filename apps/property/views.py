from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.property.mixins import TenantFilterMixin
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Commune, Property
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
)



def get_communes(request, wilaya_id):
    communes = Commune.objects.filter(wilaya_id=wilaya_id).values("id", "name")
    return JsonResponse(list(communes), safe=False)

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

def property_detail(request, reference):
    property = get_object_or_404(
        Property.objects.select_related(
            'agency', 'wilaya', 'commune', 'property_type'
        ).prefetch_related(
            'media', 'propertyamenity_set__amenity'
        ),
        reference = reference,
        is_published=True
    )

    # Increment views
    Property.objects.filter(pk=property.pk).update(views_count=property.views_count + 1)

    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()

        # if name and email and message:
        #     # Save lead
        #     from .models import Lead  # adjust if Lead is elsewhere
        #     Lead.objects.create(
        #         property=property,
        #         name=name,
        #         email=email,
        #         phone=phone,
        #         message=message,
        #     )

        #     # Increment leads count
        #     Property.objects.filter(pk=property.pk).update(leads_count=property.leads_count + 1)

            # Send email to agency
        #     send_mail(
        #         subject=f"New lead for {property.title}",
        #         message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n{message}",
        #         from_email=settings.DEFAULT_FROM_EMAIL,
        #         recipient_list=[property.agency.email],
        #         fail_silently=True,
        #     )

        #     messages.success(request, "Your message has been sent successfully.")
        # else:
        #     messages.error(request, "Please fill in all required fields.")
        print("!! supposed to send email !!")

    cover = property.media.filter(is_cover=True).first() or property.media.first()
    gallery = property.media.filter(is_cover=False) 
    print(property.agency.contacts.filter(is_primary=True))

    return render(request, 'product-details.html', {
        'property': property,
        'cover': cover,
        'gallery': gallery,
        'amenities': property.propertyamenity_set.select_related('amenity').all(),
        'primary_contacts': property.agency.contacts.filter(is_primary=True),
    })