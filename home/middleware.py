import json
from datetime import datetime
from .models import Visit
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)

class VisitLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __call__(self, request):
        response = self.get_response(request)
        
        try:
            ip = self.get_client_ip(request)
            Visit.objects.create(
                path=request.path,
                ip=ip
            )
            # Force database connection closure
            from django.db import connection
            connection.close()
        except OperationalError as e:
            logger.warning(f"Database write failed: {e}")
            pass
        except Exception as e:
            logger.warning(f"Visit logging failed: {e}")
            pass
        
        return response 