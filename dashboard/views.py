from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from meters.models import SmartMeter, MeterReading
from billing.models import Bill
from payments.models import Payment
from leaks.models import LeakReport
from schedules.models import WaterSchedule
from notifications.models import Notification

@login_required
def dashboard_home(request):
    user = request.user
    
    # Get user's meters
    meters = SmartMeter.objects.filter(user=user)
    
    # Calculate total consumption
    total_consumption = 0
    for meter in meters:
        readings = meter.readings.all()
        if readings.exists():
            total_consumption += sum(float(r.consumption) for r in readings)
    
    # Monthly consumption (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_consumption = 0
    for meter in meters:
        monthly_readings = meter.readings.filter(timestamp__gte=thirty_days_ago)
        if monthly_readings.exists():
            monthly_consumption += sum(float(r.consumption) for r in monthly_readings)
    
    # Chart data (last 7 days)
    last_7_days = []
    consumption_data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        last_7_days.append(date.strftime('%a, %b %d'))
        
        day_readings = MeterReading.objects.filter(
            meter__in=meters,
            timestamp__date=date
        )
        day_consumption = sum(float(r.consumption) for r in day_readings)
        consumption_data.append(round(day_consumption, 2))
    
    # Recent meter readings
    recent_readings = MeterReading.objects.filter(
        meter__in=meters
    ).order_by('-timestamp')[:10]
    
    # Billing stats
    pending_bills = Bill.objects.filter(user=user, status='pending')
    total_due = pending_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    paid_bills = Bill.objects.filter(user=user, status='paid')
    total_paid = paid_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent bills
    recent_bills = Bill.objects.filter(user=user).order_by('-billing_month')[:10]
    
    # Recent payments
    recent_payments = Payment.objects.filter(user=user).order_by('-payment_date')[:10]
    
    # Leak stats
    active_leaks = LeakReport.objects.filter(user=user, status__in=['detected', 'confirmed', 'in_progress'])
    resolved_leaks = LeakReport.objects.filter(user=user, status='resolved')
    recent_leaks = LeakReport.objects.filter(user=user).order_by('-reported_at')[:10]
    
    # Notification stats
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Water schedule
    today = timezone.now().strftime('%A').lower()
    today_schedule = WaterSchedule.objects.filter(day_of_week=today, is_active=True).first()
    weekly_schedule = WaterSchedule.objects.filter(is_active=True).order_by('day_of_week')
    
    context = {
        # User info
        'username': user.get_full_name() or user.username,
        'user_email': user.email,
        'user_avatar': user.get_full_name()[:2].upper() if user.get_full_name() else user.username[:2].upper(),
        
        # Meter stats
        'total_meters': meters.count(),
        'total_consumption': round(total_consumption, 2),
        'monthly_consumption': round(monthly_consumption, 2),
        
        # Chart data
        'chart_labels': last_7_days,
        'chart_data': consumption_data,
        
        # Recent data
        'recent_readings': recent_readings,
        'recent_bills': recent_bills,
        'recent_payments': recent_payments,
        'recent_leaks': recent_leaks,
        'recent_notifications': recent_notifications,
        
        # Bill stats
        'pending_bills_count': pending_bills.count(),
        'total_due': total_due,
        'paid_bills_count': paid_bills.count(),
        'total_paid': total_paid,
        
        # Leak stats
        'active_leaks_count': active_leaks.count(),
        'resolved_leaks_count': resolved_leaks.count(),
        
        # Notification
        'unread_count': unread_count,
        
        # Schedule
        'today_schedule': today_schedule,
        'weekly_schedule': weekly_schedule,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard stats"""
    user = request.user
    
    meters = SmartMeter.objects.filter(user=user)
    
    # Calculate total consumption
    total_consumption = 0
    for meter in meters:
        readings = meter.readings.all()
        if readings.exists():
            total_consumption += sum(float(r.consumption) for r in readings)
    
    data = {
        'total_meters': meters.count(),
        'total_consumption': round(total_consumption, 2),
        'pending_bills': Bill.objects.filter(user=user, status='pending').count(),
        'total_due': float(Bill.objects.filter(user=user, status='pending').aggregate(total=Sum('total_amount'))['total'] or 0),
        'active_leaks': LeakReport.objects.filter(user=user, status__in=['detected', 'confirmed', 'in_progress']).count(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }
    return JsonResponse(data)