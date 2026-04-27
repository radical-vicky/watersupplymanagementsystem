from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from meters.models import SmartMeter, MeterReading
from billing.models import Bill
from payments.models import Payment
from leaks.models import LeakReport
from .forms import ContactForm
from .models import ContactMessage

def landing_page(request):
    """Landing page with dynamic data from database"""
    context = {}
    
    # Get total users count
    total_users = User.objects.filter(is_active=True).count()
    context['total_users'] = f"{total_users:,}" if total_users > 0 else "1,000+"
    
    # Get total active meters
    total_active_meters = SmartMeter.objects.filter(status='active').count()
    context['total_active_meters'] = f"{total_active_meters//1000}K" if total_active_meters >= 1000 else str(total_active_meters)
    
    # Calculate total water saved (simulated from meter readings)
    last_month = timezone.now() - timedelta(days=30)
    total_readings = MeterReading.objects.filter(timestamp__gte=last_month)
    
    # FIX: Convert Decimal to float before multiplication
    total_water_used = total_readings.aggregate(total=Sum('consumption'))['total'] or 0
    
    # Convert Decimal to float if needed
    if hasattr(total_water_used, 'total'):
        total_water_used = float(total_water_used)
    else:
        total_water_used = float(total_water_used) if total_water_used else 0
    
    # Assume 30% savings compared to traditional systems
    water_saved = int(total_water_used * 0.3)
    
    # Format water saved for display
    if water_saved >= 1000000:
        context['total_water_saved'] = f"{water_saved//1000000}M"
    elif water_saved >= 1000:
        context['total_water_saved'] = f"{water_saved//1000}K"
    else:
        context['total_water_saved'] = f"{water_saved}"
    
    # Statistics
    context['water_savings_percentage'] = 30
    context['leak_detection_rate'] = 95
    context['satisfaction_rate'] = 98
    
    # Contact info
    context['contact_phone'] = "+254 725 345 345"
    context['contact_email'] = "hello@aquaflow.co.ke"
    context['contact_location'] = "Nairobi, Kenya"
    context['footer_description'] = "Smart water supply management for modern Kenya."
    
    # Initialize contact form
    context['form'] = ContactForm()
    
    return render(request, 'landing.html', context)

def contact_submit(request):
    """
    Handle contact form submission
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            
            # Add success message
            messages.success(
                request, 
                f'Thank you {contact.name}! Your message has been received. We will contact you within 24 hours.'
            )
            
            return redirect('pages:landing')
        else:
            # If form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            
            return redirect('pages:landing')
    
    return redirect('pages:landing')