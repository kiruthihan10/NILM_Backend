# Generated by Django 3.2.8 on 2022-06-05 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Predictionapp', '0002_auto_20220603_1120'),
    ]

    operations = [
        migrations.RenameField(
            model_name='aggregate',
            old_name='Power_Consumption',
            new_name='Power_Consumption_phase_1',
        ),
        migrations.AddField(
            model_name='aggregate',
            name='Power_Consumption_phase_2',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='aggregate',
            name='Power_Consumption_phase_3',
            field=models.FloatField(default=0),
        ),
    ]
