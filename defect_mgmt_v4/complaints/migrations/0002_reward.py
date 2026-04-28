from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(default=5000)),
                ('awarded_at', models.DateTimeField(auto_now_add=True)),
                ('is_seen', models.BooleanField(default=False)),
                ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rewards', to='complaints.complaint')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rewards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-awarded_at'],
                'unique_together': {('user', 'complaint')},
            },
        ),
    ]
