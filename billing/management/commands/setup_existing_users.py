from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
import random

from meters.models import SmartMeter, MeterReading
from billing.models import Bill
from payments.models import Payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup meters, bills, and payments for existing users'
    
    def handle(self, *args, **options):
        # Get users without meters
        users_without_meters = User.objects.filter(
            ~Q(username__startswith='admin'),
            meters__isnull=True
        )
        
        count = users_without_meters.count()
        
        if count == 0:
            self.stdout.write("✅ All users already have meters")
            return
        
        self.stdout.write(f"\n🔄 Setting up resources for {count} users...\n")
        
        for user in users_without_meters:
            # Create meter
            meter_id = f"WTR-{random.randint(10000, 99999)}"
            meter = SmartMeter.objects.create(
                meter_id=meter_id,
                user=user,
                location="Auto-created Location",
                status='active',
                last_reading=Decimal(random.randint(100, 500)),
                last_reading_date=timezone.now(),
                firmware_version="1.0.0",
                battery_level=random.randint(70, 100),
                signal_strength=random.randint(60, 100)
            )
            
            # Generate readings
            current_reading = Decimal(random.randint(100, 500))
            for day in range(30):
                consumption = Decimal(random.uniform(5, 50))
                current_reading += consumption
                MeterReading.objects.create(
                    meter=meter,
                    reading_value=current_reading,
                    consumption=consumption,
                    timestamp=timezone.now() - timedelta(days=29-day)
                )
            
            # Update meter
            latest_reading = meter.readings.order_by('-timestamp').first()
            if latest_reading:
                meter.last_reading = latest_reading.reading_value
                meter.last_reading_date = latest_reading.timestamp
                meter.save()
            
            # Create bills
            generate_bills_for_user(user, meter)
            
            self.stdout.write(f"✅ Setup for {user.username}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Completed for {count} users"))

def generate_bills_for_user(user, meter):
    """Generate bills for the user"""
    current_month = timezone.now().replace(day=1)
    
    readings = meter.readings.filter(timestamp__gte=current_month).order_by('timestamp')
    
    if readings.exists():
        first_reading = readings.first()
        last_reading = readings.last()
        consumption = last_reading.reading_value - first_reading.reading_value
        if consumption <= 0:
            consumption = Decimal(random.uniform(10, 100))
    else:
        consumption = Decimal(random.uniform(10, 100))
    
    # Calculate bill amount
    if consumption <= 20:
        rate = Decimal('50.00')
    elif consumption <= 50:
        rate = Decimal('75.00')
    elif consumption <= 100:
        rate = Decimal('100.00')
    else:
        rate = Decimal('150.00')
    
    amount = consumption * rate + Decimal('500.00')
    amount = (amount * Decimal('1.16')).quantize(Decimal('0.01'))
    
    Bill.objects.create(
        bill_number=f"BILL-{user.id}-{timezone.now().strftime('%Y%m')}",
        meter=meter,
        user=user,
        billing_month=current_month,
        issued_date=timezone.now(),
        consumption=consumption,
        amount=amount,
        total_amount=amount,
        fixed_charge=Decimal('500.00'),
        tariff_rate=rate,
        status='pending',
        due_date=current_month + timedelta(days=14)
    )