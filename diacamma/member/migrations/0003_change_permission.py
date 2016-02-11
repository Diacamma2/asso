# -*- coding: utf-8 -*-
'''
diacamma.member.migrations change module

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

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0002_change_activity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'default_permissions': [], 'verbose_name': 'activity', 'verbose_name_plural': 'activities'},
        ),
        migrations.AlterModelOptions(
            name='age',
            options={'default_permissions': [], 'ordering': ['-minimum'], 'verbose_name': 'age', 'verbose_name_plural': 'ages'},
        ),
        migrations.AlterModelOptions(
            name='season',
            options={'default_permissions': ['add', 'change'], 'ordering': ['-designation'], 'verbose_name': 'season', 'verbose_name_plural': 'seasons'},
        ),
        migrations.AlterModelOptions(
            name='subscriptiontype',
            options={'default_permissions': [], 'verbose_name': 'subscription type', 'verbose_name_plural': 'subscription types'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'default_permissions': [], 'verbose_name': 'team', 'verbose_name_plural': 'teams'},
        ),
    ]
