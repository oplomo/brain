import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import requests
from square.models import Fixture, ResultDate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update finished fixtures with results and save to square models'
    
    def handle(self, *args, **options):
        self.stdout.write(f"🚀 Starting results update at {datetime.now()}")
        
        # Get today's date for finished matches
        today_date = datetime.utcnow().strftime("%Y-%m-%d")
        self.stdout.write(f"📅 Fetching finished fixtures for: {today_date}")
        
        # Fetch finished fixtures from API
        fixtures_data = self.fetch_finished_fixtures(today_date)
        
        if not fixtures_data:
            self.stdout.write("❌ No finished fixtures data received")
            return
        
        self.stdout.write(f"📥 Found {len(fixtures_data)} finished fixtures")
        
        # Save finished fixtures to database
        saved_count = self.save_finished_fixtures(fixtures_data)
        
        # Send email notification
        self.send_notification(today_date, len(fixtures_data), saved_count)
        
        self.stdout.write(f"✅ Completed: {saved_count} results saved")
    
    def fetch_finished_fixtures(self, date):
        """Fetch finished fixtures (FT status) from Football API"""
        api_key = settings.API_FOOTBALL
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        params = {"date": date, "status": "FT"}  # Only finished fixtures
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                
                # Filter only finished matches (FT status)
                finished_fixtures = []
                for fixture in fixtures:
                    fixture_data = fixture.get("fixture", {})
                    status = fixture_data.get("status", {}).get("short")
                    if status == "FT":  # Full Time
                        finished_fixtures.append(fixture)
                
                self.stdout.write(f"🎯 Found {len(finished_fixtures)} finished matches")
                return finished_fixtures
            else:
                self.stdout.write(f"❌ API Error: {response.status_code}")
                return []
                
        except Exception as e:
            self.stdout.write(f"❌ API Request failed: {e}")
            return []
    
    def safe_get(self, data, *keys, default=None):
        """Safely get nested dictionary values"""
        if not isinstance(data, dict):
            return default
            
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def save_finished_fixtures(self, fixtures):
        """Save finished fixtures to square models"""
        saved_count = 0
        
        for fixture in fixtures:
            try:
                # Safely extract data with type checking
                if not isinstance(fixture, dict):
                    self.stdout.write("⚠️ Skipping: Fixture is not a dictionary")
                    continue
                
                # Extract data with safe methods
                fixture_data = self.safe_get(fixture, "fixture") or {}
                league_data = self.safe_get(fixture, "league") or {}
                teams_data = self.safe_get(fixture, "teams") or {}
                score_data = self.safe_get(fixture, "score") or {}
                fulltime_score = self.safe_get(score_data, "fulltime") or {}
                
                home_team = self.safe_get(teams_data, "home") or {}
                away_team = self.safe_get(teams_data, "away") or {}
                
                # Check if we have basic required data
                if not fixture_data:
                    self.stdout.write("⚠️ Skipping: Missing fixture data")
                    continue
                
                # Check if it's really finished
                status = self.safe_get(fixture_data, "status", "short")
                if status != "FT":
                    self.stdout.write("⚠️ Skipping: Not a finished match")
                    continue
                
                # Parse fixture date
                date_str = self.safe_get(fixture_data, "date")
                if not date_str:
                    self.stdout.write("⚠️ Skipping: No date in fixture")
                    continue
                    
                try:
                    fixture_date = datetime.fromisoformat(date_str.replace("Z", ""))
                except (ValueError, AttributeError):
                    self.stdout.write("⚠️ Skipping: Invalid date format")
                    continue
                
                # Get or create ResultDate
                result_date, _ = ResultDate.objects.get_or_create(
                    date=fixture_date.date()
                )
                
                # Get fixture ID
                fixture_id = self.safe_get(fixture_data, "id")
                if not fixture_id:
                    self.stdout.write("⚠️ Skipping: No fixture ID")
                    continue
                
                # Get scores safely
                home_score = self.safe_get(fulltime_score, "home")
                away_score = self.safe_get(fulltime_score, "away")
                
                # Convert scores to integers if they exist
                try:
                    home_score_int = int(home_score) if home_score is not None else None
                    away_score_int = int(away_score) if away_score is not None else None
                except (ValueError, TypeError):
                    home_score_int = None
                    away_score_int = None
                
                # Create or update Fixture
                Fixture.objects.update_or_create(
                    fixture_id=fixture_id,
                    defaults={
                        "fixture_date": fixture_date,
                        "status_short": status,
                        "team_home": self.safe_get(home_team, "name", default="Unknown Home"),
                        "team_away": self.safe_get(away_team, "name", default="Unknown Away"),
                        "score_fulltime_home": home_score_int,
                        "score_fulltime_away": away_score_int,
                        "result_date": result_date,
                    }
                )
                
                saved_count += 1
                home_name = self.safe_get(home_team, "name", default="Home")
                away_name = self.safe_get(away_team, "name", default="Away")
                self.stdout.write(f"✅ Saved result: {home_name} {home_score_int}-{away_score_int} {away_name}")
                
            except Exception as e:
                self.stdout.write(f"❌ Failed to save fixture result: {e}")
                continue
        
        return saved_count
    
    def send_notification(self, date, total_fixtures, saved_matches):
        """Send email notification"""
        subject = f"Results Updated - {saved_matches} finished matches saved"
        message = f"""
        Results update completed at {datetime.now()}!
        
        Date: {date}
        Finished fixtures found: {total_fixtures}
        Results saved: {saved_matches}
        
        Match results have been updated in the database.
        
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
            self.stdout.write("📧 Notification email sent")
        except Exception as e:
            self.stdout.write(f"❌ Email failed: {e}")