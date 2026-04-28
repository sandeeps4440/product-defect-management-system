from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.contrib.auth.models import User

from .models import (Complaint, DefectCategory, ComplaintUpdate,
                     UserProfile, Notification, Reward, ROLE_COLORS, REWARD_AMOUNT)
from .forms  import ComplaintForm, ComplaintUpdateForm, RegisterForm, ProfileForm


# ── helpers ───────────────────────────────────────────────────────────────────

def _profile(user):
    p, _ = UserProfile.objects.get_or_create(
        user=user, defaults={'role': 'customer', 'avatar_color': '#6366f1'})
    return p


def _notify(user, complaint, message):
    """Create an in-app notification for a user."""
    Notification.objects.create(user=user, complaint=complaint, message=message)


# ── register ──────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user  = form.save()
            role  = form.cleaned_data.get('role', 'customer')
            p, _  = UserProfile.objects.get_or_create(user=user)
            p.role         = role
            p.avatar_color = ROLE_COLORS.get(role, '#6366f1')
            p.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Account created.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'complaints/register.html', {'form': form})


# ── mark notifications read ───────────────────────────────────────────────────

@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ── dashboard router ──────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    p = _profile(request.user)
    if   p.role == 'admin':    return _admin_dash(request, p)
    elif p.role == 'customer': return _customer_dash(request, p)
    else:                      return _staff_dash(request, p)


def _customer_dash(request, profile):
    qs = (Complaint.objects.filter(raised_by=request.user)
          .select_related('defect_category', 'assigned_to', 'assigned_to__profile'))
    stats = {
        'total':       qs.count(),
        'pending':     qs.filter(status='pending').count(),
        'in_progress': qs.filter(status__in=['assigned', 'in_progress']).count(),
        'resolved':    qs.filter(status='resolved').count(),
    }
    unread_notifs = request.user.notifications.filter(is_read=False)
    return render(request, 'complaints/dashboard_customer.html', {
        'profile': profile, 'stats': stats, 'recent': qs[:8],
        'unread_notifs': unread_notifs,
    })


def _admin_dash(request, profile):
    all_c = Complaint.objects.select_related('defect_category', 'raised_by', 'assigned_to__profile')
    pending = all_c.filter(status='pending').order_by('-created_at')
    stats = {
        'total':       all_c.count(),
        'pending':     pending.count(),
        'in_progress': all_c.filter(status__in=['assigned', 'in_progress']).count(),
        'resolved':    all_c.filter(status='resolved').count(),
        'critical':    all_c.filter(priority='critical').count(),
    }
    cat_stats = [{'cat': c, 'count': all_c.filter(defect_category=c).count()}
                 for c in DefectCategory.objects.all()]
    staff_load = (
        User.objects
        .filter(profile__role__in=['developer','designer','tester','qa_engineer','product_manager','support'])
        .select_related('profile')
        .annotate(open_count=Count('complaints_assigned',
            filter=Q(complaints_assigned__status__in=['assigned','in_progress'])))
        .order_by('-open_count')[:8]
    )
    # Leaderboard
    leaderboard = _get_leaderboard()
    total_rewards_paid = Reward.objects.aggregate(t=Sum('amount'))['t'] or 0

    return render(request, 'complaints/dashboard_admin.html', {
        'profile': profile, 'stats': stats,
        'pending_review':     pending[:10],
        'cat_stats':          cat_stats,
        'staff_load':         staff_load,
        'all_complaints':     all_c.order_by('-created_at')[:10],
        'leaderboard':        leaderboard,
        'total_rewards_paid': total_rewards_paid,
        'reward_amount':      REWARD_AMOUNT,
    })


