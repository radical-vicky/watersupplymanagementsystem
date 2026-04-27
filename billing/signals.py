from decimal import Decimal
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random

from django.contrib.auth import get_user_model
from meters.models import SmartMeter, MeterReading
from billing.models import Bill
from payments.models import Payment

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_resources(sender, instance, created, **kwargs):
    """When a new user registers, create meter, readings, bills, and payment records"""
    if created and not instance.is_superuser:
        # Create smart meter for the user
        meter_id = f"WTR-{random.randint(10000, 99999)}"
        meter = SmartMeter.objects.create(
            meter_id=meter_id,
            user=instance,
            location="New Customer Location",
            status='active',
            last_reading=Decimal(random.randint(100, 500)),
            last_reading_date=timezone.now(),
            firmware_version="1.0.0",
            battery_level=random.randint(70, 100),
            signal_strength=random.randint(60, 100)
        )
        
        # Generate initial meter readings for the last 30 days
        current_reading = Decimal(random.randint(100, 500))
        for day in range(30):
            consumption = Decimal(random.uniform(5, 50))
            current_reading += consumption
            MeterReading.objects.create(
                meter=meter,
                reading_value=current_reading,
                consumption=consumption,
                timestamp=timezone.now() - timedelta(days=29-day),
                is_synced=True
            )
        
        # Update meter with latest reading
        latest_reading = meter.readings.order_by('-timestamp').first()
        if latest_reading:
            meter.last_reading = latest_reading.reading_value
            meter.last_reading_date = latest_reading.timestamp
            meter.save()
        
        # Generate bills for the user
        generate_bills_for_user(instance, meter)
        
        print(f"✅ Auto-created resources for new user: {instance.username}")

def generate_bills_for_user(user, meter):
    """Generate bills for the user"""
    # Generate current month bill
    current_month = timezone.now().replace(day=1)
    
    # Get readings for current month
    readings = meter.readings.filter(
        timestamp__gte=current_month
    ).order_by('timestamp')
    
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
    amount = amount * Decimal('1.16')
    amount = amount.quantize(Decimal('0.01'))
    
    # Create current bill
    bill = Bill.objects.create(
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
    
    # Also generate a previous month bill (for history)
    previous_month = current_month - timedelta(days=30)
    prev_consumption = Decimal(random.uniform(10, 100))
    prev_amount = prev_consumption * Decimal('75.00') + Decimal('500.00')
    prev_amount = (prev_amount * Decimal('1.16')).quantize(Decimal('0.01'))
    
    Bill.objects.create(
        bill_number=f"BILL-{user.id}-{previous_month.strftime('%Y%m')}",
        meter=meter,
        user=user,
        billing_month=previous_month,
        issued_date=previous_month + timedelta(days=5),
        consumption=prev_consumption,
        amount=prev_amount,
        total_amount=prev_amount,
        fixed_charge=Decimal('500.00'),
        tariff_rate=Decimal('75.00'),
        status='paid',
        paid_date=previous_month + timedelta(days=10),
        due_date=previous_month + timedelta(days=14)
    )
    
    # Generate a payment record for the previous bill
    Payment.objects.create(
        user=user,
        bill=bill,  # Link to current bill (or could link to previous)
        amount=prev_amount,
        payment_method='mpesa',
        transaction_id=f"TXN{random.randint(100000000, 999999999)}",
        status='completed',
        payment_date=previous_month + timedelta(days=10)
    )