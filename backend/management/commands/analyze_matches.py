import os
import django
import time
import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from backend.adams_square import Jerusalem
from backend.grace_isha import analyze_data
from backend.models import TaskProgress

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyze matches data with email notifications'
    
    def analyze_fetched_data(self, every_data):
        try:
            logger.info("Starting analysis for the provided data.")
            analyzer = analyze_data()
            fin = analyzer.save_every_data(every_data)
            logger.info("Data analysis successful.")
            return fin
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return False
    
    def run_analysis_for_matches(self, matches, task_id=None):
        """Run match analysis and send email report"""
        total_matches = len(matches)
        success_count = 0
        failure_count = 0
        
        if total_matches == 0:
            return success_count, failure_count
            
        jerusalem = Jerusalem()
        
        for idx, match in enumerate(matches):
            try:
                every_data = jerusalem.receive_match(match)
                
                analyzer = analyze_data()
                result = analyzer.save_every_data(every_data)
                
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"Error processing match: {e}")
            
            # Update progress if task_id provided
            if task_id:
                progress = (idx + 1) / total_matches * 100
                TaskProgress.objects.update_or_create(
                    task_id=task_id,
                    defaults={
                        "progress": progress,
                        "successful": success_count,
                        "failed": failure_count,
                        "total": total_matches,
                    },
                )
            
            # Rate limiting
            if (idx + 1) % 5 == 0:
                time.sleep(62)
        
        # Send completion email
        subject = f"Match Analysis Complete - {success_count}/{total_matches} Successful"
        message = f"""
        Match analysis completed!
        
        Results:
        - Total matches processed: {total_matches}
        - Successful analyses: {success_count}
        - Failed analyses: {failure_count}
        - Success rate: {(success_count/total_matches)*100:.1f}%
        
        Check the predictions in your admin panel:
        https://jerusqore-production.up.railway.app/admin/
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['adamsquare64@gmail.com'],
            fail_silently=False,
        )
        
        return success_count, failure_count
    
    def handle(self, *args, **options):
        # This command is primarily called from views
        # But can also be run manually for testing
        self.stdout.write("Match analysis command ready - use via web interface")