from django.core.management.base import BaseCommand
from django_redis import get_redis_connection
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Show all cached verification tokens'

    def handle(self, *args, **options):
        redis_conn = get_redis_connection("default")
        
        # Get all verification token keys
        pattern = "drf_boilerplate:1:email_verification:*"
        keys = redis_conn.keys(pattern)
        
        if not keys:
            self.stdout.write(self.style.WARNING('No verification tokens found in cache'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nFound {len(keys)} verification token(s):\n'))
        
        for key in keys:
            # Decode key
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            
            # Extract token from key
            token = key_str.split(':')[-1]
            
            # Get user_id
            user_id = redis_conn.get(key)
            user_id = user_id.decode('utf-8') if isinstance(user_id, bytes) else user_id
            
            # Get TTL
            ttl = redis_conn.ttl(key)
            hours = ttl // 3600
            minutes = (ttl % 3600) // 60
            
            # Get user info
            try:
                user = User.objects.get(id=user_id)
                email = user.email
                is_active = user.is_active
            except User.DoesNotExist:
                email = "User not found"
                is_active = None
            
            self.stdout.write(f'Token: {token}...')
            self.stdout.write(f'  User ID: {user_id}')
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Active: {is_active}')
            self.stdout.write(f'  TTL: {hours}h {minutes}m ({ttl}s)')
            self.stdout.write('---')
