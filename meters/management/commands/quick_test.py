from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random

from meters.models import SmartMeter, MeterReading
from billing.models import Bill
from payments.models import Payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Quick setup for testing payments (creates 3 test users with bills)'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Creating quick test data for payment testing...")
        
        # Create test users
        test_users = []
        for i in range(1, 4):
            username = f"pay_test_{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@test.com",
                    'first_name': f"Test{i}",
                    'last_name': "User"
                }
            )
            
            if created:
                user.set_password("test123")
                user.save()
                
                # Create meter
                meter = SmartMeter.objects.create(
                    meter_id=f"TEST{i:03d}",
                    user=user,
                    location=f"Test Location {i}",
                    status='active',
                    last_reading=Decimal(random.randint(100, 500))
                )
                
                # Create current bill
                bill = Bill.objects.create(
                    meter=meter,
                    user=user,
                    billing_period_start=timezone.now() - timezone.timedelta(days=30),
                    billing_period_end=timezone.now(),
                    previous_reading=Decimal(random.randint(100, 300)),
                    current_reading=Decimal(random.randint(300, 600)),
                    consumption=Decimal(random.randint(50, 200)),
                    amount=Decimal(random.randint(1000, 5000)),
                    status='unpaid',
                    due_date=timezone.now() + timezone.timedelta(days=7)
                )
                
                test_users.append({'user': user, 'meter': meter, 'bill': bill})
                
                self.stdout.write(f"✅ Created: {username} / test123 | Bill: KSh {bill.amount}")
        
        # Display summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("TEST CREDENTIALS")
        self.stdout.write("="*50)
        for tu in test_users:
            self.stdout.write(f"Username: {tu['user'].username}")
            self.stdout.write(f"Password: test123")
            self.stdout.write(f"Bill Amount: KSh {tu['bill'].amount}")
            self.stdout.write("-"*30)
        
        self.stdout.write("\n💡 Login at: http://localhost:8000/accounts/login/")
        self.stdout.write("💰 Navigate to Dashboard → Bills to test payments")