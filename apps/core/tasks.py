
from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, message, recipient_list):
    
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f'Email sent successfully to {recipient_list}')
        return f'Email sent to {recipient_list}'
    except Exception as e:
        logger.error(f'Error sending email: {str(e)}')
        raise
