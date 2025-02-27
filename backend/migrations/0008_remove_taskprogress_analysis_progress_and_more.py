# Generated by Django 5.1.1 on 2025-01-26 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_taskprogress_analysis'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskprogress_analysis',
            name='progress',
        ),
        migrations.AddField(
            model_name='taskprogress_analysis',
            name='failed',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taskprogress_analysis',
            name='successful',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taskprogress_analysis',
            name='to_be_processed',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taskprogress_analysis',
            name='total_processed',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
