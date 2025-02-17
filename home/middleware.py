import json
from datetime import datetime
from .models import Visit

class VisitLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log the visit to database
        Visit.objects.create(
            path=request.path,
            ip=request.META.get('REMOTE_ADDR', '')
        )
        
        return response 