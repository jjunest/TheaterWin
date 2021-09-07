# Generated by Django 3.1.5 on 2021-09-04 07:23

from django.db import migrations, models
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('TheaterWinBook', '0004_auto_20210904_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocksummarykr',
            name='id',
            field=models.AutoField(auto_created=True, default=2, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='stocksummarykr',
            name='info_date',
            field=models.DateField(default=django.utils.datetime_safe.datetime.now),
        ),
        migrations.AlterField(
            model_name='stocksummarykr',
            name='stock_code',
            field=models.SmallIntegerField(default=0),
        ),
    ]
