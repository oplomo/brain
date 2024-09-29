# Generated by Django 5.1.1 on 2024-09-28 14:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0006_remove_matchprediction_sport_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketballPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('home_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('three_way_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expected_goals_overtime', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('expected_goals_overtime_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('expected_goals_overtime_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('tovertime_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='square.match')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FootballPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('home_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('three_way_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('gg_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('gg_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('no_gg_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('no_gg_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('gg_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='square.match')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TennisPrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('home_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('draw_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('away_team_win_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('three_way_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('total_games', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('total_games_probability', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('total_games_odds', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('tgame_match_result', models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='square.match')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='MatchPrediction',
        ),
    ]