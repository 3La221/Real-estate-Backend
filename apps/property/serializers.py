from rest_framework import serializers
from .models import (
    Property, PropertyMedia, PropertyType, Agency,
    Wilaya, Commune, Amenity, PropertyAmenity
)


class WilayaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaya
        fields = ['id', 'name']


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = ['id', 'name', 'wilaya']


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'slug']


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name']


class PropertyMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = ['id', 'image', 'order', 'is_cover']
        read_only_fields = ['id']


class PropertyListSerializer(serializers.ModelSerializer):
   
    property_type = PropertyTypeSerializer(read_only=True)
    wilaya = WilayaSerializer(read_only=True)
    commune = CommuneSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'listing_type', 'price', 'negotiable',
            'property_type', 'wilaya', 'commune', 'address',
            'area_m2', 'bedrooms', 'bathrooms', 'floor',
            'furnished', 'parking', 'is_featured', 'status',
            'cover_image', 'agency_name', 'reference', 'created_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at']
    
    def get_cover_image(self, obj):
        """Get the cover image URL"""
        cover = obj.media.filter(is_cover=True).first()
        if cover and cover.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover.image.url)
            return cover.image.url
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Read-only detailed serializer for individual property view.
    All modifications are done through Django admin.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    wilaya = WilayaSerializer(read_only=True)
    commune = CommuneSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True, source='propertyamenity_set.amenity')
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'slug', 'reference',
            'listing_type', 'status', 'price', 'negotiable', 'available_from',
            'property_type', 'wilaya', 'commune',
            'address', 'latitude', 'longitude',
            'area_m2', 'bedrooms', 'bathrooms', 'floor',
            'furnished', 'parking',
            'is_published', 'is_featured',
            'media', 'amenities',
            'agency_name', 'views_count', 'leads_count',
            'created_at', 'updated_at'
        ]
