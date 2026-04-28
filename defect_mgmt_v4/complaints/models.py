from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


ROLE_CHOICES = [
    ('customer',        'Customer'),
    ('developer',       'Developer'),
    ('designer',        'Designer'),
    ('tester',          'Tester'),
    ('qa_engineer',     'QA Engineer'),
    ('product_manager', 'Product Manager'),
    ('support',         'Support Agent'),
    ('admin',           'Admin'),
]

ROLE_COLORS = {
    'customer':        '#6b7280',
    'developer':       '#6366f1',
    'designer':        '#ec4899',
    'tester':          '#f59e0b',
    'qa_engineer':     '#ef4444',
    'product_manager': '#8b5cf6',
    'support':         '#10b981',
    'admin':           '#f97316',
}


class UserProfile(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone        = models.CharField(max_length=15, blank=True)
    department   = models.CharField(max_length=100, blank=True)
    avatar_color = models.CharField(max_length=7, default='#6366f1')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_staff_role(self):
        return self.role not in ('customer',)

    def is_admin(self):
        return self.role == 'admin'


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        color = ROLE_COLORS.get('customer', '#6366f1')
        UserProfile.objects.get_or_create(user=instance, defaults={'avatar_color': color})


class DefectCategory(models.Model):
    ASSIGNABLE_ROLES = [
        ('developer',       'Developer'),
        ('designer',        'Designer'),
        ('tester',          'Tester'),
        ('qa_engineer',     'QA Engineer'),
        ('product_manager', 'Product Manager'),
        ('support',         'Support Agent'),
    ]
    name           = models.CharField(max_length=100)
    description    = models.TextField(blank=True)
    suggested_role = models.CharField(max_length=20, choices=ASSIGNABLE_ROLES, default='developer')
    color          = models.CharField(max_length=7, default='#6366f1')
    icon           = models.CharField(max_length=10, default='🔧')

    class Meta:
        verbose_name_plural = 'Defect Categories'

    def __str__(self):
        return self.name


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending',     'Pending Review'),
        ('assigned',    'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
        ('rejected',    'Rejected'),
    ]
    PRIORITY_CHOICES = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ]

    complaint_id    = models.CharField(max_length=20, unique=True, editable=False)
    title           = models.CharField(max_length=200)
    description     = models.TextField()
    product_name    = models.CharField(max_length=200)
    order_number    = models.CharField(max_length=100, blank=True)
    defect_category = models.ForeignKey(DefectCategory, on_delete=models.SET_NULL, null=True, blank=True)
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    raised_by       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_raised')
    assigned_to     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_assigned')
    image           = models.ImageField(upload_to='complaints/%Y/%m/', null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    resolved_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint_id} – {self.title}"

    def save(self, *args, **kwargs):
        if not self.complaint_id:
            import random
            self.complaint_id = f"DEF-{timezone.now().strftime('%y%m')}-{random.randint(1000, 9999)}"
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class ComplaintUpdate(models.Model):
    complaint  = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    message    = models.TextField()
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Update on {self.complaint.complaint_id}"


class Notification(models.Model):
    """Real-time notifications so users see when their complaint is updated."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    complaint  = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='notifications')
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif → {self.user.username}: {self.message[:50]}"


REWARD_AMOUNT = 5000  # ₹5,000 per resolved defect


class Reward(models.Model):
    """Tracks ₹5,000 rewards earned by staff for resolving defects."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards')
    complaint  = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='rewards')
    amount     = models.PositiveIntegerField(default=REWARD_AMOUNT)
    awarded_at = models.DateTimeField(auto_now_add=True)
    # Shown as a congrats popup once, then dismissed
    is_seen    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-awarded_at']
        # One reward per complaint per user (prevent duplicate)
        unique_together = [('user', 'complaint')]

    def __str__(self):
        return f"₹{self.amount} → {self.user.username} for {self.complaint.complaint_id}"
