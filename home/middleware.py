import json
from datetime import datetime
from .models import Visit
from django.db.utils import OperationalError
from django.db import transaction, close_old_connections, connections
import logging
import os

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
        logger.warning("Middleware called")
        
        # Get response first
        response = self.get_response(request)
        
        # Then try to log the visit
        try:
            # Ensure fresh connection
            for conn in connections.all():
                conn.close_if_unusable_or_obsolete()
            
            ip = self.get_client_ip(request)
            logger.warning(f"Got IP: {ip}")
            
            # Use a new connection for this transaction
            with transaction.atomic(using='default'):
                visit = Visit.objects.using('default').create(
                    path=request.path,
                    ip=ip
                )
                logger.warning(f"Created visit: {visit.id}")
                
        except OperationalError as e:
            logger.error(f"Database write failed: {e}")
            logger.error(f"Database file permissions: {oct(os.stat('db.sqlite3').st_mode)[-3:]}")
        except Exception as e:
            logger.error(f"Visit logging failed: {e}")
        finally:
            # Ensure all connections are properly closed
            close_old_connections()
        
        return response