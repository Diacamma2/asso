# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField(null=True, verbose_name='numeros', default=None)),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'periods',
                'verbose_name': 'period',
                'ordering': ['num'],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('designation', models.CharField(max_length=100, verbose_name='designation')),
                ('iscurrent', models.BooleanField(default=True, verbose_name='is current')),
                ('doc_need', models.TextField(null=True, verbose_name='doc need', default='')),
            ],
            options={
                'verbose_name_plural': 'seasons',
                'verbose_name': 'season',
                'ordering': ['-designation'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(null=True, verbose_name='description', default='')),
                ('duration', models.IntegerField(db_index=True, choices=[(0, 'annually'), (1, 'periodic'), (2, 'monthly'), (3, 'calendar')], default=0, verbose_name='duration')),
                ('unactive', models.BooleanField(default=True, verbose_name='unactive')),
                ('articles', models.ManyToManyField(blank=True, to='invoice.Article', verbose_name='articles')),
            ],
            options={
                'verbose_name_plural': 'subscriptions',
                'verbose_name': 'subscription',
            },
        ),
        migrations.AddField(
            model_name='period',
            name='season',
            field=models.ForeignKey(default=None, verbose_name='season', to='member.Season'),
        ),
    ]
