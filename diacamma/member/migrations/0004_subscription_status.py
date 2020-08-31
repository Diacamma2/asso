# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-05 12:45
from __future__ import unicode_literals

from django.db import migrations
import django_fsm
from django.db.models.fields.related import ForeignKey
from django.db.models import deletion


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0003_change_permission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='bill',
            field=ForeignKey(default=None, null=True, on_delete=deletion.SET_NULL, to='invoice.Bill', verbose_name='bill'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='status',
            field=django_fsm.FSMIntegerField(
                choices=[(0, 'waiting'), (1, 'building'), (2, 'valid'), (3, 'cancel'), (4, 'disbarred')], db_index=True, default=1, verbose_name='status'),
        ),
    ]
