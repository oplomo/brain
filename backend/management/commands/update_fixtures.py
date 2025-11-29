import os
import django
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import requests
import traceback
from backend.models import Match, MatchDate, League, Country, Season

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

class Command(BaseCommand):
    help = 'Update fixtures from API and send prediction reminder'
    
    def handle(self, *args, **options):
        self.stdout.write(f"🚀 CRON JOB STARTED: update_fixtures at {datetime.now()}")
        
        tomorrow_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.stdout.write(f"📅 Fetching fixtures for date: {tomorrow_date}")
        
        fixtures_data = self.fetch_fixtures_res(tomorrow_date)
        
        if fixtures_data:
            self.stdout.write(f"📥 Found {len(fixtures_data)} fixtures from API")
            new_count, updated_count = self.save_fixtures_to_db(fixtures_data)
            total_fixtures = len(fixtures_data)
            
            # Verification
            total_match_dates = MatchDate.objects.count()
            total_matches = Match.objects.count()
            recent_matches = Match.objects.filter(match_date__date=tomorrow_date).count()
            
            self.stdout.write(f"📊 VERIFICATION:")
            self.stdout.write(f"   Total MatchDate records: {total_match_dates}")
            self.stdout.write(f"   Total Match records: {total_matches}")
            self.stdout.write(f"   Matches for {tomorrow_date}: {recent_matches}")
            self.stdout.write(f"   Fixtures from API: {len(fixtures_data)}")
            
            if recent_matches == 0 and len(fixtures_data) > 0:
                self.stdout.write(self.style.WARNING("⚠️  WARNING: Fixtures were fetched but no matches were saved!"))
            
            # Send email with prediction link
            subject = f"Fixtures Updated - {total_fixtures} matches available"
            message = f"""
            Fixtures update completed at {datetime.now()}!
            
            Statistics:
            - Total fixtures fetched: {total_fixtures}
            - New matches added: {new_count}
            - Existing matches updated: {updated_count}
            - Matches saved for {tomorrow_date}: {recent_matches}
            
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
            subject = "Fixtures Update - No Matches Tomorrow"
            message = f"""
            Fixtures update completed at {datetime.now()} but no matches found for tomorrow.
            
            Date checked: {tomorrow_date}
            
            This could mean:
            - No matches scheduled for tomorrow
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
        new_matches_count = 0
        updated_matches_count = 0
        
        for fixture in res_data:
            try:
                # Get or create MatchDate
                fixture_date = datetime.fromisoformat(fixture["fixture"]["date"].replace("Z", ""))
                match_date, created = MatchDate.objects.get_or_create(
                    date=fixture_date.date()
                )
                
                # Get league data
                league_data = fixture["league"]
                
                # Get or create Country
                country_name = fixture["teams"]["home"].get("country", "Unknown")
                country, _ = Country.objects.get_or_create(
                    name=country_name,
                    defaults={'code': country_name[:3].upper() if country_name else "UNK"}
                )
                
                # Get or create League
                league, _ = League.objects.get_or_create(
                    league_id=league_data["id"],
                    defaults={
                        'name': league_data["name"],
                        'type': league_data["type"],
                        'logo': league_data.get("logo", ""),
                        'country': country
                    }
                )
                
                # Get or create Season
                season_data = fixture["league"].get("season", {})
                season_year = season_data.get("year", datetime.now().year)
                season, _ = Season.objects.get_or_create(
                    year=season_year,
                    defaults={
                        'start_date': season_data.get("start", datetime.now().date()),
                        'end_date': season_data.get("end", datetime.now().date()),
                        'current': season_data.get("current", True)
                    }
                )
                
                # Add season to league if not already added
                if season not in league.seasons.all():
                    league.seasons.add(season)
                
                # Create or update Match
                venue_info = fixture.get("fixture", {}).get("venue", {})
                
                # Debug: Print what we're about to save
                self.stdout.write(f"🔄 Processing match: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                
                obj, created = Match.objects.update_or_create(
                    match_id=fixture["fixture"]["id"],
                    defaults={
                        "date": fixture_date,
                        "referee": fixture.get("referee"),
                        "timezone": fixture["fixture"]["timezone"],
                        "match_date": match_date,
                        "venue_name": venue_info.get("name"),
                        "venue_city": venue_info.get("city"),
                        "home_team_name": fixture["teams"]["home"]["name"],
                        "home_team_logo": fixture["teams"]["home"].get("logo"),
                        "home_team_id": fixture["teams"]["home"]["id"],
                        "away_team_name": fixture["teams"]["away"]["name"],
                        "away_team_logo": fixture["teams"]["away"].get("logo"),
                        "away_team_id": fixture["teams"]["away"]["id"],
                        "league": league,
                    },
                )
                
                if created:
                    new_matches_count += 1
                    self.stdout.write(f"✅➕ New match CREATED: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                else:
                    updated_matches_count += 1
                    self.stdout.write(f"✅📝 Match UPDATED: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error saving match {fixture['fixture']['id']}: {str(e)}"))
                self.stdout.write(self.style.ERROR(f"❌ Full traceback: {traceback.format_exc()}"))
                continue
                
        return new_matches_count, updated_matches_count