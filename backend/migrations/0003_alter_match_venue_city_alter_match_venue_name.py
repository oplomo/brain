# Generated by Django 5.1.1 on 2024-11-18 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_matchdate_alter_league_logo_match'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='venue_city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='match',
            name='venue_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
