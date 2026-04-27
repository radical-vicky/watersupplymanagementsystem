from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('contact/', views.contact_submit, name='contact_submit'),  # Add this
]