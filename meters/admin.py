from django.contrib import admin
from .models import SmartMeter, MeterReading

@admin.register(SmartMeter)
class SmartMeterAdmin(admin.ModelAdmin):
    list_display = ('meter_id', 'user', 'location', 'status', 'last_reading', 'battery_level')
    list_filter = ('status', 'installation_date')
    search_fields = ('meter_id', 'user__username', 'location')

@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ('meter', 'reading_value', 'consumption', 'timestamp')
    list_filter = ('timestamp',)