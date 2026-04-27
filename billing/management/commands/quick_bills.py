import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from billing.models import Bill
from meters.models import SmartMeter

User = get_user_model()

class Command(BaseCommand):
    help = 'Quickly generate pending bills for testing payments'
    
    def handle(self, *args, **options):
        self.stdout.write("\n🚀 Creating test bills for all users...\n")
        
        users = User.objects.filter(is_superuser=False)
        
        if not users.exists():
            self.stdout.write("❌ No users found. Run 'python manage.py simulate_data --quick' first")
            return
        
        bills_created = 0
        
        for user in users:
            meter = SmartMeter.objects.filter(user=user).first()
            if not meter:
                self.stdout.write(f"⚠️ No meter for {user.username}, skipping...")
                continue
            
            # Random consumption between 10 and 200
            consumption = Decimal(random.uniform(10, 200))
            
            # Calculate amount
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
            
            bill_number = f"TEST-{user.id}-{timezone.now().strftime('%Y%m')}-{random.randint(100, 999)}"
            
            bill = Bill.objects.create(
                bill_number=bill_number,
                meter=meter,
                user=user,
                billing_month=timezone.now().replace(day=1),
                issued_date=timezone.now(),
                consumption=consumption,
                amount=amount,
                total_amount=amount,
                fixed_charge=Decimal('500.00'),
                tariff_rate=rate,
                status='pending',
                due_date=timezone.now() + timedelta(days=14)
            )
            
            bills_created += 1
            self.stdout.write(f"✅ {user.username}: {bill_number} - KES {amount:,.2f}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Created {bills_created} test bills!\n"))
        self.stdout.write("Login and go to Billing page to see pending bills and test payments.")