from django.contrib.auth import authenticate, get_user_model
from django.utils.crypto import get_random_string
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, ValidationError
import requests
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations"""

    @staticmethod
    def register_user(validated_data):
        """Register a new user and send verification email"""
        from .tasks import send_verification_email
        
        logger.debug("Starting user registration process")
        print("Starting user registration process")
        email = validated_data.get('email')
        

        existing_user = User.objects.filter(email=email, is_active=False).first()
        
        if existing_user:

            logger.info(f"Resending verification email for existing inactive user: {email}")
            token = AuthService.generate_verification_token(existing_user)
            logger.error(f"Generated verification token for existing user: {token}")
            send_verification_email.delay(existing_user.id, token)
            return existing_user
        


        validated_data.pop('password_confirm', None)
        

        logger.info(f"Creating new user: {email}")
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        

        token = AuthService.generate_verification_token(user)
        print("TOKEN:", token)
        

        send_verification_email.delay(user.id, token)
        
        return user

    @staticmethod
    def verify_email(token):
        """Verify email with token"""
        user_id = cache.get(f'email_verification:{token}')
        
        if not user_id:
            raise ValidationError('Invalid or expired verification token')
        
        try:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            

            cache.delete(f'email_verification:{token}')
            

            tokens = AuthService.generate_tokens(user)
            return user, tokens
            
        except User.DoesNotExist:
            raise ValidationError('User not found')

    @staticmethod
    def resend_verification_email(email):
        """Resend verification email"""
        from .tasks import send_verification_email
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_active:
                raise ValidationError('Email already verified')
            
            token = AuthService.generate_verification_token(user)
            send_verification_email.delay(user.id, token)
            
        except User.DoesNotExist:
            raise ValidationError('User not found')

    @staticmethod
    def generate_verification_token(user):
        """Generate and cache verification token"""
        token = get_random_string(64)

        cache.set(f'email_verification:{token}', user.id, timeout=86400)
        return token

    @staticmethod
    def login_user(email, password):
        """Authenticate and login user"""
        user = authenticate(email=email, password=password)
        
        if not user:
            raise AuthenticationFailed('Invalid credentials')
        
        if not user.is_active:
            raise AuthenticationFailed('Please verify your email first')
        
        tokens = AuthService.generate_tokens(user)
        return user, tokens

    @staticmethod
    def generate_tokens(user):
        """Generate JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def request_password_reset(email):
        """Request password reset and send email with token"""
        from .tasks import send_password_reset_email
        
        try:
            user = User.objects.get(email=email)
            
            if not user.is_active:
                raise ValidationError('Please verify your email first')
            

            token = get_random_string(64)
            logger.info(f"Generated password reset token for user {email}: {token}")

            cache.set(f'password_reset:{token}', user.id, timeout=3600)
            

            send_password_reset_email.delay(user.id, token)
            
        except User.DoesNotExist:

            pass

    @staticmethod
    def verify_reset_token(token):
        """Verify if password reset token is valid"""
        user_id = cache.get(f'password_reset:{token}')
        
        if not user_id:
            raise ValidationError('Invalid or expired reset token')
        
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise ValidationError('User not found')

    @staticmethod
    def reset_password(token, new_password):
        """Reset user password with token"""
        user = AuthService.verify_reset_token(token)
        

        user.set_password(new_password)
        user.save()
        

        cache.delete(f'password_reset:{token}')
        
        return user


class SocialAuthService:
    """Service class for social media authentication"""

    PROVIDERS = {
        'google': {
            'verify_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'email_field': 'email',
            'name_field': 'name',
        },
        'facebook': {
            'verify_url': 'https://graph.facebook.com/me',
            'params': {'fields': 'id,name,email'},
            'email_field': 'email',
            'name_field': 'name',
        },
        'github': {
            'verify_url': 'https://api.github.com/user',
            'email_field': 'email',
            'name_field': 'name',
        }
    }

    @staticmethod
    def authenticate(provider, access_token):
        """Authenticate user via social provider"""
        if provider not in SocialAuthService.PROVIDERS:
            raise ValidationError(f'Unsupported provider: {provider}')

        user_data = SocialAuthService._verify_token(provider, access_token)
        user = SocialAuthService._get_or_create_user(user_data, provider)
        tokens = AuthService.generate_tokens(user)
        
        return user, tokens

    @staticmethod
    def _verify_token(provider, access_token):
        """Verify token with provider and get user data"""
        config = SocialAuthService.PROVIDERS[provider]
        headers = {'Authorization': f'Bearer {access_token}'}
        params = config.get('params', {})

        try:
            response = requests.get(
                config['verify_url'],
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise AuthenticationFailed(f'Failed to verify {provider} token: {str(e)}')

    @staticmethod
    def _get_or_create_user(user_data, provider):
        """Get or create user from social provider data"""
        config = SocialAuthService.PROVIDERS[provider]
        email = user_data.get(config['email_field'])
        
        if not email:
            raise ValidationError('Email not provided by provider')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': user_data.get(config['name_field'], '').split()[0] if user_data.get(config['name_field']) else '',
                'is_active': True,  # Social auth users are auto-verified
            }
        )
        return user



        