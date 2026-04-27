from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_history, name='history'),
    path('initiate/<str:bill_number>/', views.initiate_payment, name='initiate'),
    path('receipt/<str:transaction_id>/', views.payment_receipt, name='receipt'),
    path('status/<str:transaction_id>/', views.payment_status, name='status'),
    path('cancel/<str:transaction_id>/', views.cancel_payment, name='cancel'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]