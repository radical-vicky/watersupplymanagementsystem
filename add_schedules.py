# add_schedules.py
import os
import django
import random
from datetime import time, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.utils import timezone
from schedules.models import WaterSchedule

# Delete existing schedules (optional - comment out to keep existing)
WaterSchedule.objects.all().delete()
print("Cleared old schedules")

# Areas and zones
areas = [
    {"name": "Westlands", "zone": "W01"},
    {"name": "Kilimani", "zone": "K01"},
    {"name": "Langata", "zone": "L01"},
    {"name": "Karen", "zone": "KRN01"},
    {"name": "CBD", "zone": "C01"},
    {"name": "Eastlands", "zone": "E01"},
    {"name": "South B", "zone": "SB01"},
    {"name": "South C", "zone": "SC01"},
    {"name": "Rongai", "zone": "R01"},
    {"name": "Thika Road", "zone": "TR01"},
]

# Water supply schedules by area
schedules_config = {
    "Westlands": {"monday": "08:00", "tuesday": "08:00", "wednesday": "08:00", "thursday": "08:00", "friday": "08:00", "saturday": "08:00", "sunday": "10:00"},
    "Kilimani": {"monday": "06:00", "tuesday": "06:00", "wednesday": "06:00", "thursday": "06:00", "friday": "06:00", "saturday": "07:00", "sunday": "09:00"},
    "Langata": {"monday": "10:00", "tuesday": "10:00", "wednesday": "10:00", "thursday": "10:00", "friday": "10:00", "saturday": "12:00", "sunday": "14:00"},
    "Karen": {"monday": "14:00", "tuesday": "14:00", "wednesday": "14:00", "thursday": "14:00", "friday": "14:00", "saturday": "16:00", "sunday": "16:00"},
    "CBD": {"monday": "05:00", "tuesday": "05:00", "wednesday": "05:00", "thursday": "05:00", "friday": "05:00", "saturday": "06:00", "sunday": "08:00"},
    "Eastlands": {"monday": "07:00", "tuesday": "07:00", "wednesday": "07:00", "thursday": "07:00", "friday": "07:00", "saturday": "08:00", "sunday": "09:00"},
    "South B": {"monday": "09:00", "tuesday": "09:00", "wednesday": "09:00", "thursday": "09:00", "friday": "09:00", "saturday": "10:00", "sunday": "11:00"},
    "South C": {"monday": "11:00", "tuesday": "11:00", "wednesday": "11:00", "thursday": "11:00", "friday": "11:00", "saturday": "12:00", "sunday": "13:00"},
    "Rongai": {"monday": "13:00", "tuesday": "13:00", "wednesday": "13:00", "thursday": "13:00", "friday": "13:00", "saturday": "14:00", "sunday": "15:00"},
    "Thika Road": {"monday": "15:00", "tuesday": "15:00", "wednesday": "15:00", "thursday": "15:00", "friday": "15:00", "saturday": "16:00", "sunday": "17:00"},
}

days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
day_display = {
    'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
    'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday'
}

schedules_created = 0

for area_info in areas:
    area_name = area_info["name"]
    zone_code = area_info["zone"]
    
    if area_name in schedules_config:
        for day in days:
            start_time_str = schedules_config[area_name].get(day, "08:00")
            start_hour = int(start_time_str.split(":")[0])
            
            # End time is 4-6 hours after start
            duration = 4 if day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] else 6
            end_hour = start_hour + duration
            end_time_str = f"{end_hour:02d}:00"
            
            start_time = time(hour=start_hour, minute=0)
            end_time = time(hour=end_hour, minute=0)
            
            notes = f"Regular water supply for {area_name} area. Duration: {duration} hours."
            
            schedule, created = WaterSchedule.objects.get_or_create(
                area_name=area_name,
                day_of_week=day,
                defaults={
                    'zone_code': zone_code,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration,
                    'is_active': True,
                    'notes': notes
                }
            )
            
            schedules_created += 1
            status = "✅" if schedule.is_active else "❌"
            print(f"{status} {area_name} ({zone_code}) - {day_display[day]}: {start_time_str} to {end_time_str} ({duration} hrs)")

print("\n" + "="*50)
print("WATER SCHEDULES SUMMARY")
print("="*50)
print(f"Total schedules created: {schedules_created}")
print(f"Active schedules: {WaterSchedule.objects.filter(is_active=True).count()}")
print("\nAreas with water schedules:")
areas_with_schedules = WaterSchedule.objects.values_list('area_name', flat=True).distinct()
for area in areas_with_schedules:
    print(f"  📍 {area}")
print("="*50)
print("✅ Water schedules added successfully!")