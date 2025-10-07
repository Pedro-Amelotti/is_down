# Generated manually by ChatGPT
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('url', models.URLField(max_length=200)),
                (
                    'server',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='systems',
                        to='monitor.server',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='SystemDowntime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                (
                    'system',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='downtimes',
                        to='monitor.system',
                    ),
                ),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='SystemStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('checked_at', models.DateTimeField(default=django.utils.timezone.now)),
                (
                    'system',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='current_status',
                        to='monitor.system',
                    ),
                ),
            ],
            options={
                'ordering': ['system__name'],
            },
        ),
        migrations.CreateModel(
            name='SystemStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('checked_at', models.DateTimeField(default=django.utils.timezone.now)),
                (
                    'system',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='status_history',
                        to='monitor.system',
                    ),
                ),
            ],
            options={
                'ordering': ['-checked_at'],
            },
        ),
    ]
