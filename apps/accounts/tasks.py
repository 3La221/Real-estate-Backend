from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_verification_email(user_id, token):
    """Send verification email to user"""
    try:
        user = User.objects.get(id=user_id)
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        subject = 'Verify your email address'
        
        # Try to use HTML template if it exists, otherwise use plain text
        try:
            html_message = render_to_string('emails/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
            })
        except Exception:
            html_message = None
        
        plain_message = f"""
Hi {user.first_name or user.email},

Thank you for registering! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Verification email sent to {user.email}"
        
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@shared_task
def send_password_reset_email(user_id, token):
    """Send password reset email to user"""
    try:
        user = User.objects.get(id=user_id)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        subject = 'Reset your password'
        
        # Try to use HTML template if it exists, otherwise use plain text
        try:
            html_message = render_to_string('emails/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
        except Exception:
            html_message = None
        
        plain_message = f"""
Hi {user.first_name or user.email},

You requested to reset your password. Please click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Best regards,
The Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Password reset email sent to {user.email}"
        
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Failed to send email: {str(e)}"
