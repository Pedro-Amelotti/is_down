from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('systems_list/', views.systems_list, name='systems_list'),  
    path('system_status/', views.system_status, name='system_status'),  
]