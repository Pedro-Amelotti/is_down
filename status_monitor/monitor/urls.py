from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('status/', views.status, name='status'),
    path('systems_list/', views.systems_list, name='systems_list'),  # nova rota
    path('system_status/', views.system_status, name='system_status'),  # nova rota
    path('dashboard_summary/', views.dashboard_summary, name='dashboard_summary'),
    # path('check_all_statuses/', views.check_all_statuses, name='check_all_statuses'),
]