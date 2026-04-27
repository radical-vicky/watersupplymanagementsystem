from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import uuid
from .models import Payment
from billing.models import Bill
from notifications.models import Notification
from .mpesa import MpesaClient

@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    total_paid = payments.filter(status='completed').aggregate(total=models.Sum('amount'))['total'] or 0
    pending_count = payments.filter(status='pending').count()
    
    context = {
        'payments': payments,
        'total_paid': total_paid,
        'pending_count': pending_count,
    }
    return render(request, 'payments/history.html', context)

@login_required
def initiate_payment(request, bill_number):
    bill = get_object_or_404(Bill, bill_number=bill_number, user=request.user)
    
    if bill.status == 'paid':
        messages.warning(request, 'This bill has already been paid.')
        return redirect('billing:detail', bill_number=bill_number)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        phone_number = request.POST.get('phone_number')
        
        transaction_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            bill=bill,
            user=request.user,
            amount=bill.total_amount,
            payment_method=payment_method,
            status='pending',
            phone_number=phone_number,
        )
        
        if payment_method == 'mpesa' and phone_number:
            mpesa = MpesaClient()
            result = mpesa.stk_push(
                phone_number=phone_number,
                amount=bill.total_amount,
                account_reference=bill.bill_number,
                transaction_desc='Water Bill Payment'
            )
            
            if 'error' in result:
                payment.status = 'failed'
                payment.save()
                messages.error(request, f'M-Pesa error: {result["error"]}')
                return redirect('payments:history')
            else:
                checkout_request_id = result.get('CheckoutRequestID', '')
                payment.mpesa_receipt_number = checkout_request_id
                payment.save()
                
                Notification.objects.create(
                    user=request.user,
                    type='payment',
                    title='Payment Initiated',
                    message=f'Payment of KES {bill.total_amount} for bill {bill.bill_number} has been initiated.',
                    is_read=False
                )
                
                messages.info(request, f'STK push sent to {phone_number}')
                return render(request, 'payments/pending.html', {
                    'payment': payment,
                    'phone_number': phone_number,
                    'checkout_request_id': checkout_request_id
                })
        else:
            payment.status = 'completed'
            payment.completion_date = timezone.now()
            payment.save()
            
            bill.status = 'paid'
            bill.paid_date = timezone.now()
            bill.save()
            
            messages.success(request, f'Payment of KES {bill.total_amount} completed successfully!')
            return redirect('payments:receipt', transaction_id=transaction_id)
    
    context = {
        'bill': bill,
        'today': timezone.now().date(),
    }
    return render(request, 'payments/initiate.html', context)

@login_required
def payment_status(request, transaction_id):
    """Check payment status from M-Pesa"""
    payment = get_object_or_404(Payment, transaction_id=transaction_id, user=request.user)
    
    if payment.status in ['completed', 'failed', 'cancelled']:
        return JsonResponse({
            'status': payment.status,
            'message': f'Payment already {payment.status}'
        })
    
    if payment.payment_method != 'mpesa':
        return JsonResponse({
            'status': payment.status,
            'message': f'Payment status: {payment.status}'
        })
    
    mpesa = MpesaClient()
    result = mpesa.query_status(payment.mpesa_receipt_number)
    
    if 'error' in result:
        return JsonResponse({
            'status': 'error',
            'message': result['error']
        })
    
    result_code = result.get('ResultCode')
    result_desc = result.get('ResultDesc', '')
    
    if result_code == '0':
        payment.status = 'completed'
        payment.completion_date = timezone.now()
        payment.save()
        
        bill = payment.bill
        bill.status = 'paid'
        bill.paid_date = timezone.now()
        bill.save()
        
        Notification.objects.create(
            user=request.user,
            type='payment',
            title='Payment Successful',
            message=f'Payment of KES {payment.amount} completed successfully.',
            is_read=False
        )
        
        return JsonResponse({
            'status': 'completed',
            'message': 'Payment completed successfully!'
        })
    
    elif result_code == '1037':
        payment.status = 'cancelled'
        payment.save()
        
        Notification.objects.create(
            user=request.user,
            type='payment',
            title='Payment Cancelled',
            message=f'You cancelled the payment on your phone.',
            is_read=False
        )
        
        return JsonResponse({
            'status': 'cancelled',
            'message': 'You cancelled the payment.'
        })
    
    elif result_code == '1032':
        payment.status = 'failed'
        payment.save()
        
        Notification.objects.create(
            user=request.user,
            type='payment',
            title='Payment Failed',
            message=f'Payment failed due to insufficient funds.',
            is_read=False
        )
        
        return JsonResponse({
            'status': 'failed',
            'message': 'Insufficient funds. Please top up and try again.'
        })
    
    else:
        return JsonResponse({
            'status': 'pending',
            'message': 'Waiting for your input...',
            'result_code': result_code
        })


@login_required
@require_POST
def cancel_payment(request, transaction_id):
    """Manually cancel a pending payment from the site"""
    try:
        payment = get_object_or_404(Payment, transaction_id=transaction_id, user=request.user)
        
        # Only allow cancellation if payment is pending
        if payment.status != 'pending':
            return JsonResponse({
                'success': False, 
                'error': 'Cannot cancel payment that is already processed'
            }, status=400)
        
        # Cancel the payment
        payment.status = 'cancelled'
        payment.save()
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            type='payment',
            title='Payment Cancelled',
            message=f'You cancelled the payment of KES {payment.amount} from the website.',
            is_read=False
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Payment cancelled successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def payment_receipt(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id, user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/receipt.html', context)


@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa payment callback"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode', 1)
            result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc', '')
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID', '')
            
            payment = Payment.objects.filter(mpesa_receipt_number=checkout_request_id).first()
            
            if not payment:
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment not found'})
            
            if result_code == 0:
                payment.status = 'completed'
                payment.completion_date = timezone.now()
                payment.save()
                
                bill = payment.bill
                bill.status = 'paid'
                bill.paid_date = timezone.now()
                bill.save()
                
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            
            elif result_code == 1037:
                payment.status = 'cancelled'
                payment.save()
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Cancelled'})
            
            elif result_code == 1032:
                payment.status = 'failed'
                payment.save()
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Insufficient funds'})
            
            else:
                payment.status = 'failed'
                payment.save()
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Failed'})
                
        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request method'})