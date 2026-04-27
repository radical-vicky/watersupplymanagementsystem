from django.contrib import admin
from django.utils.html import format_html
from .models import SmartMeter, MeterReading

class MeterReadingInline(admin.TabularInline):
    model = MeterReading
    extra = 0
    fields = ['reading_value', 'consumption', 'timestamp', 'is_synced']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

@admin.register(SmartMeter)
class SmartMeterAdmin(admin.ModelAdmin):
    list_display = ['meter_id', 'user', 'location', 'status', 'last_reading', 'last_reading_date', 'battery_level', 'signal_strength', 'is_online_indicator']
    list_filter = ['status', 'installation_date', 'battery_level']
    search_fields = ['meter_id', 'user__username', 'user__email', 'location']
    readonly_fields = ['installation_date', 'last_reading_date']
    inlines = [MeterReadingInline]
    
    fieldsets = (
        ('Meter Information', {
            'fields': ('meter_id', 'user', 'location', 'status')
        }),
        ('Readings', {
            'fields': ('last_reading', 'last_reading_date')
        }),
        ('Technical Details', {
            'fields': ('firmware_version', 'battery_level', 'signal_strength'),
            'classes': ('collapse',)
        }),
    )
    
    def is_online_indicator(self, obj):
        if obj.is_online():
            return "✓ Online"
        else:
            return "✗ Offline"
    is_online_indicator.short_description = 'Status'
    is_online_indicator.allow_tags = True
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_maintenance']
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Mark selected meters as Active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(status='inactive')
    mark_as_inactive.short_description = "Mark selected meters as Inactive"
    
    def mark_as_maintenance(self, request, queryset):
        queryset.update(status='maintenance')
    mark_as_maintenance.short_description = "Mark selected meters as Under Maintenance"

@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ['meter', 'reading_value', 'consumption', 'timestamp', 'is_synced', 'high_consumption_indicator']
    list_filter = ['timestamp', 'is_synced', 'meter__status']
    search_fields = ['meter__meter_id', 'meter__user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def high_consumption_indicator(self, obj):
        if obj.is_high_consumption:
            return "⚠ High"
        return "✓ Normal"
    high_consumption_indicator.short_description = 'Usage Level'
    high_consumption_indicator.allow_tags = True