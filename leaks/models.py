from django.db import models
from django.conf import settings

class LeakReport(models.Model):
    TYPE_CHOICES = (
        ('reported', 'User Reported'),
        ('detected', 'System Detected'),
        ('potential', 'Potential Leak'),
    )
    
    STATUS_CHOICES = (
        ('detected', 'Detected'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'Under Repair'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    )
    
    report_id = models.CharField(max_length=50, unique=True)
    meter = models.ForeignKey('meters.SmartMeter', on_delete=models.CASCADE, related_name='leak_reports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leak_reports')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='leaks/', null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_leaks'
    )
    estimated_water_loss = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    
    class Meta:
        db_table = 'leak_reports'
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"Leak {self.report_id} - {self.meter.meter_id}"