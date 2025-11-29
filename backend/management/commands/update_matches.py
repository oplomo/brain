import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from square.models import Match, Fixture, FootballPrediction
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update matches with final scores (does not alter predictions)'
    
    def handle(self, *args, **options):
        self.stdout.write(f"🚀 CRON JOB STARTED: update_matches at {datetime.datetime.now()}")
        
        # Get all matches and fixtures to see what's available
        matches = Match.objects.filter(updated=False)
        fixtures = Fixture.objects.filter(status_short="FT")
        
        self.stdout.write(f"📊 Found {matches.count()} unupdated matches")
        self.stdout.write(f"📊 Found {fixtures.count()} finished fixtures")
        
        fixture_map = {fixture.fixture_id: fixture for fixture in fixtures}
        updated_count = 0
        
        for match in matches:
            if match.match_id in fixture_map:
                fixture = fixture_map[match.match_id]
                
                football_prediction = FootballPrediction.objects.filter(match=match).first()
                if football_prediction:
                    # Create new fields if they don't exist, or use existing ones
                    football_prediction.actual_home_goals = fixture.score_fulltime_home
                    football_prediction.actual_away_goals = fixture.score_fulltime_away
                    football_prediction.save()
                    self.stdout.write(f"✅ Updated match {match.match_id}: {fixture.score_fulltime_home}-{fixture.score_fulltime_away}")

                match.updated = True
                match.save()
                updated_count += 1
        
        # Send email notification
        subject = f"Match Scores Updated - {updated_count} matches"
        message = f"""
        Match score update completed at {datetime.datetime.now()}!
        
        Statistics:
        - Unupdated matches found: {matches.count()}
        - Finished fixtures found: {fixtures.count()}
        - Successfully updated: {updated_count}
        
        The predictions remain unchanged - only actual results were updated.
        
        Check the results here: https://jerusqore-production.up.railway.app/admin/
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['adamsquare64@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write("📧 Email sent successfully")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Email failed: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Successfully updated {updated_count} match scores'))
        self.stdout.write(f"⏰ CRON JOB COMPLETED: update_matches at {datetime.datetime.now()}")