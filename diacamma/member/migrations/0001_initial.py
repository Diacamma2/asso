# -*- coding: utf-8 -*-
'''
Initial django functions

@author: Laurent GAY
@organization: sd-libre.fr
@contact: info@sd-libre.fr
@copyright: 2015 sd-libre.fr
@license: This file is part of Lucterios.

Lucterios is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Lucterios is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Lucterios.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import unicode_literals
from datetime import date

from django.db import migrations, models
from django.utils import translation
from django.conf import settings

from lucterios.CORE.models import PrintModel


def initial_values(*args):
    translation.activate(settings.LANGUAGE_CODE)
    PrintModel().load_model("diacamma.member", "Adherent_0001", is_default=True)
    PrintModel().load_model("diacamma.member", "Adherent_0002", is_default=False)
    PrintModel().load_model("diacamma.member", "Adherent_0003", is_default=False)
    PrintModel().load_model("diacamma.member", "Adherent_0004", is_default=True)
    PrintModel().load_model("diacamma.member", "Adherent_0005", is_default=False)


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
            ],
            options={
                'verbose_name_plural': 'activities',
                'verbose_name': 'activity',
            },
        ),
        migrations.CreateModel(
            name='Adherent',
            fields=[
                ('individual_ptr', models.OneToOneField(on_delete=models.CASCADE, parent_link=True, auto_created=True,
                                                        to='contacts.Individual', primary_key=True, serialize=False)),
                ('num', models.IntegerField(
                    default=0, verbose_name='numeros')),
                ('birthday', models.DateField(
                    default=date.today, null=True, verbose_name='birthday')),
                ('birthplace', models.CharField(
                    blank=True, max_length=50, verbose_name='birthplace')),
            ],
            options={
                'verbose_name_plural': 'adherents',
                'verbose_name': 'adherent',
            },
            bases=('contacts.individual',),
        ),
        migrations.CreateModel(
            name='Age',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('minimum', models.IntegerField(
                    verbose_name='minimum', default=0)),
                ('maximum', models.IntegerField(
                    verbose_name='maximum', default=0)),
            ],
            options={
                'verbose_name_plural': 'ages',
                'ordering': ['-minimum'],
                'verbose_name': 'age',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(
                    max_length=100, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'documents needs',
                'verbose_name': 'document needs',
                'default_permissions': [],
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('num', models.IntegerField(
                    null=True, verbose_name='numeros', default=None)),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
            ],
            options={
                'verbose_name_plural': 'periods',
                'ordering': ['num'],
                'verbose_name': 'period',
                'default_permissions': [],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('designation', models.CharField(
                    max_length=100, verbose_name='designation')),
                ('iscurrent', models.BooleanField(
                    verbose_name='is current', default=False)),
            ],
            options={
                'verbose_name_plural': 'seasons',
                'ordering': ['-designation'],
                'verbose_name': 'season',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
                ('adherent', models.ForeignKey(on_delete=models.CASCADE,
                                               default=None, to='member.Adherent', verbose_name='adherent')),
                ('season', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                             default=None, to='member.Season', verbose_name='season')),
            ],
            options={
                'verbose_name_plural': 'subscription',
                'verbose_name': 'subscription',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionType',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
                ('duration', models.IntegerField(choices=[(0, 'annually'), (1, 'periodic'), (
                    2, 'monthly'), (3, 'calendar')], default=0, db_index=True, verbose_name='duration')),
                ('unactive', models.BooleanField(
                    verbose_name='unactive', default=False)),
                ('articles', models.ManyToManyField(
                    to='invoice.Article', blank=True, verbose_name='articles')),
            ],
            options={
                'verbose_name_plural': 'subscription types',
                'verbose_name': 'subscription type',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
                ('unactive', models.BooleanField(
                    verbose_name='unactive', default=False)),
            ],
            options={
                'verbose_name_plural': 'teams',
                'verbose_name': 'team',
            },
        ),
        migrations.CreateModel(
            name='DocAdherent',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value', models.BooleanField(
                    default=False, verbose_name='value')),
                ('document', models.ForeignKey(default=None, on_delete=models.deletion.PROTECT,
                                               verbose_name='document', to='member.Document')),
                ('subscription', models.ForeignKey(default=None, on_delete=models.deletion.CASCADE,
                                                   verbose_name='subscription', to='member.Subscription')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'documents',
                'verbose_name': 'document',
            },
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value', models.CharField(
                    null=True, verbose_name='license #', max_length=50)),
                ('activity', models.ForeignKey(default=None, null=True,
                                               on_delete=models.deletion.PROTECT, verbose_name='activity', to='member.Activity')),
                ('subscription', models.ForeignKey(on_delete=models.CASCADE,
                                                   verbose_name='subscription', default=None, to='member.Subscription')),
                ('team', models.ForeignKey(default=None, null=True,
                                           on_delete=models.deletion.PROTECT, verbose_name='team', to='member.Team')),
            ],
            options={
                'verbose_name': 'license',
                'default_permissions': [],
                'verbose_name_plural': 'licenses'
            },
        ),
        migrations.AddField(
            model_name='subscription',
            name='subscriptiontype',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, default=None,
                                    to='member.SubscriptionType', verbose_name='subscription type'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='bill',
            field=models.ForeignKey(
                null=True, verbose_name='bill', on_delete=models.deletion.PROTECT, to='invoice.Bill', default=None),
        ),
        migrations.AddField(
            model_name='period',
            name='season',
            field=models.ForeignKey(on_delete=models.CASCADE,
                                    default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.AddField(
            model_name='document',
            name='season',
            field=models.ForeignKey(on_delete=models.CASCADE,
                                    default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.RunPython(initial_values),
    ]
