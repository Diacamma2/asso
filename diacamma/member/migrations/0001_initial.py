# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'documents needs',
                'verbose_name': 'document needs',
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('num', models.IntegerField(default=None, null=True, verbose_name='numeros')),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
            ],
            options={
                'ordering': ['num'],
                'default_permissions': [],
                'verbose_name_plural': 'periods',
                'verbose_name': 'period',
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('designation', models.CharField(max_length=100, verbose_name='designation')),
                ('iscurrent', models.BooleanField(default=True, verbose_name='is current')),
            ],
            options={
                'ordering': ['-designation'],
                'verbose_name_plural': 'seasons',
                'verbose_name': 'season',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(default='', null=True, verbose_name='description')),
                ('duration', models.IntegerField(default=0, db_index=True, choices=[(0, 'annually'), (1, 'periodic'), (2, 'monthly'), (3, 'calendar')], verbose_name='duration')),
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
            field=models.ForeignKey(to='member.Season', verbose_name='season', default=None),
        ),
        migrations.AddField(
            model_name='document',
            name='season',
            field=models.ForeignKey(to='member.Season', verbose_name='season', default=None),
        ),
    ]
