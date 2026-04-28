from .models import UserProfile, Notification

def user_profile(request):
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user, defaults={'role': 'customer', 'avatar_color': '#6366f1'})
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'user_profile': profile, 'unread_notif_count': unread_count}
    return {'user_profile': None, 'unread_notif_count': 0}
