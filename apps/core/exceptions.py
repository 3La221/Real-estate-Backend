"""
Custom exception handler for Django REST Framework.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response
    if response is not None:
        custom_response = {
            'error': True,
            'status_code': response.status_code,
        }

        # Handle validation errors
        if isinstance(exc, ValidationError):
            custom_response['message'] = 'Validation error'
            custom_response['details'] = response.data
        else:
            # Handle other errors
            if isinstance(response.data, dict):
                custom_response['message'] = response.data.get('detail', str(exc))
                custom_response['details'] = response.data
            else:
                custom_response['message'] = str(exc)
                custom_response['details'] = response.data

        response.data = custom_response

    return response
