from django.contrib import admin
from .models import Tariff, Bill

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate_per_unit', 'fixed_charge', 'is_active', 'effective_from')
    list_filter = ('is_active',)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'user', 'billing_month', 'total_amount', 'status', 'due_date')
    list_filter = ('status', 'billing_month')
    search_fields = ('bill_number', 'user__username')