from decimal import Decimal
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
import random

User = get_user_model()

@receiver(post_save, sender=User)
def auto_create_user_resources(sender, instance, created, **kwargs):
    """When a new user registers, automatically create meter, bills, and payment history"""
    
    if not created:
        return
    
    if instance.is_superuser:
        return
    
    # Check if user already has a meter
    from meters.models import SmartMeter
    if SmartMeter.objects.filter(user=instance).exists():
        return
    
    print(f"\n🔄 Auto-creating resources for new user: {instance.username}")
    
    try:
        # Create meter
        meter = SmartMeter.objects.create(
            meter_id=f"WTR-{random.randint(10000, 99999)}",
            user=instance,
            location=random.choice([
                'Nairobi - Westlands', 'Nairobi - Kilimani', 'Mombasa - CBD',
                'Kisumu - Milimani', 'Nakuru - CBD', 'Eldoret - Kapsoya'
            ]),
            status='active',
            last_reading=Decimal(random.randint(100, 500)),
            last_reading_date=timezone.now(),
            firmware_version="1.0.0",
            battery_level=random.randint(70, 100),
            signal_strength=random.randint(60, 100)
        )
        
        print(f"   ✅ Created meter: {meter.meter_id}")
        
        # Generate initial readings (30 days)
        from meters.models import MeterReading
        current_reading = Decimal(random.randint(100, 500))
        for day in range(30):
            consumption = Decimal(random.uniform(10, 50))
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
        
        print(f"   ✅ Created 30 days of readings")
        
        # Generate bills for the user (last 3 months)
        from billing.models import Bill
        from payments.models import Payment
        
        for months_ago in range(3):
            billing_month = (timezone.now().replace(day=1) - timedelta(days=months_ago * 30)).replace(day=1)
            
            # Calculate consumption for this month
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
            else:
                consumption = Decimal(random.uniform(10, 100))
            
            if consumption <= 0:
                consumption = Decimal(random.uniform(10, 100))
            
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
            
            # Status: current month pending, older paid
            if months_ago == 0:
                status = 'pending'
            else:
                status = 'paid'
            
            bill = Bill.objects.create(
                bill_number=f"BILL-{instance.id}-{billing_month.strftime('%Y%m')}",
                meter=meter,
                user=instance,
                billing_month=billing_month,
                issued_date=billing_month + timedelta(days=5),
                consumption=consumption,
                amount=amount,
                total_amount=amount,
                fixed_charge=Decimal('500.00'),
                tariff_rate=rate,
                status=status,
                due_date=billing_month + timedelta(days=30)
            )
            
            print(f"   ✅ Created {status} bill: {bill.bill_number} - KES {amount:,.2f}")
            
            if status == 'paid':
                bill.paid_date = billing_month + timedelta(days=random.randint(10, 25))
                bill.save()
                
                # Create payment record
                Payment.objects.create(
                    user=instance,
                    bill=bill,
                    amount=amount,
                    payment_method=random.choice(['mpesa', 'bank_transfer', 'cash']),
                    transaction_id=f"TXN{random.randint(100000000, 999999999)}",
                    status='completed',
                    payment_date=bill.paid_date
                )
                print(f"   ✅ Created payment record for bill {bill.bill_number}")
        
        print(f"✅ Successfully created all resources for {instance.username}\n")
        
    except Exception as e:
        print(f"❌ Error creating resources for {instance.username}: {str(e)}")