# -*- coding: utf-8 -*-
'''
diacamma.member test_tools package

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

from lucterios.framework.xfergraphic import XferContainerAcknowledge

from diacamma.accounting.test_tools import default_compta
from diacamma.invoice.test_tools import default_articles
from diacamma.payoff.test_tools import default_bankaccount
from diacamma.member.editors import SeasonEditor
from diacamma.member.models import Season


def default_financial():
    default_compta()
    default_articles()
    default_bankaccount()


def default_season():
    xfer = XferContainerAcknowledge()
    for idx in range(20):
        xfer.params['begin_date'] = '%d-09-01' % (2000 + idx)
        xfer.item = Season()
        editor = SeasonEditor(xfer.item)
        editor.saving(xfer)
    Season.objects.get(id=10).set_has_actif()
