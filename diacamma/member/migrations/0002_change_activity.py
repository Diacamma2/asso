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

from django.db import migrations, models
from django.utils.translation import ugettext_lazy as _

from diacamma.member.models import Activity, License


def convert_values(*args):
    # add default activity
    if len(Activity.objects.all()) == 0:
        default_act = Activity.objects.create(
            name=_("default"), description=_("default"))
    else:
        default_act = Activity.objects.all()[0]
    for lic in License.objects.filter(activity__isnull=True):
        lic.activity = default_act
        lic.update()


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(convert_values),
        migrations.AlterField(
            model_name='license',
            name='activity',
            field=models.ForeignKey(
                default=None, on_delete=models.deletion.PROTECT, to='member.Activity', verbose_name='activity'),
        ),
    ]
