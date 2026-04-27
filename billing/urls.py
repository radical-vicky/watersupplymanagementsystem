from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.bill_list, name='list'),
    path('<str:bill_number>/', views.bill_detail, name='detail'),
]