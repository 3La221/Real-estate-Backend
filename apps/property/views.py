from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.property.mixins import TenantFilterMixin
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import ListView
from django.db.models import F, Q, Count, OuterRef, Prefetch, Subquery
from .models import Amenity, Property, PropertyMedia, Wilaya

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

    return render(request, 'product-details.html', {
        'property': property,
        'cover': cover,
        'gallery': gallery,
        'amenities': property.propertyamenity_set.select_related('amenity').all(),
        'primary_contacts': property.agency.contacts.filter(is_primary=True),
    })

def home(request):
    amenities = (
        Amenity.objects
        .filter(icon__isnull=False)
        .exclude(icon='')
        .annotate(total=Count('propertyamenity'))
        .order_by('-total')[:10]
    )

    cover_image_subquery = PropertyMedia.objects.filter(
        property=OuterRef('pk'),
        is_cover=True
    ).values('image')[:1]

    featured_properties = (
        Property.objects
        .filter(is_featured=True, is_published=True)
        .annotate(image=Subquery(cover_image_subquery))
        .order_by('-created_at')[:4]
    )

    # Subquery: one cover image per wilaya (via its first published property)
    wilaya_cover_subquery = PropertyMedia.objects.filter(
        property__wilaya=OuterRef('pk'),
        property__is_published=True,
        is_cover=True
    ).values('image')[:1]

    locations_with_properties = (
        Wilaya.objects
        .annotate(
            property_count=Count(
                'properties',
                filter=Q(properties__is_published=True)
            ),
            image=Subquery(wilaya_cover_subquery)
        )
        .filter(property_count__gt=0)
        .order_by('-property_count')[:8]
    )
    for location in locations_with_properties:
        print(location.image.url)
    return render(request, 'index5.html', {
        'amenities': amenities,
        'featured': featured_properties,
        'locations': locations_with_properties,
    })