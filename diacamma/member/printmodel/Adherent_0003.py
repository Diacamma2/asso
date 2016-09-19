# -*- coding: utf-8 -*-
'''
Printmodel django module for accounting

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

from django.utils.translation import ugettext_lazy as _

from diacamma.member.models import Adherent

name = _("Complet listing")
kind = 0
modelname = Adherent.get_long_name()
value = """210
297
1//%s//#num
1//%s//#lastname
1//%s//#firstname
1//%s//#address
1//%s//#postal_code
1//%s//#city
1//%s//#tel1
1//%s//#tel2
1//%s//#email
1//%s//#comment
1//%s//#birthday
1//%s//#birthplace
1//%s//#current_subscription.season
1//%s//#current_subscription.subscriptiontype
1//%s//#current_subscription.begin_date
1//%s//#current_subscription.end_date
1//%s//#current_subscription.license_set.team
1//%s//#current_subscription.license_set.activity
1//%s//#current_subscription.license_set.value
""" % (_('numeros'), _('lastname'), _('firstname'), _('address'), _('postal code'), _('city'), _('tel1'), _('tel2'), _('email'),
       _('comment'), _("birthday"), _("birthplace"), _('season'), _('subscription type'), _('begin date'), _('end date'), _('team'), _('activity'), _('license #'))
