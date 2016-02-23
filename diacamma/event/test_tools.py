# -*- coding: utf-8 -*-
'''
diacamma.event package

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

from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params

from diacamma.member.models import Activity

from diacamma.event.models import DegreeType, SubDegreeType, Degree


def default_event_params():
    for activity in Activity.objects.all():
        for level in range(1, 10):
            DegreeType.objects.create(
                name="level #%d.%d" % (activity.id, level), level=level, activity=activity)
    for level in range(1, 6):
        SubDegreeType.objects.create(
            name="sublevel #%d" % level, level=level)
    Parameter.change_value("event-degree-text", 'Grade')
    Parameter.change_value("event-subdegree-text", 'Barette')
    Parameter.change_value("event-comment-text", 'Epreuve 1:{[br/]}Epreuve 2:{[br/]}')
    Params.clear()


def add_default_degree():
    # Avrel Dalton level 1.2 sublevel 3
    Degree.objects.create(
        adherent_id=2, degree_id=2, subdegree_id=3, date='2011-11-04')
    # William Dalton level 1.7
    Degree.objects.create(
        adherent_id=3, degree_id=7, subdegree_id=None, date='2011-10-11')
    # Jack Dalton level 2.2 sublevel 1
    Degree.objects.create(
        adherent_id=4, degree_id=11, subdegree_id=1, date='2012-04-09')
    # Joe Dalton level 2.6
    Degree.objects.create(
        adherent_id=5, degree_id=15, subdegree_id=None, date='2010-09-21')
    # Lucky Luke level 1.3 sublevel 6
    Degree.objects.create(
        adherent_id=6, degree_id=3, subdegree_id=6, date='2011-07-14')
