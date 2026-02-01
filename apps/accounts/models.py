from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Can be extended with additional fields as needed.
    """
    phone_number = models.CharField(max_length=20, blank=True)
    agency = models.ForeignKey(
        'property.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_users',
        help_text='Agency this user belongs to. Agency staff can only manage their own properties.'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
    
    @property
    def is_agency_staff(self):
        """Check if user is agency staff (has agency assigned)"""
        return self.agency is not None and self.is_staff
    
    @property
    def is_superadmin(self):
        """Check if user is superadmin"""
        return self.is_superuser
