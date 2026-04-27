from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.utils import timezone
import uuid
from .models import LeakReport
from meters.models import SmartMeter

@login_required
def leak_list(request):
    if request.user.role in ['admin', 'technician']:
        leaks = LeakReport.objects.all().order_by('-reported_at')
    else:
        leaks = LeakReport.objects.filter(user=request.user).order_by('-reported_at')
    
    total_reports = leaks.count()
    active_count = leaks.filter(status__in=['detected', 'confirmed']).count()
    in_progress_count = leaks.filter(status='in_progress').count()
    resolved_count = leaks.filter(status='resolved').count()
    
    context = {
        'leaks': leaks,
        'total_reports': total_reports,
        'active_count': active_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
    }
    return render(request, 'leaks/list.html', context)

@login_required
def report_leak(request):
    if request.method == 'POST':
        meter_id = request.POST.get('meter_id')
        description = request.POST.get('description')
        location = request.POST.get('location')
        image = request.FILES.get('image')
        
        meter = get_object_or_404(SmartMeter, meter_id=meter_id, user=request.user)
        report_id = f"LEAK{uuid.uuid4().hex[:8].upper()}"
        
        leak = LeakReport.objects.create(
            report_id=report_id,
            meter=meter,
            user=request.user,
            type='reported',
            description=description,
            location=location,
            image=image
        )
        
        messages.success(request, f'Leak reported successfully! Reference: {report_id}')
        return redirect('leaks:detail', report_id=report_id)
    
    meters = SmartMeter.objects.filter(user=request.user)
    context = {'meters': meters}
    return render(request, 'leaks/report.html', context)

@login_required
def leak_detail(request, report_id):
    leak = get_object_or_404(LeakReport, report_id=report_id)
    
    if request.user.role not in ['admin', 'technician'] and leak.user != request.user:
        messages.error(request, 'You do not have permission to view this leak report')
        return redirect('leaks:list')
    
    context = {'leak': leak}
    return render(request, 'leaks/detail.html', context)

@login_required
def update_leak_status(request, report_id):
    if request.user.role not in ['admin', 'technician']:
        messages.error(request, 'Only administrators and technicians can update leak status')
        return redirect('leaks:detail', report_id=report_id)
    
    leak = get_object_or_404(LeakReport, report_id=report_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        leak.status = new_status
        if new_status == 'resolved':
            leak.resolved_at = timezone.now()
        leak.save()
        messages.success(request, f'Leak status updated to {new_status}')
    
    return redirect('leaks:detail', report_id=report_id)