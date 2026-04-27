from django.urls import path
from . import views

app_name = 'leaks'

urlpatterns = [
    path('', views.leak_list, name='list'),
    path('report/', views.report_leak, name='report'),
    path('<str:report_id>/', views.leak_detail, name='detail'),
    path('<str:report_id>/update/', views.update_leak_status, name='update'),
]