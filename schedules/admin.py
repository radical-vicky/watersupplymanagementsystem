from django.contrib import admin
from .models import WaterSchedule, SupplyNotification

@admin.register(WaterSchedule)
class WaterScheduleAdmin(admin.ModelAdmin):
    list_display = ('area_name', 'zone_code', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active', 'area_name')
    search_fields = ('area_name', 'zone_code')

@admin.register(SupplyNotification)
class SupplyNotificationAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'notification_date', 'is_sent')
    list_filter = ('is_sent', 'notification_date')