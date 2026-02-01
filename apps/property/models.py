import uuid
from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField

from apps.accounts.models import User
from apps.core.models import Tenant

# Create your models here.
class Commune(models.Model):
    id = models.CharField(primary_key=True, max_length=191)
    name = models.CharField(max_length=191)
    wilaya = models.ForeignKey('Wilaya', models.SET_NULL,null=True,blank=True)  # Field name made lowercase.

    class Meta:
        db_table = 'commune'
    
    def __str__(self):
        return self.name

class Wilaya(models.Model):
    id = models.CharField(primary_key=True, max_length=191)
    name = models.CharField(max_length=191)

    class Meta:
        db_table = 'wilaya'

    def __str__(self):
        return self.name


def agency_upload_path(instance, filename):
    return f"agencies/{instance.slug}/{filename}"

class Agency(models.Model):
    
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="agency",
        db_index=True,
        default=None,
        help_text="Tenant this agency belongs to (one-to-one)"
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_agencies",
        help_text="Primary contact/owner of the agency"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)

    email = models.EmailField()

    wilaya = models.ForeignKey(Wilaya,on_delete=models.CASCADE,related_name="agencies")
    commune = models.ForeignKey(Commune,on_delete=models.CASCADE,related_name="agencies")
    address = models.CharField(max_length=255, blank=True)

    logo = CloudinaryField('agency_logo', folder='agencies/logos', blank=True, null=True)
    cover_image = CloudinaryField('agency_cover', folder='agencies/covers', blank=True, null=True)

    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)     
            slug = base
            i = 1
            while Agency.objects.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug 
        super().save(*args, **kwargs)



class AgencyContact(models.Model):
    PHONE = "phone"
    WHATSAPP = "whatsapp"

    CONTACT_TYPE_CHOICES = [
        (PHONE, "Phone"),
        (WHATSAPP, "WhatsApp"),
    ]

    agency = models.ForeignKey(
        Agency,
        related_name="contacts",
        on_delete=models.CASCADE
    )

    type = models.CharField(
        max_length=10,
        choices=CONTACT_TYPE_CHOICES
    )

    number = models.CharField(max_length=20)

    label = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. Sales, Rentals, Office"
    )

    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.agency.name} - {self.type}: {self.number}"
    
    def save(self, *args, **kwargs): 
        if self.is_primary:
            AgencyContact.objects.filter(
                agency=self.agency,
                type=self.type
            ).update(is_primary=False)
        super().save(*args, **kwargs)

def property_media_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    property_id = instance.property.id or "temp"

    return (
        f"agencies/{instance.property.agency.slug}/"
        f"properties/{property_id}/"
        f"{uuid.uuid4()}.{ext}"
    )

class PropertyType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)      
            slug = base
            i = 1
            while PropertyType.objects.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug 
            super().save(*args, **kwargs)

class Property(models.Model):
    SALE = "sale"
    RENT = "rent"
    EXCHANGE = "exchange"

    LISTING_TYPE_CHOICES = [
        (SALE, "For Sale"),
        (RENT, "For Rent"),
        (EXCHANGE, "For Exchange")
    ]

    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    RENTED = "rented"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (SOLD, "Sold"),
        (RENTED, "Rented"),
        (ARCHIVED, "Archived"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_index=True
    )

    agency = models.ForeignKey(
        Agency,
        related_name="properties",
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(max_length=255, blank=True) # assuming that slugs would be helpful in the seo

    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="properties",
        db_index=True
    )

    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        db_index=True
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_index=True
    )

    negotiable = models.BooleanField(default=False)
    available_from = models.DateField(null=True, blank=True) 

    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.CASCADE,
        related_name="properties"
    )
    commune = models.ForeignKey(
        Commune,
        on_delete=models.CASCADE,
        related_name="properties"
    )
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    area_m2 = models.PositiveIntegerField()
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    floor = models.IntegerField(null=True, blank=True)

    furnished = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)

    is_published = models.BooleanField(default=True,db_index=True)
    is_featured = models.BooleanField(default=False,db_index=True)

    reference = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    views_count = models.PositiveIntegerField(default=0)
    leads_count = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"{self.agency.id}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def publish(self):
        self.status = self.ACTIVE
        self.is_published = True
        self.save()

    def __str__(self):
        return f"{self.title} ({self.agency.name})"

class PropertyMedia(models.Model):
    property = models.ForeignKey(
        Property,
        related_name="media",
        on_delete=models.CASCADE
    )
    order = models.PositiveSmallIntegerField(default=0)
    image = CloudinaryField(
        'property_image',
        folder='properties',
        transformation={
            'quality': 'auto',
            'fetch_format': 'auto'
        }
    )
    is_cover = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Media for {self.property.title}"
    
    def save(self, *args, **kwargs):
        # If this is marked as cover, unset other cover images
        if self.is_cover:
            PropertyMedia.objects.filter(
                property=self.property,
                is_cover=True
            ).exclude(id=self.id).update(is_cover=False)
        super().save(*args, **kwargs)

class Amenity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class PropertyAmenity(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("property", "amenity")

    def __str__(self):
        return f"{self.property} - {self.amenity}"

