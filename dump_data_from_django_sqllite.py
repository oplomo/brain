import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

from django.core.management import call_command
from io import StringIO

def clean_export():
    print("Creating clean export...")
    
    # Export apps in correct dependency order
    apps_order = [
        'contenttypes',  # First
        'auth',          # Then auth (needs contenttypes)
        'sites',
        'backend',
        'square',
        'django_celery_beat',
        'sessions',
    ]
    
    all_data = []
    
    for app in apps_order:
        try:
            print(f"Exporting {app}...")
            
            # Use Django's dumpdata command
            output = StringIO()
            call_command(
                'dumpdata', 
                app, 
                format='json', 
                indent=2,
                stdout=output,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True
            )
            
            output.seek(0)
            data = output.read()
            
            if data and data.strip():
                app_data = json.loads(data)
                all_data.extend(app_data)
                print(f"  - Success: {len(app_data)} records")
            else:
                print(f"  - No data")
                
        except Exception as e:
            print(f"  - Error: {e}")
            continue
    
    # Save clean data
    output_file = 'dump_and_load_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nClean export completed! Data saved to {output_file}")
    print(f"Total records: {len(all_data)}")

if __name__ == '__main__':
    clean_export()