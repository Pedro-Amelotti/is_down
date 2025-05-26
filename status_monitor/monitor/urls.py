from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('status/', views.status, name='status'),
    path('systems_list/', views.systems_list, name='systems_list'),  # nova rota
    path('system_status/', views.system_status, name='system_status'),  # nova rota
    path('glpi-assistencias/', views.glpi_assistencias, name='glpi_assistencias'),
]