from django.urls import path
from . import views

urlpatterns = [
    path('register/',                   views.register_view,           name='register'),
    path('dashboard/',                  views.dashboard,               name='dashboard'),
    path('complaints/',                 views.complaint_list,          name='complaint_list'),
    path('complaints/raise/',           views.raise_complaint,         name='raise_complaint'),
    path('complaints/<int:pk>/',        views.complaint_detail,        name='complaint_detail'),
    path('notifications/read/',         views.mark_notifications_read, name='mark_notifs_read'),
    path('analytics/',                  views.analytics,               name='analytics'),
    path('profile/',                    views.profile_view,            name='profile'),
    path('leaderboard/',                views.leaderboard_view,        name='leaderboard'),
]
