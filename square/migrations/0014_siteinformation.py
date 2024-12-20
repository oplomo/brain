# Generated by Django 5.1.1 on 2024-10-01 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('square', '0013_basketballprediction_expected_goals_awayteam_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(help_text='The name of the website.', max_length=255)),
                ('site_description', models.TextField(blank=True, help_text='A brief description of the website.')),
                ('logo', models.ImageField(blank=True, help_text='The logo of the site.', null=True, upload_to='logos/')),
                ('privacy_policy', models.TextField(blank=True, help_text='Privacy policy of the website.')),
                ('terms_and_conditions', models.TextField(blank=True, help_text='Terms and conditions of the website.')),
                ('facebook_link', models.URLField(blank=True, help_text='Link to Facebook page.')),
                ('twitter_link', models.URLField(blank=True, help_text='Link to Twitter profile.')),
                ('instagram_link', models.URLField(blank=True, help_text='Link to Instagram profile.')),
                ('linkedin_link', models.URLField(blank=True, help_text='Link to LinkedIn profile.')),
                ('reddit_link', models.URLField(blank=True, help_text='Link to reddit channel.')),
                ('discord_link', models.URLField(blank=True, help_text='Link to discord channel.')),
                ('contact_email', models.EmailField(blank=True, help_text='Contact email for the site.', max_length=255)),
                ('contact_phone', models.CharField(blank=True, help_text='Contact phone number for the site.', max_length=20)),
                ('address', models.TextField(blank=True, help_text='Physical address of the site or organization.')),
                ('support_email', models.EmailField(blank=True, help_text='Support email address.', max_length=255)),
                ('about_us', models.TextField(blank=True, help_text='Information about the website or company.')),
                ('newsletter_link', models.URLField(blank=True, help_text='Link to newsletter or subscription page.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
