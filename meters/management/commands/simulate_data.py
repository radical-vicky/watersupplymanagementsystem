import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from meters.models import SmartMeter, MeterReading

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate simulated water meters and readings for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of test users to create')
        parser.add_argument('--readings', type=int, default=30, help='Number of readings per meter')
        parser.add_argument('--clear', action='store_true', help='Clear existing test data')
        parser.add_argument('--quick', action='store_true', help='Quick setup with 3 users')
        
    def handle(self, *args, **options):
        if options['quick']:
            self.quick_setup()
            return
            
        if options['clear']:
            self.clear_test_data()
            
        num_users = options['users']
        num_readings = options['readings']
        
        self.stdout.write(self.style.SUCCESS(f'\n🚰 Starting simulation with {num_users} users...\n'))
        
        test_users = self.create_users_with_meters(num_users)
        
        if num_readings > 0:
            self.generate_meter_readings(num_readings)
            
        self.display_summary()
        
        if test_users:
            self.save_credentials(test_users)
            
        self.stdout.write(self.style.SUCCESS('\n✅ Simulation completed!\n'))
    
    def quick_setup(self):
        """Quick setup with 3 users"""
        self.stdout.write("\n🚀 Creating 3 test users...\n")
        
        test_users = []
        locations = ['Nairobi - Westlands', 'Mombasa - CBD', 'Kisumu - Milimani']
        
        for i in range(1, 4):
            username = f"test_user_{i}"
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"⚠️ User {username} already exists")
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.com",
                password="test123",
                first_name=f"Test{i}",
                last_name="User"
            )
            
            meter = SmartMeter.objects.create(
                meter_id=f"TEST{i:03d}",
                user=user,
                location=locations[i-1],
                status='active',
                last_reading=Decimal(random.randint(100, 500)),
                last_reading_date=timezone.now(),
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
            
            test_users.append({
                'user': user,
                'meter': meter,
                'password': 'test123'
            })
            
            self.stdout.write(f"✅ Created: {username} / test123 | Meter: {meter.meter_id}")
        
        self.display_quick_credentials(test_users)
        self.save_credentials(test_users)
    
    def clear_test_data(self):
        """Clear all test data"""
        self.stdout.write('Clearing test data...')
        
        test_users = User.objects.filter(Q(username__startswith='test_user_'))
        count = test_users.count()
        test_users.delete()
        
        self.stdout.write(f'Deleted {count} test users')
    
    def create_users_with_meters(self, num_users):
        """Create test users with meters"""
        users_created = []
        locations = [
            'Nairobi - Westlands', 'Nairobi - Kilimani', 'Nairobi - Buruburu',
            'Mombasa - Nyali', 'Mombasa - CBD', 'Kisumu - Milimani',
            'Nakuru - CBD', 'Eldoret - Kapsoya', 'Thika - Makongeni'
        ]
        
        for i in range(num_users):
            username = f"test_user_{i+1}"
            email = f"testuser{i+1}@example.com"
            password = "Test@123456"
            
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=f"Test{i+1}",
                last_name="User"
            )
            
            meter = SmartMeter.objects.create(
                meter_id=f"WTR-{random.randint(10000, 99999)}",
                user=user,
                location=random.choice(locations),
                status=random.choice(['active', 'active', 'active', 'active', 'inactive']),
                last_reading=Decimal(random.randint(0, 1000)),
                last_reading_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                firmware_version=f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                battery_level=random.randint(70, 100),
                signal_strength=random.randint(60, 100)
            )
            
            users_created.append({
                'user': user,
                'meter': meter,
                'password': password
            })
            
            self.stdout.write(f"✅ Created: {username} | Password: {password} | Meter: {meter.meter_id}")
        
        return users_created
    
    def generate_meter_readings(self, num_readings):
        """Generate historical meter readings"""
        meters = SmartMeter.objects.filter(status='active')
        
        for meter in meters:
            current_reading = float(meter.last_reading) if meter.last_reading else 0
            
            for day in range(num_readings):
                consumption = Decimal(random.uniform(5, 50))
                current_reading += float(consumption)
                
                reading_date = timezone.now() - timedelta(days=num_readings - day)
                
                MeterReading.objects.create(
                    meter=meter,
                    reading_value=Decimal(str(round(current_reading, 3))),
                    consumption=consumption,
                    timestamp=reading_date,
                    is_synced=True
                )
            
            latest_reading = meter.readings.order_by('-timestamp').first()
            if latest_reading:
                meter.last_reading = latest_reading.reading_value
                meter.last_reading_date = latest_reading.timestamp
                meter.save()
            
            self.stdout.write(f"📊 Generated {num_readings} readings for {meter.meter_id}")
    
    def display_summary(self):
        """Display summary"""
        test_users = User.objects.filter(username__startswith='test_user_')
        total_users = test_users.count()
        total_meters = SmartMeter.objects.filter(user__in=test_users).count()
        total_readings = MeterReading.objects.filter(meter__user__in=test_users).count()
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 SIMULATION SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Users: {total_users}")
        self.stdout.write(f"Meters: {total_meters}")
        self.stdout.write(f"Readings: {total_readings}")
        self.stdout.write("="*50)
    
    def display_quick_credentials(self, test_users):
        """Display quick credentials"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("TEST CREDENTIALS")
        self.stdout.write("="*50)
        for tu in test_users:
            self.stdout.write(f"Username: {tu['user'].username}")
            self.stdout.write(f"Password: test123")
            self.stdout.write(f"Meter: {tu['meter'].meter_id}")
            self.stdout.write("-"*30)
    
    def save_credentials(self, test_users):
        """Save credentials to file"""
        filename = 'test_credentials.txt'
        
        with open(filename, 'w') as f:
            f.write("WATER SUPPLY SYSTEM - TEST CREDENTIALS\n")
            f.write("="*50 + "\n\n")
            
            for user_info in test_users:
                f.write(f"Username: {user_info['user'].username}\n")
                f.write(f"Password: {user_info['password']}\n")
                f.write(f"Email: {user_info['user'].email}\n")
                f.write(f"Meter ID: {user_info['meter'].meter_id}\n")
                f.write("-"*30 + "\n\n")
        
        self.stdout.write(f"\n📝 Credentials saved to: {filename}")