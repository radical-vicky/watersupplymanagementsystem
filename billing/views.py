from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models  # ADD THIS IMPORT
from django.utils import timezone
from .models import Bill
from payments.models import Payment

@login_required
def bill_list(request):
    bills = Bill.objects.filter(user=request.user).order_by('-billing_month')
    pending_count = bills.filter(status='pending').count()
    paid_count = bills.filter(status='paid').count()
    total_due = bills.filter(status='pending').aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    context = {
        'bills': bills,
        'pending_count': pending_count,
        'paid_count': paid_count,
        'total_due': total_due,
        'today': timezone.now().date(),
    }
    return render(request, 'billing/list.html', context)

@login_required
def bill_detail(request, bill_number):
    bill = get_object_or_404(Bill, bill_number=bill_number, user=request.user)
    payments = Payment.objects.filter(bill=bill)
    
    context = {
        'bill': bill,
        'payments': payments,
        'today': timezone.now().date(),
    }
    return render(request, 'billing/detail.html', context)