def _staff_dash(request, profile):
    qs = (Complaint.objects.filter(assigned_to=request.user)
          .select_related('defect_category', 'raised_by', 'raised_by__profile'))
    stats = {
        'total':       qs.count(),
        'open':        qs.filter(status__in=['assigned', 'open']).count(),
        'in_progress': qs.filter(status='in_progress').count(),
        'resolved':    qs.filter(status='resolved').count(),
        'critical':    qs.filter(priority='critical').count(),
    }
    # Reward stats
    my_rewards   = Reward.objects.filter(user=request.user)
    total_earned = my_rewards.aggregate(total=Sum('amount'))['total'] or 0
    reward_count = my_rewards.count()
    new_rewards  = list(my_rewards.filter(is_seen=False).select_related('complaint'))
    # Mark all unseen as seen now (will show popup once)
    my_rewards.filter(is_seen=False).update(is_seen=True)
    return render(request, 'complaints/dashboard_staff.html', {
        'profile':             profile,
        'stats':               stats,
        'assigned_complaints': qs.order_by('-created_at')[:15],
        'role_label':          profile.get_role_display(),
        'total_earned':        total_earned,
        'reward_count':        reward_count,
        'new_rewards':         new_rewards,
        'reward_amount':       REWARD_AMOUNT,
    })


# ── raise complaint ───────────────────────────────────────────────────────────

@login_required
def raise_complaint(request):
    profile = _profile(request.user)
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            c           = form.save(commit=False)
            c.raised_by = request.user
            c.status    = 'pending'
            c.assigned_to     = None
            c.defect_category = None   # admin decides
            c.priority        = 'medium'  # admin will set actual priority
            c.save()
            ComplaintUpdate.objects.create(
                complaint=c, updated_by=request.user,
                message='Complaint submitted with photo evidence. Awaiting admin review.',
                new_status='pending',
            )
            messages.success(request,
                f'✅ Complaint {c.complaint_id} submitted! Admin will review and assign it.')
            return redirect('complaint_detail', pk=c.pk)
    else:
        form = ComplaintForm()
    return render(request, 'complaints/raise_complaint.html',
                  {'form': form, 'profile': profile})


# ── complaint list ────────────────────────────────────────────────────────────

@login_required
def complaint_list(request):
    profile = _profile(request.user)
    if   profile.role == 'admin':    qs = Complaint.objects.all()
    elif profile.role == 'customer': qs = Complaint.objects.filter(raised_by=request.user)
    else:                            qs = Complaint.objects.filter(assigned_to=request.user)

    qs = qs.select_related('defect_category', 'raised_by', 'assigned_to__profile')

    status   = request.GET.get('status',   '')
    priority = request.GET.get('priority', '')
    search   = request.GET.get('search',   '')
    if status:   qs = qs.filter(status=status)
    if priority: qs = qs.filter(priority=priority)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(complaint_id__icontains=search)
                       | Q(product_name__icontains=search))

    return render(request, 'complaints/complaint_list.html', {
        'complaints': qs, 'profile': profile,
        'categories': DefectCategory.objects.all(),
        'filters':    {'status': status, 'priority': priority, 'search': search},
    })


# ── complaint detail ──────────────────────────────────────────────────────────

