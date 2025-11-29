import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from square.models import Match, Fixture, FootballPrediction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update matches with final scores (does not alter predictions)'
    
    def handle(self, *args, **options):
        self.stdout.write("Starting match score updates...")
        
        # Only get FINISHED matches (FT = Full Time)
        matches = Match.objects.filter(updated=False)
        fixtures = Fixture.objects.filter(status_short="FT")  # Only final results
        
        fixture_map = {fixture.fixture_id: fixture for fixture in fixtures}

        updated_count = 0
        for match in matches:
            if match.match_id in fixture_map:
                fixture = fixture_map[match.match_id]
                
                # ONLY update the actual scores, don't touch predictions
                football_prediction = FootballPrediction.objects.filter(match=match).first()
                if football_prediction:
                    # Just update the actual result fields (assuming you have these)
                    # This doesn't alter the prediction, only records what actually happened
                    football_prediction.actual_home_goals = fixture.score_fulltime_home
                    football_prediction.actual_away_goals = fixture.score_fulltime_away
                    football_prediction.save()

                match.updated = True
                match.save()
                updated_count += 1
        
        # Send email notification
        if updated_count > 0:
            subject = f"Match Scores Updated - {updated_count} matches"
            message = f"""
            Match score update completed successfully!
            
            Updated {updated_count} matches with final scores.
            
            The predictions remain unchanged - only actual results were updated.
            
            Check the results here: https://jerusqore-production.up.railway.app/admin/
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['adamsquare64@gmail.com'],
                fail_silently=False,
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} match scores'))