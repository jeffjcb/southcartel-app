# Generated by Django 3.2.5 on 2021-10-13 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_preferences_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='preferences',
            options={'verbose_name': 'preference', 'verbose_name_plural': 'preferences'},
        ),
        migrations.AddField(
            model_name='refundrequests',
            name='processed',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]