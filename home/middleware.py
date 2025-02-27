import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from django.conf import settings

# Setup logger
logger = logging.getLogger(__name__)

def get_log_directory():
    """Determine and create the appropriate log directory based on environment."""
    if settings.DEBUG:
        # Development environment - use project directory
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
    else:
        # Production environment - try multiple locations
        potential_dirs = [
            '/var/log/bomy-web',  # Primary choice
            '/tmp/bomy-web/logs',  # Fallback 1
            os.path.join(settings.BASE_DIR, 'logs')  # Fallback 2
        ]
        
        for dir_path in potential_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(dir_path, '.test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return dir_path
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not use log directory {dir_path}: {e}")
                continue
        
        # If all else fails, use /tmp
        log_dir = '/tmp'
        logger.warning("Using /tmp for logging as fallback")
    
    return log_dir

# Initialize logging setup
try:
    LOG_DIR = get_log_directory()
    VISIT_LOG_PATH = os.path.join(LOG_DIR, 'visits.log')
    
    # Ensure the log file exists and has correct permissions
    if not os.path.exists(VISIT_LOG_PATH):
        with open(VISIT_LOG_PATH, 'a'):
            pass
        # Try to set permissions to 666 (rw-rw-rw-)
        try:
            os.chmod(VISIT_LOG_PATH, 0o666)
        except Exception as e:
            logger.warning(f"Could not set log file permissions: {e}")
    
    # Configure the rotating file handler
    visit_handler = RotatingFileHandler(
        VISIT_LOG_PATH,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=3,  # Keep 3 backup files
        delay=True  # Don't open the file until first log
    )
    
    visit_logger = logging.getLogger('visits')
    visit_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to prevent duplicates
    for handler in visit_logger.handlers[:]:
        visit_logger.removeHandler(handler)
    
    visit_logger.addHandler(visit_handler)
    
except Exception as e:
    logger.error(f"Failed to setup logging: {e}")
    # Set up a null handler to prevent logging errors
    visit_logger = logging.getLogger('visits')
    visit_logger.addHandler(logging.NullHandler())

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
            try:
                visit_logger.info(json.dumps(visit_data))
            except Exception as e:
                logger.error(f"Failed to log visit: {e}")
                
        except Exception as e:
            logger.error(f"Visit logging failed: {e}")
        
        return response