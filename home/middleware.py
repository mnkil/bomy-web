import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from django.conf import settings

# Setup logger
logger = logging.getLogger(__name__)

# Define log directories based on environment
if settings.DEBUG:
    LOG_DIR = os.path.join(settings.BASE_DIR, 'logs')
else:
    LOG_DIR = '/var/log/bomy-web'

VISIT_LOG_PATH = os.path.join(LOG_DIR, 'visits.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Configure the rotating file handler
visit_handler = RotatingFileHandler(
    VISIT_LOG_PATH,
    maxBytes=1024 * 1024,  # 1MB
    backupCount=3  # Keep 3 backup files
)
visit_logger = logging.getLogger('visits')
visit_logger.addHandler(visit_handler)
visit_logger.setLevel(logging.INFO)

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
            
            # Log the visit
            visit_logger.info(json.dumps(visit_data))
                
        except Exception as e:
            logger.error(f"Visit logging failed: {e}")
        
        return response