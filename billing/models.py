from django.db import models
from django.conf import settings
from django.utils import timezone

class Tariff(models.Model):
    name = models.CharField(max_length=100)
    min_consumption = models.DecimalField(max_digits=10, decimal_places=3)
    max_consumption = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    fixed_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'tariffs'
    
    def __str__(self):
        return f"{self.name} - KES {self.rate_per_unit}/unit"

class Bill(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
    )
    
    bill_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bills')
    meter = models.ForeignKey('meters.SmartMeter', on_delete=models.CASCADE)
    billing_month = models.DateField()
    consumption = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tariff_rate = models.DecimalField(max_digits=10, decimal_places=2)
    fixed_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    issued_date = models.DateTimeField(auto_now_add=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bills'
        ordering = ['-billing_month']
    
    def __str__(self):
        return f"Bill {self.bill_number} - {self.user.username} - KES {self.total_amount}"
    
    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_date = timezone.now()
        self.save()