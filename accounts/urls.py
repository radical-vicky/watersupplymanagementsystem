from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),  # This will be at /profile/
    path('edit/', views.edit_profile, name='edit_profile'),
]