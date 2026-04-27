from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    ROLE_CHOICES = (
        ('consumer', 'Consumer'),
        ('admin', 'Administrator'),
        ('technician', 'Technician'),
        ('billing_officer', 'Billing Officer'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consumer')
    phone_number = PhoneNumberField(unique=True, null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"