@login_required
def complaint_detail(request, pk):
    c       = get_object_or_404(Complaint.objects.select_related(
        'defect_category', 'raised_by__profile', 'assigned_to__profile'), pk=pk)
    profile = _profile(request.user)

    if profile.role == 'customer' and c.raised_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('complaint_list')

    # Mark notifications for this complaint as read
    request.user.notifications.filter(complaint=c, is_read=False).update(is_read=True)

    # Filter staff by category's suggested role if category is set
    if c.defect_category:
        suggested = c.defect_category.suggested_role
        staff_users = (
            User.objects
            .filter(profile__role=suggested, is_active=True)
            .select_related('profile')
            .order_by('first_name', 'username')
        )
        all_staff = (
            User.objects
            .filter(profile__role__in=['developer','designer','tester','qa_engineer','product_manager','support'], is_active=True)
            .exclude(profile__role=suggested)
            .select_related('profile')
            .order_by('profile__role','first_name')
        )
    else:
        staff_users = (
            User.objects
            .filter(profile__role__in=['developer','designer','tester','qa_engineer','product_manager','support'], is_active=True)
            .select_related('profile')
            .order_by('profile__role', 'first_name')
        )
        all_staff = User.objects.none()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ── ADMIN ASSIGNS ─────────────────────────────────────────────────────
        if action == 'assign' and profile.is_admin():
            cat_id      = request.POST.get('defect_category', '')
            priority    = request.POST.get('priority', c.priority)
            assignee_id = request.POST.get('assigned_to', '')
            new_status  = request.POST.get('status', 'assigned')
            note        = request.POST.get('note', '').strip()

            if not assignee_id:
                messages.error(request, '⚠ Please select a staff member to assign this complaint.')
                return render(request, 'complaints/complaint_detail.html', {
                    'complaint': c, 'profile': profile,
                    'updates': c.updates.all(), 'staff_users': staff_users,
                    'all_staff': all_staff, 'categories': DefectCategory.objects.all(),
                    'assign_error': 'Please select a staff member.',
                })

            # Fetch objects
            try:
                assignee = User.objects.select_related('profile').get(pk=int(assignee_id))
            except (User.DoesNotExist, ValueError):
                messages.error(request, '⚠ Invalid staff member selected.')
                return redirect('complaint_detail', pk=pk)

            category = None
            if cat_id:
                try:
                    category = DefectCategory.objects.get(pk=int(cat_id))
                except (DefectCategory.DoesNotExist, ValueError):
                    pass

            old_status = c.status

            # Save complaint
            c.defect_category = category
            c.priority        = priority
            c.assigned_to     = assignee
            c.status          = new_status
            if new_status == 'resolved':
                c.resolved_at = timezone.now()
            c.save()

            assignee_name = assignee.get_full_name() or assignee.username
            assignee_role = assignee.profile.get_role_display()
            cat_name      = str(category) if category else 'Not categorised'

            log_msg = (
                f"Admin identified fault: {cat_name}. "
                f"Assigned to {assignee_name} ({assignee_role}). "
                f"Priority: {c.get_priority_display()}. "
                f"Status → {c.get_status_display()}."
            )
            if note:
                log_msg += f" Note: {note}"

            ComplaintUpdate.objects.create(
                complaint=c, updated_by=request.user,
                message=log_msg, old_status=old_status, new_status=c.status,
            )

            # Notify the customer
            _notify(c.raised_by, c,
                f"Your complaint '{c.title}' has been reviewed by Admin and assigned to "
                f"{assignee_name} ({assignee_role}). Fault identified: {cat_name}. "
                f"Status is now: {c.get_status_display()}.")

            # Notify the assignee (staff)
            _notify(assignee, c,
                f"Admin assigned complaint '{c.title}' (#{c.complaint_id}) to you. "
                f"Priority: {c.get_priority_display()}. Please review and start working on it.")

            messages.success(request,
                f'✅ Complaint assigned to {assignee_name} ({assignee_role}) successfully!')
            return redirect('complaint_detail', pk=pk)

        # ── STAFF STATUS UPDATE ───────────────────────────────────────────────
        elif action == 'update_status' and profile.is_staff_role():
            note_text  = request.POST.get('note_text', '').strip()
            new_status = request.POST.get('new_status', c.status)
            old_status = c.status

            if not note_text:
                messages.error(request, '⚠ Please add a note before updating status.')
                return redirect('complaint_detail', pk=pk)

            ComplaintUpdate.objects.create(
                complaint=c, updated_by=request.user,
                message=note_text, old_status=old_status, new_status=new_status,
            )
            c.status = new_status
            if new_status == 'resolved':
                c.resolved_at = timezone.now()
            c.save()

            # ── REWARD on resolve ─────────────────────────────────────────────
            reward_given = False
            if new_status == 'resolved' and c.assigned_to:
                reward, created = Reward.objects.get_or_create(
                    user=c.assigned_to, complaint=c,
                    defaults={'amount': REWARD_AMOUNT, 'is_seen': False},
                )
                if created:
                    reward_given = True
                    _notify(c.assigned_to, c,
                        f"🎉 Congratulations! You earned ₹{REWARD_AMOUNT:,} reward for resolving '{c.title}'.")

            # Notify customer of the update
            worker_name = request.user.get_full_name() or request.user.username
            worker_role = profile.get_role_display()
            _notify(c.raised_by, c,
                f"Update on your complaint '{c.title}': "
                f"{worker_name} ({worker_role}) changed status to {c.get_status_display()}. "
                f"Note: {note_text}")

            if reward_given:
                messages.success(request,
                    f'✅ Status updated to Resolved. 🎉 ₹{REWARD_AMOUNT:,} reward awarded to {worker_name}!')
            else:
                messages.success(request, f'✅ Status updated to: {c.get_status_display()}')
            return redirect('complaint_detail', pk=pk)

        # ── CUSTOMER COMMENT ──────────────────────────────────────────────────
        elif action == 'comment':
            msg = request.POST.get('comment_text', '').strip()
            if msg:
                ComplaintUpdate.objects.create(
                    complaint=c, updated_by=request.user, message=msg,
                )
                # Notify assigned staff if exists
                if c.assigned_to:
                    _notify(c.assigned_to, c,
                        f"Customer '{request.user.get_full_name() or request.user.username}' "
                        f"added a comment on complaint '{c.title}': {msg[:80]}")
                messages.success(request, 'Comment added.')
            else:
                messages.error(request, 'Comment cannot be empty.')
            return redirect('complaint_detail', pk=pk)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint':   c,
        'profile':     profile,
        'updates':     c.updates.all(),
        'staff_users': staff_users,
        'all_staff':   all_staff,
        'categories':  DefectCategory.objects.all(),
    })


