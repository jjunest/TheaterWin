# Generated by Django 3.1.5 on 2021-09-04 07:00

from django.db import migrations, models
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('TheaterWinBook', '0002_full_chatting_message_theaterwinbookrecordinfo_theaterwinbookrecordreply_theaterwinquestioninfo_thea'),
    ]

    operations = [
        migrations.CreateModel(
            name='STOCK_SUMMARY_KR',
            fields=[
                ('bat_time', models.DateTimeField(default=django.utils.datetime_safe.datetime.now)),
                ('info_date', models.DateField(default=django.utils.datetime_safe.datetime.now, primary_key=True, serialize=False)),
                ('stock_code', models.SmallIntegerField()),
                ('stock_name', models.CharField(max_length=20)),
            ],
        ),
    ]
