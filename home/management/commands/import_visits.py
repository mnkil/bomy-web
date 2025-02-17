from django.core.management.base import BaseCommand
from home.models import Visit
from datetime import datetime
import json
import os

VISIT_LOG_PATH = '/var/log/bomy-web/visits.log'

class Command(BaseCommand):
    help = 'Import visits from log file to database'

    def handle(self, *args, **options):
        if not os.path.exists(VISIT_LOG_PATH):
            return
            
        # Read and process log file
        with open(VISIT_LOG_PATH, 'r') as f:
            lines = f.readlines()
            
        # Clear the file
        open(VISIT_LOG_PATH, 'w').close()
        
        # Process visits
        for line in lines:
            try:
                data = json.loads(line.strip())
                Visit.objects.create(
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    path=data['path'],
                    ip=data['ip']
                )
            except Exception as e:
                self.stdout.write(f"Error processing visit: {e}") 