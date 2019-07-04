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
from django.conf import settings

from lucterios.CORE.models import PrintModel
from lucterios.framework.tools import set_locale_lang


def initial_values(*args):
    set_locale_lang(settings.LANGUAGE_CODE)
    PrintModel().load_model("diacamma.member", "Adherent_0006", is_default=False)
    PrintModel().load_model("diacamma.member", "Adherent_0007", is_default=False)


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0006_change_ordering'),
    ]

    operations = [
        migrations.RunPython(initial_values),
    ]
