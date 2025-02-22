# Generated by Django 5.1.1 on 2025-02-22 01:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0025_alter_match_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='gold_bar',
            field=models.CharField(default='N/A', max_length=50),
        ),
        migrations.AddField(
            model_name='match',
            name='is_premium',
            field=models.BooleanField(default=False),
        ),
    ]
