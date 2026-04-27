from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import WaterSchedule

def is_admin(user):
    return user.role == 'admin'

@login_required
def schedule_list(request):
    today = timezone.now().strftime('%A').lower()
    schedules = WaterSchedule.objects.all().order_by('day_of_week')
    today_schedule = WaterSchedule.objects.filter(day_of_week=today, is_active=True).first()
    
    context = {
        'schedules': schedules,
        'today_schedule': today_schedule,
        'today': today,
    }
    return render(request, 'schedules/list.html', context)

@login_required
def schedule_detail(request, schedule_id):
    """View schedule details"""
    schedule = get_object_or_404(WaterSchedule, id=schedule_id)
    
    context = {
        'schedule': schedule,
    }
    return render(request, 'schedules/detail.html', context)

@user_passes_test(is_admin)
def schedule_create(request):
    if request.method == 'POST':
        schedule = WaterSchedule.objects.create(
            area_name=request.POST.get('area_name'),
            zone_code=request.POST.get('zone_code'),
            day_of_week=request.POST.get('day_of_week'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, f'Schedule for {schedule.area_name} created successfully!')
        return redirect('schedules:list')
    
    return render(request, 'schedules/create.html')

@user_passes_test(is_admin)
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(WaterSchedule, id=schedule_id)
    
    if request.method == 'POST':
        schedule.area_name = request.POST.get('area_name')
        schedule.zone_code = request.POST.get('zone_code')
        schedule.day_of_week = request.POST.get('day_of_week')
        schedule.start_time = request.POST.get('start_time')
        schedule.end_time = request.POST.get('end_time')
        schedule.notes = request.POST.get('notes', '')
        schedule.save()
        messages.success(request, f'Schedule for {schedule.area_name} updated successfully!')
        return redirect('schedules:list')
    
    context = {'schedule': schedule}
    return render(request, 'schedules/edit.html', context)

@user_passes_test(is_admin)
def schedule_toggle(request, schedule_id):
    schedule = get_object_or_404(WaterSchedule, id=schedule_id)
    schedule.is_active = not schedule.is_active
    schedule.save()
    status = "activated" if schedule.is_active else "deactivated"
    messages.success(request, f'Schedule for {schedule.area_name} {status} successfully!')
    return redirect('schedules:list')