# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-14 15:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0007_storage'),
        ('event', '0005_invoice_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='default_article_nomember',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventnomember', to='invoice.Article', verbose_name='default article (no member)'),
        ),
        migrations.AlterField(
            model_name='event',
            name='default_article',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='event', to='invoice.Article', verbose_name='default article (member)'),
        ),
    ]
