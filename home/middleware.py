import json
from datetime import datetime
from .models import Visit
from django.db.utils import OperationalError
from django.db import transaction, close_old_connections
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
        logger.warning("Middleware called")  # Debug log
        close_old_connections()
        
        response = self.get_response(request)
        
        try:
            ip = self.get_client_ip(request)
            logger.warning(f"Got IP: {ip}")  # Debug log
            with transaction.atomic():
                visit = Visit.objects.create(
                    path=request.path,
                    ip=ip
                )
                logger.warning(f"Created visit: {visit.id}")  # Debug log
        except OperationalError as e:   
            logger.warning(f"Database write failed: {e}")
        except Exception as e:
            logger.warning(f"Visit logging failed: {e}")
        finally:
            close_old_connections()
        
        return response