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
    
    def save_fixtures(self, fixtures):
        """Save fixtures to backend models"""
        saved_count = 0
        
        for fixture in fixtures:
            try:
                # Extract data from fixture
                fixture_data = fixture.get("fixture", {})
                league_data = fixture.get("league", {})
                teams_data = fixture.get("teams", {})
                home_team = teams_data.get("home", {})
                away_team = teams_data.get("away", {})
                venue_data = fixture_data.get("venue", {})
                
                # Parse fixture date
                fixture_date = datetime.fromisoformat(fixture_data["date"].replace("Z", ""))
                
                # Get or create MatchDate
                match_date, _ = MatchDate.objects.get_or_create(
                    date=fixture_date.date()
                )
                
                # Get or create Country
                country_name = home_team.get("country", "Unknown")
                country, _ = Country.objects.get_or_create(
                    name=country_name,
                    defaults={'code': country_name[:3].upper() if country_name else "UNK"}
                )
                
                # Get or create League
                league_id = league_data["id"]
                league, _ = League.objects.get_or_create(
                    league_id=league_id,
                    defaults={
                        'name': league_data.get("name", "Unknown League"),
                        'type': league_data.get("type", "League"),
                        'logo': league_data.get("logo", ""),
                        'country': country
                    }
                )
                
                # Get or create Season
                season_data = league_data.get("season", {})
                season_year = season_data.get("year", datetime.now().year)
                season, _ = Season.objects.get_or_create(
                    year=season_year,
                    defaults={
                        'start_date': season_data.get("start", datetime.now().date()),
                        'end_date': season_data.get("end", datetime.now().date()),
                        'current': season_data.get("current", True)
                    }
                )
                
                # Add season to league
                if season not in league.seasons.all():
                    league.seasons.add(season)
                
                # Create or update Match
                Match.objects.update_or_create(
                    match_id=fixture_data["id"],
                    defaults={
                        "date": fixture_date,
                        "referee": fixture.get("referee"),
                        "timezone": fixture_data.get("timezone", "UTC"),
                        "match_date": match_date,
                        "venue_name": venue_data.get("name"),
                        "venue_city": venue_data.get("city"),
                        "home_team_name": home_team.get("name", "Unknown Home"),
                        "home_team_logo": home_team.get("logo"),
                        "home_team_id": home_team.get("id"),
                        "away_team_name": away_team.get("name", "Unknown Away"),
                        "away_team_logo": away_team.get("logo"),
                        "away_team_id": away_team.get("id"),
                        "league": league,
                    }
                )
                
                saved_count += 1
                self.stdout.write(f"✅ Saved: {home_team.get('name')} vs {away_team.get('name')}")
                
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