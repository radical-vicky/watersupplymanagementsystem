from django.db import models
from django.conf import settings
from django.utils import timezone

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
    
    def __str__(self):
        return f"Meter {self.meter_id} - {self.user.username}"
    
    def update_reading(self, reading_value):
        previous_reading = self.last_reading
        consumption = reading_value - previous_reading
        
        MeterReading.objects.create(
            meter=self,
            reading_value=reading_value,
            consumption=consumption,
            timestamp=timezone.now()
        )
        
        self.last_reading = reading_value
        self.last_reading_date = timezone.now()
        self.save()
        
        # Check for potential leak
        if consumption > self.get_average_daily_consumption() * 2:
            from leaks.models import LeakReport
            LeakReport.objects.create(
                meter=self,
                user=self.user,
                type='detected',
                status='detected',
                description=f"Unusual consumption detected: {consumption} units"
            )
        
        return consumption
    
    def get_average_daily_consumption(self):
        last_7_days = MeterReading.objects.filter(
            meter=self,
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        )
        if last_7_days.exists():
            return last_7_days.aggregate(models.Avg('consumption'))['consumption__avg'] or 0
        return 0

class MeterReading(models.Model):
    meter = models.ForeignKey(SmartMeter, on_delete=models.CASCADE, related_name='readings')
    reading_value = models.DecimalField(max_digits=10, decimal_places=3)
    consumption = models.DecimalField(max_digits=10, decimal_places=3)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'meter_readings'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Reading {self.reading_value} - {self.meter.meter_id}"