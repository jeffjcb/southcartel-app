# Generated by Django 3.2.5 on 2021-09-17 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_auto_20210913_1354'),
    ]

    operations = [
        migrations.AddField(
            model_name='variation',
            name='stock',
            field=models.IntegerField(default=0.00024740227610094015),
            preserve_default=False,
        ),
    ]
