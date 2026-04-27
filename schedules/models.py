from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class WaterSchedule(models.Model):
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    area_name = models.CharField(max_length=100)
    zone_code = models.CharField(max_length=20)
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(24)])
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'water_schedules'
        ordering = ['area_name', 'day_of_week', 'start_time']
        unique_together = ['area_name', 'day_of_week']  # One schedule per area per day
    
    def __str__(self):
        return f"{self.area_name} - {self.get_day_of_week_display()} ({self.start_time} to {self.end_time})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration
        start = self.start_time
        end = self.end_time
        duration = (end.hour - start.hour) if end.hour >= start.hour else (24 - start.hour + end.hour)
        self.duration_hours = duration
        super().save(*args, **kwargs)

class SupplyNotification(models.Model):
    schedule = models.ForeignKey(WaterSchedule, on_delete=models.CASCADE, related_name='notifications')
    notification_date = models.DateField(auto_now_add=True)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'supply_notifications'