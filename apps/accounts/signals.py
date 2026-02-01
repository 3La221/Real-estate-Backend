from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def assign_default_permissions(sender, instance, created, **kwargs):
    """
    Automatically assign property permissions to newly created users.
    Permissions assigned:
    - Can add property
    - Can change property
    - Can delete property
    - Can view property
    """
    if created:
        try:

            from apps.property.models import Property
            property_content_type = ContentType.objects.get_for_model(Property)
            

            permissions = Permission.objects.filter(
                content_type=property_content_type,
                codename__in=[
                    'add_property',
                    'change_property',
                    'delete_property',
                    'view_property'
                ]
            )
            

            instance.user_permissions.add(*permissions)
            
        except Exception as e:
            # Log the error but don't break user creation
            print(f"Error assigning default permissions to user {instance.username}: {e}")
