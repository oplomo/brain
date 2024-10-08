# Generated by Django 5.1.1 on 2024-09-29 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0010_footballprediction_total_card_result_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='footballprediction',
            name='dc12_normalized_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dc12_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dc12_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dc1x_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dc1x_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dc_result',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('won', 'Won'), ('lost', 'Lost')], default='waiting', max_length=50),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dcx2_odds',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='footballprediction',
            name='dcx2_probability',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
