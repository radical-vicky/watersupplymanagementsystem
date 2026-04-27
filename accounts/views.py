from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models  # ADD THIS IMPORT
from meters.models import SmartMeter
from payments.models import Payment
from leaks.models import LeakReport
from notifications.models import Notification

@login_required
def profile(request):
    user = request.user
    
    # Get user statistics
    total_meters = SmartMeter.objects.filter(user=user).count()
    total_payments = Payment.objects.filter(user=user, status='completed').count()
    total_amount_paid = Payment.objects.filter(user=user, status='completed').aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Recent activities
    recent_activities = []
    
    # Add recent payments
    recent_payments = Payment.objects.filter(user=user, status='completed').order_by('-payment_date')[:3]
    for payment in recent_payments:
        recent_activities.append({
            'type': 'Payment',
            'description': f'Paid KES {payment.amount:,.0f} for bill {payment.bill.bill_number}',
            'date': payment.payment_date
        })
    
    # Add recent leak reports
    recent_leaks = LeakReport.objects.filter(user=user).order_by('-reported_at')[:3]
    for leak in recent_leaks:
        recent_activities.append({
            'type': 'Leak Report' if leak.type == 'reported' else 'System Alert',
            'description': f'Leak reported at {leak.location}',
            'date': leak.reported_at
        })
    
    # Add recent notifications
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:3]
    for notification in recent_notifications:
        recent_activities.append({
            'type': 'Notification',
            'description': notification.title,
            'date': notification.created_at
        })
    
    # Sort by date (newest first)
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
    
    context = {
        'total_meters': total_meters,
        'total_payments': total_payments,
        'total_amount_paid': total_amount_paid,
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', user.email)
        user.address = request.POST.get('address', '')
        
        # Handle phone number
        phone = request.POST.get('phone_number', '')
        if phone:
            user.phone_number = phone
        
        # Handle profile picture
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html')