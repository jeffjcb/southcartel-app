# Generated by Django 3.2.5 on 2021-09-18 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_variation_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('size&color', 'size&color')], max_length=100),
        ),
    ]