# ── leaderboard helper & views ───────────────────────────────────────────────

def _get_leaderboard():
    return (
        User.objects
        .filter(rewards__isnull=False)
        .select_related('profile')
        .annotate(
            resolved_count=Count('rewards__complaint', distinct=True),
            total_earned=Sum('rewards__amount'),
        )
        .order_by('-resolved_count', '-total_earned')[:20]
    )


@login_required
def leaderboard_view(request):
    profile    = _profile(request.user)
    board      = _get_leaderboard()
    my_rewards = Reward.objects.filter(user=request.user)
    my_count   = my_rewards.count()
    my_earned  = my_rewards.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'complaints/leaderboard.html', {
        'profile':       profile,
        'board':         board,
        'my_count':      my_count,
        'my_earned':     my_earned,
        'reward_amount': REWARD_AMOUNT,
    })


# ── analytics ─────────────────────────────────────────────────────────────────

@login_required
def analytics(request):
    profile = _profile(request.user)
    qs = (Complaint.objects.filter(raised_by=request.user)
          if profile.role == 'customer' else Complaint.objects.all())
    total         = qs.count()
    status_data   = {s[0]: qs.filter(status=s[0]).count()   for s in Complaint.STATUS_CHOICES}
    priority_data = {p[0]: qs.filter(priority=p[0]).count() for p in Complaint.PRIORITY_CHOICES}
    cat_data      = [{'cat': cat, 'count': qs.filter(defect_category=cat).count()}
                     for cat in DefectCategory.objects.all()]
    assignee_data = (
        User.objects.filter(complaints_assigned__in=qs)
        .select_related('profile')
        .annotate(cnt=Count('complaints_assigned'))
        .order_by('-cnt')[:10]
    )
    return render(request, 'complaints/analytics.html', {
        'profile': profile, 'total': total,
        'status_data': status_data, 'priority_data': priority_data,
        'cat_data': cat_data, 'assignee_data': assignee_data,
    })


# ── profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    profile = _profile(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name  = request.POST.get('last_name',  '')
            request.user.email      = request.POST.get('email',      '')
            request.user.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
        })
    return render(request, 'complaints/profile.html', {'form': form, 'profile': profile})
