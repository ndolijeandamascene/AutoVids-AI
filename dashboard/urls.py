from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('content/', views.content_management, name='content'),
    path('videos/', views.video_library, name='videos'),
    path('accounts/', views.accounts_view, name='accounts'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('logs/', views.system_logs, name='logs'),
]
