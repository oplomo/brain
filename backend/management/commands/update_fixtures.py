import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import requests
from backend.models import Match, MatchDate, League, Country, Season

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update fixtures from API and save to backend models'
    
    def handle(self, *args, **options):
        self.stdout.write(f"🚀 Starting fixtures update at {datetime.now()}")
        
        # Get tomorrow's date
        tomorrow_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.stdout.write(f"📅 Fetching fixtures for: {tomorrow_date}")
        
        # Fetch fixtures from API
        fixtures_data = self.fetch_fixtures(tomorrow_date)
        
        if not fixtures_data:
            self.stdout.write("❌ No fixtures data received")
            return
        
        self.stdout.write(f"📥 Found {len(fixtures_data)} fixtures")
        
        # Save fixtures to database
        saved_count = self.save_fixtures(fixtures_data)
        
        # Send email notification
        self.send_notification(tomorrow_date, len(fixtures_data), saved_count)
        
        self.stdout.write(f"✅ Completed: {saved_count} matches saved")
    
    def fetch_fixtures(self, date):
        """Fetch fixtures from Football API"""
        api_key = settings.API_FOOTBALL
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        params = {"date": date}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", [])
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
    
    def get_or_create_season(self, season_data):
        """Safely get or create season, handling duplicates"""
        season_year = self.safe_get(season_data, "year", default=datetime.now().year)
        
        # Try to get existing season first
        existing_season = Season.objects.filter(year=season_year).first()
        if existing_season:
            return existing_season, False
        
        # If no existing season, create one
        try:
            season = Season.objects.create(
                year=season_year,
                start_date=self.safe_get(season_data, "start", default=datetime.now().date()),
                end_date=self.safe_get(season_data, "end", default=datetime.now().date()),
                current=self.safe_get(season_data, "current", default=True)
            )
            return season, True
        except Exception as e:
            # If creation fails, just use the first one found
            self.stdout.write(f"⚠️ Season creation failed, using existing: {e}")
            return Season.objects.filter(year=season_year).first(), False
    
    def save_fixtures(self, fixtures):
        """Save fixtures to backend models"""
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
                home_team = self.safe_get(teams_data, "home") or {}
                away_team = self.safe_get(teams_data, "away") or {}
                venue_data = self.safe_get(fixture_data, "venue") or {}
                
                # Check if we have basic required data
                if not fixture_data or not league_data:
                    self.stdout.write("⚠️ Skipping: Missing fixture or league data")
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
                
                # Get or create MatchDate
                match_date, _ = MatchDate.objects.get_or_create(
                    date=fixture_date.date()
                )
                
                # Get or create Country
                country_name = self.safe_get(home_team, "country", default="Unknown")
                country, _ = Country.objects.get_or_create(
                    name=country_name,
                    defaults={'code': country_name[:3].upper() if country_name else "UNK"}
                )
                
                # Get or create League
                league_id = self.safe_get(league_data, "id")
                if not league_id:
                    self.stdout.write("⚠️ Skipping: No league ID")
                    continue
                    
                league, _ = League.objects.get_or_create(
                    league_id=league_id,
                    defaults={
                        'name': self.safe_get(league_data, "name", default="Unknown League"),
                        'type': self.safe_get(league_data, "type", default="League"),
                        'logo': self.safe_get(league_data, "logo", default=""),
                        'country': country
                    }
                )
                
                # Get or create Season (using safe method)
                season_data = self.safe_get(league_data, "season") or {}
                season, _ = self.get_or_create_season(season_data)
                
                if not season:
                    self.stdout.write("⚠️ Skipping: Could not get/create season")
                    continue
                
                # Add season to league
                if season not in league.seasons.all():
                    league.seasons.add(season)
                
                # Get match ID
                match_id = self.safe_get(fixture_data, "id")
                if not match_id:
                    self.stdout.write("⚠️ Skipping: No match ID")
                    continue
                
                # Create or update Match
                Match.objects.update_or_create(
                    match_id=match_id,
                    defaults={
                        "date": fixture_date,
                        "referee": self.safe_get(fixture, "referee"),
                        "timezone": self.safe_get(fixture_data, "timezone", default="UTC"),
                        "match_date": match_date,
                        "venue_name": self.safe_get(venue_data, "name"),
                        "venue_city": self.safe_get(venue_data, "city"),
                        "home_team_name": self.safe_get(home_team, "name", default="Unknown Home"),
                        "home_team_logo": self.safe_get(home_team, "logo"),
                        "home_team_id": self.safe_get(home_team, "id"),
                        "away_team_name": self.safe_get(away_team, "name", default="Unknown Away"),
                        "away_team_logo": self.safe_get(away_team, "logo"),
                        "away_team_id": self.safe_get(away_team, "id"),
                        "league": league,
                    }
                )
                
                saved_count += 1
                home_name = self.safe_get(home_team, "name", default="Home")
                away_name = self.safe_get(away_team, "name", default="Away")
                self.stdout.write(f"✅ Saved: {home_name} vs {away_name}")
                
            except Exception as e:
                self.stdout.write(f"❌ Failed to save fixture: {e}")
                continue
        
        return saved_count
    
    def send_notification(self, date, total_fixtures, saved_matches):
        """Send email notification"""
        subject = f"Fixtures Updated - {saved_matches} matches saved"
        message = f"""
        Fixtures update completed at {datetime.now()}!
        
        Date: {date}
        Fixtures fetched: {total_fixtures}
        Matches saved: {saved_matches}
        
        Ready for predictions!
        
        Click here: https://jerusqore-production.up.railway.app/select_football_prediction/
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