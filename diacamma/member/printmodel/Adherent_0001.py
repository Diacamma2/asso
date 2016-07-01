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

name = _("adherents listing")
kind = 0
modelname = Adherent.get_long_name()
value = """210
297
22//%s//#num
25//%s//#lastname
40//%s//#firstname
50//%s//#address
15//%s//#postal_code
30//%s//#city
20//%s//#tel1 #tel2
35//%s//#email
30//%s//#comment
""" % (_('numeros'), _('lastname'), _('firstname'), _('address'), _('postal code'), _('city'), _('phone'), _('email'), _('comment'))
