from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SmartMeter

@login_required
def meter_list(request):
    meters = SmartMeter.objects.filter(user=request.user)
    context = {
        'meters': meters,
        'total_meters': meters.count(),
    }
    return render(request, 'meters/list.html', context)

@login_required
def meter_detail(request, meter_id):
    meter = get_object_or_404(SmartMeter, meter_id=meter_id, user=request.user)
    readings = meter.readings.all().order_by('-timestamp')[:50]
    context = {
        'meter': meter,
        'readings': readings,
    }
    return render(request, 'meters/detail.html', context)