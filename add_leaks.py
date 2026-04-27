# add_leaks.py
import os
import django
import random
import uuid
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from leaks.models import LeakReport
from meters.models import SmartMeter

User = get_user_model()

# Get the admin user
user = User.objects.filter(username='ADMIN').first()
if not user:
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()

if not user:
    print("❌ No user found! Please create a user first.")
    exit()

print(f"✅ Using user: {user.username}")

# Get user's meters
meters = SmartMeter.objects.filter(user=user)
if not meters.exists():
    print("❌ No meters found for this user. Creating a test meter...")
    meter = SmartMeter.objects.create(
        meter_id=f"WTR-{uuid.uuid4().hex[:6].upper()}",
        user=user,
        location="Nairobi, Main",
        status='active',
        last_reading=1000,
        last_reading_date=timezone.now()
    )
    meters = [meter]
    print(f"✅ Created meter: {meter.meter_id}")
else:
    meter = meters.first()
    print(f"✅ Using meter: {meter.meter_id}")

# Delete existing leaks (optional - comment out if you want to keep existing)
# LeakReport.objects.filter(user=user).delete()
# print("Cleared old leak reports")

# Leak locations
locations = [
    "Kitchen sink", "Bathroom pipe", "Main water inlet", "Outside pipe", 
    "Toilet tank", "Water heater connection", "Garden tap", "Underground pipe",
    "Roof tank overflow", "Balcony tap", "Garage pipe", "Laundry area"
]

# Status options
status_options = ['detected', 'confirmed', 'in_progress', 'resolved']
type_options = ['reported', 'detected', 'reported', 'detected']  # More reported than detected

# Create leak reports
leaks_created = 0
today = timezone.now()

for i in range(15):  # Create 15 leak reports
    # Random date within last 90 days
    days_ago = random.randint(0, 90)
    reported_date = today - timedelta(days=days_ago)
    
    # Random status (older leaks more likely to be resolved)
    if days_ago > 60:
        status = 'resolved'
    elif days_ago > 30:
        status = random.choice(['resolved', 'resolved', 'in_progress'])
    else:
        status = random.choice(['detected', 'confirmed', 'in_progress'])
    
    # Random type
    leak_type = random.choice(type_options)
    
    # Random location
    location = random.choice(locations)
    
    # Random description based on type
    if leak_type == 'detected':
        description = f"System detected abnormal water flow of {random.randint(50, 500)} liters per hour"
    else:
        descriptions = [
            f"Water leaking from {location}. Needs immediate attention.",
            f"Dripping water constantly from {location}. Wasting water.",
            f"Water pooling around {location}. Suspect pipe burst.",
            f"Moisture detected near {location}. Possible underground leak.",
            f"{location} is leaking badly. Water pressure is low."
        ]
        description = random.choice(descriptions)
    
    # Generate report ID
    report_id = f"LEAK-{uuid.uuid4().hex[:8].upper()}"
    
    # Create leak report
    leak = LeakReport.objects.create(
        report_id=report_id,
        meter=meter,
        user=user,
        type=leak_type,
        status=status,
        description=description,
        location=location,
        reported_at=reported_date,
        resolved_at=reported_date + timedelta(days=random.randint(1, 10)) if status == 'resolved' else None,
        estimated_water_loss=random.randint(100, 5000) if status != 'detected' else None
    )
    leaks_created += 1
    
    # Show status emoji
    if status == 'resolved':
        status_icon = "✅"
    elif status == 'in_progress':
        status_icon = "🔄"
    elif status == 'confirmed':
        status_icon = "📌"
    else:
        status_icon = "⚠️"
    
    print(f"{status_icon} {report_id}: {location} - {status} ({reported_date.strftime('%b %d')})")

print("\n" + "="*50)
print("LEAK REPORTS SUMMARY")
print("="*50)
print(f"Total leaks created: {leaks_created}")
print(f"Active leaks (detected/confirmed/in_progress): {LeakReport.objects.filter(user=user, status__in=['detected', 'confirmed', 'in_progress']).count()}")
print(f"Resolved leaks: {LeakReport.objects.filter(user=user, status='resolved').count()}")
print("="*50)
print("✅ Leak reports added successfully!")