from django.db import models
from django.core.validators import RegexValidator


class Tenant(models.Model):
    
    name = models.CharField(max_length=255, help_text="Tenant display name")
    slug = models.SlugField(unique=True, help_text="Unique identifier for tenant")
    
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Primary domain (e.g., tenant1.com)",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9]$',
                message='Enter a valid domain name'
            )
        ]
    )
    
    # Balak n7tajo multiple domains per tenant
    additional_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional domains for this tenant (JSON array)"
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    schema_name = models.CharField(
        max_length=63,
        unique=True,
        blank=True,
        help_text="Database schema name (optional for schema-based tenancy)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenants'
        ordering = ['name']
        indexes = [
            models.Index(fields=['domain', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    def get_all_domains(self):
        """Returns all domains associated with this tenant"""
        domains = [self.domain]
        if self.additional_domains:
            domains.extend(self.additional_domains)
        return domains


class TimeStampedModel(models.Model):
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark the instance as deleted."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
