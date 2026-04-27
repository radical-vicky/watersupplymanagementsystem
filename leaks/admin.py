from django.contrib import admin
from .models import LeakReport

@admin.register(LeakReport)
class LeakReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'meter', 'type', 'status', 'reported_at')
    list_filter = ('type', 'status')
    search_fields = ('report_id', 'location')