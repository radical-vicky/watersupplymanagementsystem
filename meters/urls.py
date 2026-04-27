from django.urls import path
from . import views

app_name = 'meters'

urlpatterns = [
    path('', views.meter_list, name='list'),
    path('<str:meter_id>/', views.meter_detail, name='detail'),
    path('<str:meter_id>/chart/', views.meter_reading_chart, name='chart'),
    path('<str:meter_id>/add-reading/', views.add_reading, name='add_reading'),
]