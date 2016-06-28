# -*- coding: utf-8 -*-
'''
diacamma.event.migrations inital module

@author: Laurent GAY
@organization: sd-libre.fr
@contact: info@sd-libre.fr
@copyright: 2016 sd-libre.fr
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

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('member', '0003_change_permission'),
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Degree',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='date')),
                ('adherent', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE,
                                               to='member.Adherent', verbose_name='adherent')),
            ],
            options={
                'verbose_name': 'degree',
                'verbose_name_plural': 'degrees',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='DegreeType',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    max_length=100, verbose_name='name')),
                ('level', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(
                    1), django.core.validators.MaxValueValidator(100)], verbose_name='level')),
                ('activity', models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT,
                                               to='member.Activity', verbose_name='activity')),
            ],
            options={
                'verbose_name': 'degree type',
                'verbose_name_plural': 'degree types',
                'ordering': ['activity', '-level'],
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='date')),
                ('comment', models.TextField(
                    blank=False, verbose_name='comment')),
                ('status', models.IntegerField(choices=[
                 (0, 'building'), (1, 'valid')], db_index=True, default=0, verbose_name='status')),
                ('activity', models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT,
                                               to='member.Activity', verbose_name='activity')),
            ],
            options={
                'verbose_name_plural': 'events',
                'verbose_name': 'event',
            },
        ),
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isresponsible', models.BooleanField(
                    default=False, verbose_name='responsible')),
                ('contact', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE,
                                              to='contacts.Individual', verbose_name='contact')),
                ('event', models.ForeignKey(
                    default=None, on_delete=django.db.models.deletion.CASCADE, to='event.Event', verbose_name='event')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'organizers',
                'verbose_name': 'organizer',
            },
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(
                    blank=True, verbose_name='comment')),
                ('contact', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE,
                                              to='contacts.Individual', verbose_name='contact')),
                ('degree_result', models.ForeignKey(default=None, null=True,
                                                    on_delete=django.db.models.deletion.CASCADE, to='event.DegreeType', verbose_name='degree result')),
                ('event', models.ForeignKey(
                    default=None, on_delete=django.db.models.deletion.CASCADE, to='event.Event', verbose_name='event')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'participants',
                'verbose_name': 'participant',
            },
        ),
        migrations.CreateModel(
            name='SubDegreeType',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    max_length=100, verbose_name='name')),
                ('level', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(
                    1), django.core.validators.MaxValueValidator(100)], verbose_name='level')),
            ],
            options={
                'default_permissions': [],
                'verbose_name': 'sub degree type',
                'verbose_name_plural': 'sub degree types',
                'ordering': ['-level'],
            },
        ),
        migrations.AddField(
            model_name='participant',
            name='subdegree_result',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='event.SubDegreeType', verbose_name='sub-degree result'),
        ),
        migrations.AddField(
            model_name='degree',
            name='degree',
            field=models.ForeignKey(
                default=None, on_delete=django.db.models.deletion.PROTECT, to='event.DegreeType', verbose_name='degree'),
        ),
        migrations.AddField(
            model_name='degree',
            name='event',
            field=models.ForeignKey(
                default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='event.Event', verbose_name='event'),
        ),
        migrations.AddField(
            model_name='degree',
            name='subdegree',
            field=models.ForeignKey(
                default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='event.SubDegreeType', verbose_name='sub degree'),
        ),
    ]
