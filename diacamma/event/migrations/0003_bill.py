# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-18 09:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0001_initial'),
        ('event', '0002_outing'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='default_article',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='invoice.Article', verbose_name='default article'),
        ),
        migrations.AddField(
            model_name='participant',
            name='article',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='invoice.Article', verbose_name='article'),
        ),
        migrations.AddField(
            model_name='participant',
            name='bill',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='invoice.Bill', verbose_name='bill'),
        ),
    ]
