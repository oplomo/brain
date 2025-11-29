import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
import requests
from square.models import Fixture, ResultDate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update fixtures from API and send prediction reminder'
    
    def fetch_fixtures_res(self, date):
        api_key = settings.API_FOOTBALL
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        params = {"date": date}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("response", [])
        else:
            self.stdout.write(self.style.ERROR(f"API Error: {response.status_code}"))
            return []
    
    def save_fixtures_to_db(self, res_data):
        new_fixtures_count = 0
        updated_fixtures_count = 0
        
        for fixture in res_data:
            result_date, created = ResultDate.objects.get_or_create(
                date=datetime.fromisoformat(
                    fixture["fixture"]["date"].replace("Z", "")
                ).date()
            )

            fulltime_home = fixture["score"]["fulltime"].get("home", None)
            fulltime_away = fixture["score"]["fulltime"].get("away", None)

            obj, created = Fixture.objects.update_or_create(
                fixture_id=fixture["fixture"]["id"],
                defaults={
                    "fixture_date": datetime.fromisoformat(
                        fixture["fixture"]["date"].replace("Z", "")
                    ),
                    "status_short": fixture["fixture"]["status"]["short"],
                    "team_home": fixture["teams"]["home"]["name"],
                    "team_away": fixture["teams"]["away"]["name"],
                    "score_fulltime_home": fulltime_home,
                    "score_fulltime_away": fulltime_away,
                    "result_date": result_date,
                },
            )
            
            if created:
                new_fixtures_count += 1
            else:
                updated_fixtures_count += 1
                
        return new_fixtures_count, updated_fixtures_count
    
    def handle(self, *args, **options):
        self.stdout.write("Starting fixtures update...")
        today_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        fixtures_data = self.fetch_fixtures_res(today_date)
        
        if fixtures_data:
            new_count, updated_count = self.save_fixtures_to_db(fixtures_data)
            total_fixtures = len(fixtures_data)
            
            # Send email with prediction link
            subject = f"Fixtures Updated - {total_fixtures} matches available"
            message = f"""
            Fixtures update completed successfully!
            
            Statistics:
            - Total fixtures fetched: {total_fixtures}
            - New fixtures added: {new_count}
            - Existing fixtures updated: {updated_count}
            
            🎯 Time to make your predictions!
            
            Click here to select predictions:
            https://jerusqore-production.up.railway.app/select_football_prediction/
            
            Or go to: /select_football_prediction/
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['adamsquare64@gmail.com'],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully processed {total_fixtures} fixtures '
                f'({new_count} new, {updated_count} updated)'
            ))
        else:
            self.stdout.write(self.style.WARNING('No fixtures data found'))
            
            # Send email even when no fixtures (so you know it's working)
            subject = "Fixtures Update - No Matches Today"
            message = """
            Fixtures update completed but no matches found for today.
            
            This could mean:
            - No matches scheduled for today
            - API is temporarily unavailable
            - No active leagues/seasons
            
            The system will check again in 6 minutes.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['adamsquare64@gmail.com'],
                fail_silently=False,
            )