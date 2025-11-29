import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')
django.setup()

from django.core.management import call_command

print("Importing clean export...")
try:
    call_command('loaddata', 'dump_and_load_data.json')
    print("SUCCESS: Clean data imported successfully!")
except Exception as e:
    print(f"ERROR: {e}")