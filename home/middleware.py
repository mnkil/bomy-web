import json
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
VISIT_LOG_PATH = os.path.join(LOG_DIR, 'visits.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

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
            visit_data = {
                'timestamp': datetime.now().isoformat(),
                'path': request.path,
                'ip': ip
            }
            
            # Write to log file
            with open(VISIT_LOG_PATH, 'a') as f:
                f.write(json.dumps(visit_data) + '\n')
                
        except Exception as e:
            logger.error(f"Visit logging failed: {e}")
        
        return response