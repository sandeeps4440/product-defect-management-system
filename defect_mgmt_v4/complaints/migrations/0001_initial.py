from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('customer','Customer'),('developer','Developer'),('designer','Designer'),('tester','Tester'),('qa_engineer','QA Engineer'),('product_manager','Product Manager'),('support','Support Agent'),('admin','Admin')], default='customer', max_length=20)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('avatar_color', models.CharField(default='#6366f1', max_length=7)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DefectCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('suggested_role', models.CharField(choices=[('developer','Developer'),('designer','Designer'),('tester','Tester'),('qa_engineer','QA Engineer'),('product_manager','Product Manager'),('support','Support Agent')], default='developer', max_length=20)),
                ('color', models.CharField(default='#6366f1', max_length=7)),
                ('icon', models.CharField(default='🔧', max_length=10)),
            ],
            options={'verbose_name_plural': 'Defect Categories'},
        ),
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('complaint_id', models.CharField(editable=False, max_length=20, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('product_name', models.CharField(max_length=200)),
                ('order_number', models.CharField(blank=True, max_length=100)),
                ('priority', models.CharField(choices=[('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')], default='medium', max_length=10)),
                ('status', models.CharField(choices=[('pending','Pending Review'),('assigned','Assigned'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed'),('rejected','Rejected')], default='pending', max_length=15)),
                ('image', models.ImageField(blank=True, null=True, upload_to='complaints/%Y/%m/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaints_assigned', to=settings.AUTH_USER_MODEL)),
                ('defect_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='complaints.defectcategory')),
                ('raised_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints_raised', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ComplaintUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('old_status', models.CharField(blank=True, max_length=15)),
                ('new_status', models.CharField(blank=True, max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='complaints.complaint')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='complaints.complaint')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
