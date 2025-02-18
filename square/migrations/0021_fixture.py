# Generated by Django 5.1.1 on 2025-02-18 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0020_basketballprediction_away_team_expected_goals_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fixture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixture_id', models.IntegerField(unique=True)),
                ('fixture_date', models.DateTimeField()),
                ('status_short', models.CharField(max_length=10)),
                ('team_home', models.CharField(max_length=255)),
                ('team_away', models.CharField(max_length=255)),
                ('score_fulltime_home', models.IntegerField(blank=True, null=True)),
                ('score_fulltime_away', models.IntegerField()),
            ],
        ),
    ]
