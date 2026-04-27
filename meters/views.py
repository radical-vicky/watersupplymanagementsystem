from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from .models import SmartMeter, MeterReading

@login_required
def meter_list(request):
    meters = SmartMeter.objects.filter(user=request.user)
    
    # Calculate statistics
    total_meters = meters.count()
    
    context = {
        'meters': meters,
        'total_meters': total_meters,
    }
    return render(request, 'meters/list.html', context)



@login_required
def meter_detail(request, meter_id):
    meter = get_object_or_404(SmartMeter, meter_id=meter_id, user=request.user)
    
    # Get paginated readings
    readings_list = meter.readings.all().order_by('-timestamp')
    paginator = Paginator(readings_list, 20)
    page_number = request.GET.get('page')
    readings = paginator.get_page(page_number)
    
    # Calculate statistics
    total_consumption = meter.get_total_consumption(30)
    avg_daily = meter.get_average_daily_consumption()
    estimated_bill = meter.estimated_monthly_bill
    
    # Get last 7 days for chart
    last_7_days = []
    for i in range(6, -1, -1):
        day = timezone.now() - timezone.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        daily_readings = MeterReading.objects.filter(
            meter=meter,
            timestamp__range=[day_start, day_end]
        )
        
        if daily_readings.exists():
            daily_consumption = daily_readings.aggregate(Sum('consumption'))['consumption__sum'] or 0
        else:
            daily_consumption = 0
        
        last_7_days.append({
            'date': day.strftime('%a, %b %d'),
            'consumption': float(daily_consumption),
            'full_date': day.strftime('%Y-%m-%d')
        })
    
    # Get last 12 months for monthly chart
    last_12_months = []
    for i in range(11, -1, -1):
        month = timezone.now() - timezone.timedelta(days=30*i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            next_month = month.replace(year=month.year+1, month=1, day=1)
        else:
            next_month = month.replace(month=month.month+1, day=1)
        
        monthly_readings = MeterReading.objects.filter(
            meter=meter,
            timestamp__gte=month_start,
            timestamp__lt=next_month
        )
        
        monthly_consumption = monthly_readings.aggregate(Sum('consumption'))['consumption__sum'] or 0
        
        last_12_months.append({
            'month': month.strftime('%b %Y'),
            'consumption': float(monthly_consumption)
        })
    
    # Get recent alerts - FIXED: changed created_at to reported_at
    recent_alerts = []
    try:
        from leaks.models import LeakReport
        recent_alerts = LeakReport.objects.filter(
            meter=meter, 
            status='detected'
        ).order_by('-reported_at')[:5]  # Changed from -created_at to -reported_at
    except ImportError:
        pass
    
    context = {
        'meter': meter,
        'readings': readings,
        'total_consumption': total_consumption,
        'avg_daily_consumption': avg_daily,
        'estimated_bill': estimated_bill,
        'last_7_days': last_7_days,
        'last_12_months': last_12_months,
        'is_online': meter.is_online(),
        'recent_alerts': recent_alerts,
    }
    return render(request, 'meters/detail.html', context)

@login_required
def meter_reading_chart(request, meter_id):
    """AJAX endpoint for meter reading chart data"""
    meter = get_object_or_404(SmartMeter, meter_id=meter_id, user=request.user)
    days = int(request.GET.get('days', 30))
    
    readings = MeterReading.objects.filter(
        meter=meter,
        timestamp__gte=timezone.now() - timezone.timedelta(days=days)
    ).order_by('timestamp')
    
    data = {
        'labels': [r.timestamp.strftime('%Y-%m-%d') for r in readings],
        'readings': [float(r.reading_value) for r in readings],
        'consumption': [float(r.consumption) for r in readings],
    }
    
    return JsonResponse(data)

@login_required
def add_reading(request, meter_id):
    """Manually add a meter reading"""
    if request.method == 'POST':
        meter = get_object_or_404(SmartMeter, meter_id=meter_id, user=request.user)
        
        try:
            reading_value = Decimal(request.POST.get('reading_value'))
            consumption = meter.update_reading(reading_value)
            
            messages.success(request, f'Reading added successfully! Consumption: {consumption:.3f} m³')
            return JsonResponse({'success': True, 'consumption': float(consumption)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)