from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('', views.schedule_list, name='list'),
    path('<int:schedule_id>/', views.schedule_detail, name='detail'),  # Add this
    path('create/', views.schedule_create, name='create'),
    path('<int:schedule_id>/edit/', views.schedule_edit, name='edit'),
    path('<int:schedule_id>/toggle/', views.schedule_toggle, name='toggle'),
]