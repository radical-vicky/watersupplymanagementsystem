from django.urls import path
from . import views

app_name = 'meters'

urlpatterns = [
    path('', views.meter_list, name='list'),
    path('<str:meter_id>/', views.meter_detail, name='detail'),
]