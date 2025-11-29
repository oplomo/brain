import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
import requests
from datetime import datetime, timedelta
from square.models import Fixture, ResultDate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update fixtures from API and send prediction reminder'
    
    def handle(self, *args, **options):
        self.stdout.write(f"🚀 CRON JOB STARTED: update_fixtures at {datetime.now()}")
        
        tommorow_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        self.stdout.write(f"📅 Fetching fixtures for date: {tommorow_date}")
        
        fixtures_data = self.fetch_fixtures_res(tommorow_date)
        
        if fixtures_data:
            self.stdout.write(f"📥 Found {len(fixtures_data)} fixtures from API")
            new_count, updated_count = self.save_fixtures_to_db(fixtures_data)
            total_fixtures = len(fixtures_data)
            
            # Send email with prediction link
            subject = f"Fixtures Updated - {total_fixtures} matches available"
            message = f"""
            Fixtures update completed at {datetime.now()}!
            
            Statistics:
            - Total fixtures fetched: {total_fixtures}
            - New fixtures added: {new_count}
            - Existing fixtures updated: {updated_count}
            
            🎯 Time to make your predictions!
            
            Click here to select predictions:
            https://jerusqore-production.up.railway.app/select_football_prediction/
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
            
            self.stdout.write(self.style.SUCCESS(
                f'🎉 Successfully processed {total_fixtures} fixtures '
                f'({new_count} new, {updated_count} updated)'
            ))
        else:
            self.stdout.write(self.style.WARNING('⚠️ No fixtures data found from API'))
            
            # Send email even when no fixtures
            subject = "Fixtures Update - No Matches Today"
            message = f"""
            Fixtures update completed at {datetime.now()} but no matches found for today.
            
            Date checked: {tommorow_date}
            
            This could mean:
            - No matches scheduled for today
            - API is temporarily unavailable
            - No active leagues/seasons
            
            The system will check again in 6 minutes.
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['adamsquare64@gmail.com'],
                    fail_silently=False,
                )
                self.stdout.write("📧 No-data email sent successfully")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Email failed: {e}"))
        
        self.stdout.write(f"⏰ CRON JOB COMPLETED: update_fixtures at {datetime.now()}")
    
    def fetch_fixtures_res(self, date):
        api_key = settings.API_FOOTBALL
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        params = {"date": date}
        
        self.stdout.write(f"🌐 Making API request to: {url}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            self.stdout.write(f"📡 API Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                self.stdout.write(f"✅ API Success - Found {len(fixtures)} fixtures")
                return fixtures
            else:
                self.stdout.write(self.style.ERROR(f"❌ API Error: {response.status_code} - {response.text}"))
                return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ API Request failed: {e}"))
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