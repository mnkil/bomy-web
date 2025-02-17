import json
from datetime import datetime
from .models import Visit
from django.db.utils import OperationalError

class VisitLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        try:
            Visit.objects.create(
                path=request.path,
                ip=request.META.get('REMOTE_ADDR', '')
            )
        except Exception:
            # Fail silently to not disrupt the main application
            pass
        
        return response 