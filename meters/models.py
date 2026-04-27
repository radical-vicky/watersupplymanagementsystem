from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum
from decimal import Decimal

class SmartMeter(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('faulty', 'Faulty'),
    )
    
    meter_id = models.CharField(max_length=50, unique=True, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meters')
    location = models.CharField(max_length=255)
    installation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_reading = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    last_reading_date = models.DateTimeField(null=True, blank=True)
    firmware_version = models.CharField(max_length=20, default='1.0.0')
    battery_level = models.IntegerField(default=100)
    signal_strength = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'smart_meters'
        ordering = ['-installation_date']
    
    def __str__(self):
        return f"Meter {self.meter_id} - {self.user.get_full_name() or self.user.username}"
    
    def update_reading(self, reading_value):
        """Update meter reading and calculate consumption"""
        previous_reading = self.last_reading
        consumption = reading_value - previous_reading
        
        # Ensure consumption is not negative (meter reset or error)
        if consumption < 0:
            consumption = 0
        
        # Create reading record
        reading = MeterReading.objects.create(
            meter=self,
            reading_value=reading_value,
            consumption=consumption,
            timestamp=timezone.now()
        )
        
        # Update meter
        self.last_reading = reading_value
        self.last_reading_date = timezone.now()
        self.save()
        
        # Check for potential leak (only if consumption is unusually high)
        avg_consumption = self.get_average_daily_consumption()
        if avg_consumption > 0 and consumption > avg_consumption * 3:
            self.detect_leak(consumption, avg_consumption)
        
        return consumption
    
    def detect_leak(self, consumption, avg_consumption):
        """Create leak detection alert"""
        try:
            from leaks.models import LeakReport
            LeakReport.objects.create(
                meter=self,
                user=self.user,
                type='detected',
                status='detected',
                description=f"Unusual consumption detected: {consumption:.2f} units (Avg: {avg_consumption:.2f})"
            )
        except ImportError:
            # If leaks app doesn't exist yet, just log
            print(f"Leak detected for meter {self.meter_id} but leaks app not installed")
    
    def get_average_daily_consumption(self):
        """Calculate average daily consumption from last 7 days"""
        last_7_days = MeterReading.objects.filter(
            meter=self,
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        )
        if last_7_days.exists():
            avg = last_7_days.aggregate(Avg('consumption'))['consumption__avg']
            return avg or 0
        return 0
    
    def get_total_consumption(self, days=30):
        """Get total consumption for specified number of days"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        readings = MeterReading.objects.filter(
            meter=self,
            timestamp__gte=start_date
        )
        total = readings.aggregate(Sum('consumption'))['consumption__sum']
        return total or 0
    
    def get_current_month_consumption(self):
        """Get consumption for current month"""
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        readings = MeterReading.objects.filter(
            meter=self,
            timestamp__gte=start_of_month
        )
        total = readings.aggregate(Sum('consumption'))['consumption__sum']
        return total or 0
    
    def is_online(self):
        """Check if meter is reporting properly"""
        if self.status != 'active':
            return False
        if self.battery_level < 10:
            return False
        if not self.last_reading_date:
            return False
        # Consider offline if no reading in last 24 hours
        hours_since_last_reading = (timezone.now() - self.last_reading_date).total_seconds() / 3600
        return hours_since_last_reading < 24
    
    @property
    def estimated_monthly_bill(self):
        """Estimate monthly bill based on average consumption"""
        avg_daily = self.get_average_daily_consumption()
        monthly_consumption = avg_daily * 30
        
        # Simple rate calculation (customize based on your billing rates)
        if monthly_consumption <= 20:
            rate = Decimal('0.50')
        elif monthly_consumption <= 50:
            rate = Decimal('0.75')
        elif monthly_consumption <= 100:
            rate = Decimal('1.00')
        else:
            rate = Decimal('1.50')
        
        amount = monthly_consumption * rate + Decimal('5.00')
        amount = amount * Decimal('1.16')  # Add VAT
        return amount.quantize(Decimal('0.01'))


class MeterReading(models.Model):
    meter = models.ForeignKey(SmartMeter, on_delete=models.CASCADE, related_name='readings')
    reading_value = models.DecimalField(max_digits=10, decimal_places=3)
    consumption = models.DecimalField(max_digits=10, decimal_places=3)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'meter_readings'
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"Reading {self.reading_value} - {self.meter.meter_id} - {self.timestamp.date()}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate consumption if not provided
        if not self.consumption and self.pk is None:
            last_reading = MeterReading.objects.filter(
                meter=self.meter
            ).order_by('-timestamp').first()
            
            if last_reading:
                self.consumption = self.reading_value - last_reading.reading_value
                if self.consumption < 0:
                    self.consumption = 0
            else:
                self.consumption = 0
        
        super().save(*args, **kwargs)
    
    @property
    def is_high_consumption(self):
        """Check if this reading shows unusually high consumption"""
        avg = self.meter.get_average_daily_consumption()
        return self.consumption > avg * 2 if avg > 0 else False