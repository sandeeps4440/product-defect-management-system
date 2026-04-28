from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from complaints.models import DefectCategory, UserProfile, Complaint, ComplaintUpdate, Notification, ROLE_COLORS


def make_user(username, password, first, last, email, role, is_staff=False, is_super=False):
    user, _ = User.objects.get_or_create(username=username)
    user.first_name = first; user.last_name = last; user.email = email
    user.is_staff = is_staff; user.is_superuser = is_super; user.is_active = True
    user.set_password(password)
    user.save()
    p, _ = UserProfile.objects.get_or_create(user=user)
    p.role = role; p.avatar_color = ROLE_COLORS.get(role, '#6366f1'); p.save()
    return user


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating categories...')
        cats = [
            ('Software Bug',          '🐛', 'developer',       '#6366f1', 'App crashes, errors, unexpected behavior'),
            ('UI/UX Issue',           '🎨', 'designer',        '#ec4899', 'Visual or layout problems'),
            ('Functionality Failure', '⚙️', 'tester',          '#f59e0b', 'Feature not working as expected'),
            ('Performance Issue',     '⚡', 'developer',       '#3b82f6', 'Slow response or lag'),
            ('Security Vulnerability','🔒', 'qa_engineer',     '#ef4444', 'Security flaws or data exposure'),
            ('Physical Damage',       '📦', 'product_manager', '#8b5cf6', 'Hardware or physical defects'),
            ('Documentation Error',   '📄', 'support',         '#10b981', 'Wrong or missing documentation'),
            ('Compatibility Issue',   '🔌', 'qa_engineer',     '#f97316', 'Does not work on supported platform'),
        ]
        for name, icon, role, color, desc in cats:
            DefectCategory.objects.update_or_create(
                name=name, defaults={'icon': icon, 'suggested_role': role, 'color': color, 'description': desc})

        self.stdout.write('Creating users...')
        admin = make_user('admin',         'admin123',    'Admin', 'User',   'admin@demo.com',  'admin',           True, True)
        alice = make_user('dev_alice',      'staff123',    'Alice', 'Dev',    'alice@demo.com',  'developer')
        bob   = make_user('dev_bob',        'staff123',    'Bob',   'Coder',  'bob@demo.com',    'developer')
        cara  = make_user('designer_cara',  'staff123',    'Cara',  'Design', 'cara@demo.com',   'designer')
        dan   = make_user('tester_dan',     'staff123',    'Dan',   'Tester', 'dan@demo.com',    'tester')
        emma  = make_user('qa_emma',        'staff123',    'Emma',  'QA',     'emma@demo.com',   'qa_engineer')
        frank = make_user('pm_frank',       'staff123',    'Frank', 'PM',     'frank@demo.com',  'product_manager')
        grace = make_user('support_grace',  'staff123',    'Grace', 'Help',   'grace@demo.com',  'support')
        cust1 = make_user('customer1',      'customer123', 'John',  'Smith',  'john@demo.com',   'customer')
        cust2 = make_user('customer2',      'customer123', 'Jane',  'Doe',    'jane@demo.com',   'customer')

        self.stdout.write('Creating complaints...')
        def mc(title, product, order, desc, cat_name, priority, user):
            cat = DefectCategory.objects.get(name=cat_name)
            c, created = Complaint.objects.get_or_create(title=title, defaults={
                'product_name': product, 'order_number': order, 'description': desc,
                'defect_category': cat, 'priority': priority, 'raised_by': user, 'status': 'pending'})
            if created:
                ComplaintUpdate.objects.create(complaint=c, updated_by=user,
                    message='Complaint submitted. Awaiting admin review.', new_status='pending')
            return c

        c1 = mc('App crashes on checkout',          'ShopEasy App',      'ORD-001', 'Crashes every time at checkout page.',          'Software Bug',          'critical', cust1)
        c2 = mc('Broken screen protector',           'Screen Guard X1',   'ORD-002', 'Arrived with cracks. Bad packaging.',           'Physical Damage',       'high',     cust1)
        c3 = mc('Login button invisible on mobile',  'Customer Portal',   '',        'White text on white background in dark mode.',  'UI/UX Issue',           'high',     cust2)
        c4 = mc('Payment confirmation not sent',     'E-Commerce',        'ORD-003', 'No email after payment. Money deducted.',       'Functionality Failure', 'high',     cust2)
        c5 = mc('Dashboard takes 30s to load',       'Analytics Suite',   '',        '30+ seconds to load basic charts.',             'Performance Issue',     'medium',   cust1)

        # Admin assigns two as demo
        for c, assignee, cat_name in [(c1, alice, 'Software Bug'), (c3, cara, 'UI/UX Issue')]:
            cat = DefectCategory.objects.get(name=cat_name)
            c.defect_category = cat; c.assigned_to = assignee; c.status = 'assigned'; c.save()
            n = assignee.get_full_name() or assignee.username
            r = assignee.profile.get_role_display()
            msg = f'Admin identified fault: {cat.name}. Assigned to {n} ({r}). Priority: {c.get_priority_display()}. Status → Assigned.'
            ComplaintUpdate.objects.create(complaint=c, updated_by=admin,
                message=msg, old_status='pending', new_status='assigned')
            Notification.objects.create(user=c.raised_by, complaint=c,
                message=f"Your complaint '{c.title}' has been reviewed by Admin and assigned to {n} ({r}). Fault: {cat.name}.")
            Notification.objects.create(user=assignee, complaint=c,
                message=f"Admin assigned complaint '{c.title}' to you. Priority: {c.get_priority_display()}.")

        self.stdout.write(self.style.SUCCESS("""
╔══════════════════════════════════════════════════╗
║         DefectTrack Pro — Ready!                 ║
╠══════════════════════════════════════════════════╣
║  USERNAME          PASSWORD      ROLE            ║
║  admin             admin123      Admin            ║
║  dev_alice         staff123      Developer        ║
║  designer_cara     staff123      Designer         ║
║  tester_dan        staff123      Tester           ║
║  qa_emma           staff123      QA Engineer      ║
║  pm_frank          staff123      Product Manager  ║
║  support_grace     staff123      Support          ║
║  customer1         customer123   Customer         ║
║  customer2         customer123   Customer         ║
╠══════════════════════════════════════════════════╣
║  Register your own: http://127.0.0.1:8000/register║
╚══════════════════════════════════════════════════╝
"""))
