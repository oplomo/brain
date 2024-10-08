# Generated by Django 5.1.1 on 2024-09-29 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0012_footballprediction_dc1x_normalized_probability_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_awayteam',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_awayteam_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_awayteam_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_halftime',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_halftime_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_halftime_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_hometeam',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_hometeam_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='expected_goals_hometeam_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='t_awayteam_result',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='t_hometeam_result',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50),
        ),
        migrations.AddField(
            model_name='basketballprediction',
            name='thalftime_match_result',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50),
        ),
    ]
