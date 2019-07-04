# -*- coding: utf-8 -*-
'''
diacamma.syndic tests package

@author: Laurent GAY
@organization: sd-libre.fr
@contact: info@sd-libre.fr
@copyright: 2018 sd-libre.fr
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

from lucterios.framework.test import add_user
from lucterios.contacts.models import Individual
from lucterios.CORE.views import get_wizard_step_list
from lucterios.documents.views import DocumentShow

from diacamma.member.test_tools import set_parameters
from diacamma.member.tests_adherent import BaseAdherentTest
from diacamma.accounting.views import ThirdShow
from diacamma.invoice.views import BillShow


class AssoTest(BaseAdherentTest):

    def setUp(self):
        BaseAdherentTest.setUp(self)
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])
        ThirdShow.url_text
        DocumentShow.url_text
        BillShow.url_text
        self.add_subscriptions()
        contact = Individual.objects.get(id=5)
        contact.user = add_user('joe')
        contact.save()

    def test_status(self):
        self.calljson('/CORE/authentification', {'username': 'admin', 'password': 'admin'})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.calljson('/CORE/statusMenu', {})
        self.assert_observer('core.custom', 'CORE', 'statusMenu')
        self.assert_count_equal('', 19)

    def test_wizard(self):
        self.calljson('/CORE/authentification', {'username': 'admin', 'password': 'admin'})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        steplist = get_wizard_step_list()
        self.assertEqual(20, len(steplist.split(';')), steplist)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 1})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 18)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 2})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 14)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 3})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 9)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 4})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 5})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 11)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 6})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 20)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 7})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 13)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 8})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 9})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 11)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 10})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 10)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 11})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 12)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 12})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 13})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 14})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 17)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 15})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 8)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 16})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 9)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 17})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 10)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 18})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 18)

        self.calljson('/CORE/configurationWizard', {'steplist': steplist, 'step': 19})
        self.assert_observer('core.custom', 'CORE', 'configurationWizard')
        self.assert_count_equal('', 13)

    def test_situation(self):
        self.calljson('/CORE/authentification', {'username': 'joe', 'password': 'joe'})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.calljson('/CORE/situationMenu', {})
        self.assert_observer('core.custom', 'CORE', 'situationMenu')
        self.assert_count_equal('', 8)
