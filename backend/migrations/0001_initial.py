# Generated by Django 5.1.1 on 2024-11-18 11:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(blank=True, max_length=10, null=True)),
                ('flag', models.URLField(blank=True, max_length=300, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('current', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('league_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=50)),
                ('logo', models.URLField(max_length=300)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.country')),
                ('seasons', models.ManyToManyField(related_name='leagues', to='backend.season')),
            ],
        ),
    ]
