import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models

from billing.models import Bill
from meters.models import SmartMeter, MeterReading

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate pending bills for all users for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, help='Number of users to generate bills for')
        parser.add_argument('--months', type=int, default=3, help='Number of months of bills to generate')
        parser.add_argument('--clear', action='store_true', help='Clear existing pending bills first')
        
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_pending_bills()
        
        months = options['months']
        
        # Get users
        if options['users']:
            users = User.objects.filter(is_superuser=False)[:options['users']]
        else:
            users = User.objects.filter(is_superuser=False)
        
        self.stdout.write(self.style.SUCCESS(f'\n💰 Generating pending bills for {users.count()} users...\n'))
        
        bills_created = 0
        
        for user in users:
            # Get or create meter for user
            meter = SmartMeter.objects.filter(user=user).first()
            if not meter:
                meter = SmartMeter.objects.create(
                    meter_id=f"WTR-{random.randint(10000, 99999)}",
                    user=user,
                    location="Default Location",
                    status='active',
                    last_reading=Decimal(random.randint(0, 1000)),
                    last_reading_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                    firmware_version="1.0.0",
                    battery_level=random.randint(70, 100),
                    signal_strength=random.randint(60, 100)
                )
                
                current_reading = Decimal(random.randint(100, 500))
                for day in range(30):
                    consumption = Decimal(random.uniform(10, 50))
                    current_reading += consumption
                    MeterReading.objects.create(
                        meter=meter,
                        reading_value=current_reading,
                        consumption=consumption,
                        timestamp=timezone.now() - timedelta(days=30-day)
                    )
                
                latest_reading = meter.readings.order_by('-timestamp').first()
                if latest_reading:
                    meter.last_reading = latest_reading.reading_value
                    meter.last_reading_date = latest_reading.timestamp
                    meter.save()
            
            # Generate bills for the last X months
            for month in range(months):
                # Calculate billing month
                billing_month = (timezone.now().replace(day=1) - timedelta(days=month * 30)).replace(day=1)
                
                # Check if bill already exists for this month
                if Bill.objects.filter(meter=meter, billing_month=billing_month).exists():
                    continue
                
                # Get readings for this period
                month_start = billing_month
                if billing_month.month == 12:
                    month_end = billing_month.replace(year=billing_month.year+1, month=1, day=1)
                else:
                    month_end = billing_month.replace(month=billing_month.month+1, day=1)
                
                readings = meter.readings.filter(
                    timestamp__gte=month_start,
                    timestamp__lt=month_end
                ).order_by('timestamp')
                
                if readings.exists():
                    first_reading = readings.first()
                    last_reading = readings.last()
                    
                    consumption = last_reading.reading_value - first_reading.reading_value
                    
                    if consumption < 0:
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
                    amount = amount * Decimal('1.16')
                    amount = amount.quantize(Decimal('0.01'))
                    
                    # Generate bill number
                    bill_number = f"BILL-{user.id}-{billing_month.strftime('%Y%m')}-{random.randint(1000, 9999)}"
                    
                    bill = Bill.objects.create(
                        bill_number=bill_number,
                        meter=meter,
                        user=user,
                        billing_month=billing_month,
                        issued_date=timezone.now(),
                        consumption=consumption,
                        amount=amount,
                        total_amount=amount,
                        fixed_charge=Decimal('500.00'),
                        tariff_rate=rate,
                        status='pending',
                        due_date=billing_month + timedelta(days=30)
                    )
                    
                    bills_created += 1
                    self.stdout.write(f"✅ Created bill for {user.username}: {bill_number} - KES {amount:,.2f}")
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n📊 Summary: {bills_created} pending bills created\n'))
        
        # Display users with bills
        users_with_bills = User.objects.filter(bills__status='pending').distinct()
        self.stdout.write("👥 Users with pending bills:")
        for user in users_with_bills[:10]:
            pending_total = Bill.objects.filter(user=user, status='pending').aggregate(total=models.Sum('total_amount'))['total'] or 0
            self.stdout.write(f"   - {user.username}: KES {pending_total:,.2f}")
    
    def clear_pending_bills(self):
        """Clear all pending bills"""
        count = Bill.objects.filter(status='pending').count()
        Bill.objects.filter(status='pending').delete()
        self.stdout.write(f'🗑️ Cleared {count} pending bills')