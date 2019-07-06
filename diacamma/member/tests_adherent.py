# -*- coding: utf-8 -*-
'''
lucterios.contacts package

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
from shutil import rmtree
from datetime import date
from _io import StringIO

from django.utils import formats, six
from os.path import isfile
from base64 import b64decode

from lucterios.framework.test import LucteriosTest
from lucterios.framework.filetools import get_user_dir
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params
from lucterios.contacts.views_contacts import LegalEntityShow
from lucterios.contacts.models import LegalEntity
from lucterios.contacts.views import ContactImport
from lucterios.contacts.tests_contacts import change_ourdetail

from diacamma.invoice.views import BillList, BillTransition, BillFromQuotation, BillAddModify, BillShow, DetailAddModify
from diacamma.accounting.views import ThirdShow

from diacamma.member.models import Season
from diacamma.member.views import AdherentActiveList, AdherentAddModify, AdherentShow,\
    SubscriptionAddModify, SubscriptionShow, LicenseAddModify, LicenseDel,\
    AdherentDoc, AdherentLicense, AdherentLicenseSave, AdherentStatistic,\
    AdherentRenewList, AdherentRenew, SubscriptionTransition, AdherentCommand,\
    AdherentCommandDelete, AdherentCommandModify, AdherentFamilyAdd,\
    AdherentFamilySelect, AdherentFamilyCreate, FamilyAdherentAdd,\
    FamilyAdherentCreate, FamilyAdherentAdded, AdherentListing,\
    AdherentThirdList
from diacamma.member.test_tools import default_season, default_financial, default_params,\
    default_adherents, default_subscription, set_parameters, default_prestation
from diacamma.accounting.models import FiscalYear
from diacamma.accounting.test_tools import fill_accounts_fr
from diacamma.invoice.models import get_or_create_customer


class BaseAdherentTest(LucteriosTest):

    def __init__(self, methodName):
        LucteriosTest.__init__(self, methodName)
        if date.today().month > 8:
            self.dateref_expected = date(
                2009, date.today().month, date.today().day)
        else:
            self.dateref_expected = date(
                2010, date.today().month, date.today().day)

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()

    def add_subscriptions(self, year=2009, season_id=10):
        default_adherents()
        default_subscription()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 3, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 2, 'period': 37 + (year - 2009) * 4, 'season': season_id, 'team': 1, 'activity': 1, 'value': '645'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 4, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 3, 'month': '%s-10' % year, 'season': season_id, 'team': 3, 'activity': 1, 'value': '489'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 4, 'begin_date': '%s-09-15' % year, 'season': season_id, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 6, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 1, 'activity': 2, 'value': '159'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')


class AdherentTest(BaseAdherentTest):

    def setUp(self):
        BaseAdherentTest.setUp(self)
        Parameter.change_value('member-family-type', 0)
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])
        ThirdShow.url_text

    def test_defaultlist(self):
        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('', 2 + 6 + 2)
        self.assert_attrib_equal('team', 'description', 'group')
        self.assert_attrib_equal('activity', 'description', 'passion')
        self.assert_select_equal('status', 3)  # nb=3
        self.assert_select_equal('age', 8, True)
        self.assert_select_equal('team', 3, True)
        self.assert_select_equal('activity', 2, True)
        self.assert_json_equal('DATE', 'dateref', self.dateref_expected.isoformat())
        self.assert_select_equal('genre', 3)  # nb=3
        self.assert_count_equal('#adherent/actions', 5)
        self.assert_grid_equal('adherent', {'num': "N°", 'firstname': "prénom", 'lastname': "nom", 'tel1': "tel1", 'tel2': "tel2", 'email': "courriel", 'license': "participation"}, 0)
        self.assert_json_equal('', '#adherent/size_by_page', 25)
        self.assertEqual(len(self.json_actions), 3, self.json_actions)

        Parameter.change_value("member-size-page", 100)
        Parameter.change_value("member-fields", "firstname;lastname;email;documents")
        Params.clear()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_grid_equal('adherent', {'firstname': "prénom", 'lastname': "nom", 'email': "courriel", 'documents': "documents demandés"}, 0)
        self.assert_json_equal('', '#adherent/size_by_page', 100)

    def test_add_adherent(self):
        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal('', 1 + 14)
        self.assertEqual(len(self.json_actions), 2)

        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {"address": 'Avenue de la Paix{[newline]}BP 987',
                                                             "comment": 'no comment', "firstname": 'Marie', "lastname": 'DUPOND',
                                                             "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                             "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'marie.dupond@worldcompany.com',
                                                             "birthday": "1998-08-04", "birthplace": "Fort-de-France",
                                                             "genre": "2"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 2 + (18 + 1) + 2 + 2)  # header + identity + subscription + grade
        self.assert_json_equal('LABELFORM', 'dateref', self.dateref_expected.isoformat(), True)
        self.assert_json_equal('LABELFORM', 'firstname', "Marie")
        self.assert_json_equal('LABELFORM', 'lastname', "DUPOND")
        self.assert_json_equal('LABELFORM', 'num', "1")
        self.assert_json_equal('LABELFORM', 'birthday', "1998-08-04")
        self.assert_json_equal('LABELFORM', 'birthplace', "Fort-de-France")
        self.assert_json_equal('LABELFORM', 'age_category', "Benjamins")
        self.assert_count_equal('subscription', 0)  # nb=6
        self.assert_count_equal('degrees', 0)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'birthday', "1998-08-04")
        self.assert_json_equal('LABELFORM', 'age_category', "Cadets")

        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {"address": 'Avenue de la Paix{[newline]}BP 987',
                                                             "comment": 'no comment', "firstname": 'Jean', "lastname": 'DUPOND',
                                                             "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                             "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'jean.dupond@worldcompany.com',
                                                             "birthday": "2000-06-22", "birthplace": "Fort-de-France",
                                                             "genre": "1"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Jean")
        self.assert_json_equal('LABELFORM', 'lastname', "DUPOND")
        self.assert_json_equal('LABELFORM', 'num', "2")
        self.assert_json_equal('LABELFORM', 'birthday', "2000-06-22")
        self.assert_json_equal('LABELFORM', 'age_category', "Poussins")

    def test_add_subscription(self):
        default_adherents()

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_grid_equal('subscription', {'status': "status", 'season': "saison", 'subscriptiontype': "type de cotisation", 'begin_date': "date de début", 'end_date': "date de fin", 'involvement': "participation"}, 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'subscriptionAddModify')

        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 9)
        self.assert_select_equal('season', 20)  # nb=20
        self.assert_select_equal('subscriptiontype', {1: "Annually [76,44 €]", 2: "Periodic [76,44 €]", 3: "Monthly [76,44 €]", 4: "Calendar [76,44 €]"})
        self.assert_attrib_equal('team', 'description', 'group')
        self.assert_attrib_equal('activity', 'description', 'passion')
        self.assert_select_equal('team', 3)  # nb=3
        self.assert_select_equal('activity', 2)  # nb=2

    def test_add_subscription_annually(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 9)
        self.assert_json_equal('SELECT', 'season', '10')
        self.assert_select_equal('status', 2)  # nb=2
        self.assert_json_equal('SELECT', 'status', '2')
        self.assert_json_equal('SELECT', 'subscriptiontype', '1')
        self.assert_json_equal('LABELFORM', 'seasondates', "1 sep. 2009 => 31 août 2010")

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'status': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity1] abc123"])

    def test_add_subscription_periodic(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 9)
        self.assert_json_equal('SELECT', 'season', '10')
        self.assert_json_equal('SELECT', 'subscriptiontype', '2')
        self.assert_select_equal('period', 4)  # nb=4
        self.assert_json_equal('', '#period/case/@2/@0', '39')

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 2, 'season': 10, 'period': 39, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-03-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-05-31")

    def test_add_subscription_monthly(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 9)
        self.assert_json_equal('SELECT', 'season', '10')
        self.assert_json_equal('SELECT', 'subscriptiontype', '3')
        self.assert_select_equal('month', 12)  # nb=12
        self.assert_json_equal('', '#month/case/@3/@0', "2009-12")

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 3, 'season': 10, 'month': '2009-12', 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-12-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2009-12-31")

    def test_add_subscription_calendar(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 9)
        self.assert_json_equal('SELECT', 'season', '10')
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_json_equal('DATE', 'begin_date', self.dateref_expected.isoformat())

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 4, 'season': 10, 'begin_date': '2009-10-01', 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-10-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-09-30")

    def test_show_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'status': 2, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_grid_equal('license', {'team': "group", 'activity': "passion", 'value': "N° licence"}, 1)
        self.assert_json_equal('', 'license/@0/team', "team2")
        self.assert_json_equal('', 'license/@0/activity', "activity1")
        self.assert_json_equal('', 'license/@0/value', "abc123")

        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'licenseAddModify')
        self.assert_count_equal('', 4)
        self.assert_attrib_equal('team', 'description', 'group')
        self.assert_attrib_equal('activity', 'description', 'passion')
        self.assert_select_equal('team', 3)  # nb=3
        self.assert_select_equal('activity', 2)  # nb=2

        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1, 'team': 1, 'activity': 2, 'value': '987xyz'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/license', ["team1 [activity2] 987xyz", "team2 [activity1] abc123"])

        self.factory.xfer = AdherentLicense()
        self.calljson('/diacamma.member/adherentLicense', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentLicense')
        self.assert_count_equal('', 4 + 4 * 2)
        self.assert_json_equal('EDIT', 'value_1', 'abc123')
        self.assert_json_equal('EDIT', 'value_2', '987xyz')

        self.factory.xfer = AdherentLicenseSave()
        self.calljson('/diacamma.member/adherentLicenseSave', {'adherent': 2, 'dateref': '2009-10-01', 'value_1': 'abcd1234', 'value_2': '9876wxyz'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentLicenseSave')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/license', ["team1 [activity2] 9876wxyz", "team2 [activity1] abcd1234"])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('license', 2)

        self.factory.xfer = LicenseDel()
        self.calljson('/diacamma.member/licenseDel', {'CONFIRME': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1, 'license': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseDel')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('license', 1)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

    def test_subscription_bydate(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('', 2 + 6 + 3)
        self.assert_count_equal('adherent', 5)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "4")
        self.assert_json_equal('', 'adherent/@2/id', "5")
        self.assert_json_equal('', 'adherent/@3/id', "3")
        self.assert_json_equal('', 'adherent/@4/id', "6")
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 1 octobre 2009")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-11-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@2/id', "3")
        self.assert_json_equal('', 'adherent/@3/id', "6")
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 15 novembre 2009")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-20'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@2/id', "6")
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 20 janvier 2010")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-09-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "3")
        self.assert_json_equal('', 'adherent/@2/id', "6")
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 1 septembre 2009")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-09-10'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/id', "5")
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 10 septembre 2010")

    def test_subscription_byage(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2010-09-10'}, False)
        self.assert_json_equal('LABELFORM', 'age_category', "Poussins")
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3, 'dateref': '2010-09-10'}, False)
        self.assert_json_equal('LABELFORM', 'age_category', "Benjamins")
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4, 'dateref': '2010-09-10'}, False)
        self.assert_json_equal('LABELFORM', 'age_category', "Juniors")
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5, 'dateref': '2010-09-10'}, False)
        self.assert_json_equal('LABELFORM', 'age_category', "Espoirs")
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 6}, False)
        self.assert_json_equal('LABELFORM', 'age_category', "Seniors")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '1;2;3'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 2)
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}Âge{[/u]}{[/b]} : Minimes, Benjamins, Poussins")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '4;5;6'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 2)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '7;8'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}Âge{[/u]}{[/b]} : Vétérans, Seniors")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '1;3;5;7'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)

    def test_subscription_byteam(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'team': '1'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 2)
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - team1 - date de référence : 1 octobre 2009")
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 6)
        self.assertEqual(info[2], "{[b]}{[u]}group{[/u]}{[/b]}")
        self.assertEqual(info[3], "team N°1")
        self.assertEqual(info[4], "The bests")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'team': '2;3'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)
        self.assertEqual(self.json_context['TITLE'], "Adhérents cotisants - date de référence : 1 octobre 2009")
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}group{[/u]}{[/b]} : team2, team3")

    def test_subscription_byactivity(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'activity': '1'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}passion{[/u]}{[/b]} : activity1")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'activity': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 2)
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}passion{[/u]}{[/b]} : activity2")

    def test_subscription_bygenre(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'genre': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)
        info = self.json_context['INFO'].split("{[br]}")
        self.assertEqual(len(info), 4)
        self.assertEqual(info[2], "{[b]}{[u]}genre{[/u]}{[/b]} : Femme")

    def test_subscription_doc(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_count_equal('', 2 + (19 + 5) + 2 + 5 + 4 + 2)  # header + identity/docs + subscription + financial + invoice + grade
        self.assert_attrib_equal('doc_1', "description", "Doc 1")
        self.assert_attrib_equal('doc_2', "description", "Doc 2")
        self.assert_json_equal('CHECK', 'doc_1', "0")
        self.assert_json_equal('CHECK', 'doc_2', "0")

        self.factory.xfer = AdherentDoc()
        self.calljson('/diacamma.member/adherentDoc', {'adherent': 2, 'dateref': '2009-10-01', 'doc_1': 1, 'doc_2': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentDoc')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_json_equal('CHECK', 'doc_1', "1")
        self.assert_json_equal('CHECK', 'doc_2', "0")

        self.factory.xfer = AdherentDoc()
        self.calljson('/diacamma.member/adherentDoc', {'adherent': 2, 'dateref': '2009-10-01', 'doc_1': 0, 'doc_2': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentDoc')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_json_equal('CHECK', 'doc_1', "0")
        self.assert_json_equal('CHECK', 'doc_2', "1")

    def test_subscription_withoutparams(self):
        self.add_subscriptions()
        set_parameters([])

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-09-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('', 3 + 2 + 2)

        self.assert_count_equal('adherent', 3)
        self.assert_count_equal('#adherent/actions', 4)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 2 + (15 + 5) + 2 + 5 + 4 + 2)  # header + identity + subscription + financial + invoice + grade
        self.assert_count_equal('subscription', 1)  # nb=5

        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal('', 1 + 12)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 6)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 7)

    def test_subscription_printlisting(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '1;2;3', 'team': '2;3', 'activity': '2', 'genre': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')

        new_context = dict(self.json_context)
        new_context['PRINT_MODE'] = '4'
        new_context['MODEL'] = 1
        self.factory.xfer = AdherentListing()
        self.calljson('/diacamma.member/adherentListing', new_context, False)
        self.assert_observer('core.print', 'diacamma.member', 'adherentListing')
        csv_value = b64decode(six.text_type(self.response_json['print']['content'])).decode("utf-8")
        content_csv = csv_value.split('\n')
        self.assertEqual(len(content_csv), 8, str(content_csv))
        self.assertEqual(content_csv[1].strip(), '"Adhérents cotisants - date de référence : 1 octobre 2009"')
        self.assertEqual(content_csv[3].strip(), '"status : en création & validé,,passion : activity2,,group : team2, team3,,Âge : Minimes, Benjamins, Poussins,,genre : Femme"')
        self.assertEqual(content_csv[4].strip(), '"nom";"adresse";"ville";"tel";"courriel";')

    def test_statistic(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('', 3)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_count_equal('town_1', 2)
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')
        self.assert_count_equal('town_2', 2)
        self.assert_json_equal('', 'town_2/@1/ratio', '{[b]}1{[/b]}')
        self.assert_count_equal('seniority_1', 1)
        self.assert_count_equal('team_1', 2)
        self.assert_count_equal('activity_1', 2)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01', 'only_valid': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_count_equal('town_1', 2)
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')
        self.assert_count_equal('town_2', 2)
        self.assert_json_equal('', 'town_2/@1/ratio', '{[b]}1{[/b]}')
        self.assert_count_equal('seniority_1', 1)
        self.assert_count_equal('team_1', 2)
        self.assert_count_equal('activity_1', 2)

    def test_renew(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@2/id', "6")

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-01-20'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 2)
        self.assert_json_equal('', 'adherent/@0/id', "4")
        self.assert_json_equal('', 'adherent/@1/id', "3")

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-01', 'CONFIRME': 'YES', 'adherent': '2;5;6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-01-20', 'CONFIRME': 'YES', 'adherent': '3;4'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-01-20'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity1] 132"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team2 [activity1] 132"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-12-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-02-28")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] 645"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2009-11-30")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team1 [activity1] 645"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-01-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-01-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity1] 489"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-10-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2009-10-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity1] 489"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-10-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-09-30")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity2] 470"])

    def test_import(self):
        csv_content = """'nom','prenom','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','NumLicence','Equipe','Activite'
'USIF','Pierre','Homme','37 avenue de la plage','99673','TOUINTOUIN','0502851031','0439423854','pierre572@free.fr','12/09/1961','BIDON SUR MER','Annually','1000029-00099','team1','activity1'
'NOJAXU','Amandine','Femme','11 avenue du puisatier','99247','BELLEVUE','0022456300','0020055601','amandine723@hotmail.fr','27/02/1976','ZINZIN','Periodic#2','1000030-00099','team2','activity2'
'','',
'GOC','Marie','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Monthly#5','1000031-00099','team3','activity1'
'UHADIK','Marie','Femme','1 impasse de l'Oisan','99410','VIENVITEVOIR','0699821944','0873988470','marie439@orange.fr','27/08/1981','TOUINTOUIN','Calendar#01/11/2009','1000032-00099','team1','activity2'
'FEPIZIBU','Benjamin','Homme','30 cours de la Chartreuse','99247','BELLEVUE','0262009068','0754416670','benjamin475@free.fr','25/03/1979','KIKIMDILUI','Annually','1000033-00099','team2','activity2'
"""
        self.add_subscriptions()
        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 1, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 6 + 17)
        self.assert_select_equal('fld_city', 15)  # nb=15
        self.assert_select_equal('fld_country', 16)  # nb=16
        self.assert_count_equal('CSV', 6)
        self.assert_count_equal('#CSV/actions', 0)
        self.assertEqual(len(self.json_actions), 3)
        self.assert_action_equal(self.json_actions[0], (six.text_type('Retour'), 'images/left.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '0'}))
        self.assert_action_equal(self.json_actions[1], (six.text_type('Ok'), 'images/ok.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '2'}))
        self.assertEqual(len(self.json_context), 8)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 4)
        self.assert_count_equal('CSV', 6)
        self.assert_count_equal('#CSV/actions', 0)
        self.assertEqual(len(self.json_actions), 3)
        self.assert_action_equal(self.json_actions[1], (six.text_type('Ok'), 'images/ok.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '3'}))

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 2)
        self.assert_json_equal('LABELFORM', 'result', "5 éléments ont été importés")
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 7}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'lastname', "USIF")
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] 1000029-00099"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 8}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'lastname', "NOJAXU")
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-12-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-02-28")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] 1000030-00099"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 9}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'lastname', "GOC")
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-01-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-01-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity1] 1000031-00099"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'lastname', "UHADIK")
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-11-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-10-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity2] 1000032-00099"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 11}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'lastname', "FEPIZIBU")
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] 1000033-00099"])

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 8)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 10)

    def test_status_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'status': 1, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_grid_equal('license', {'team': "group", 'activity': "passion", 'value': "N° licence"}, 1)
        self.assert_json_equal('', 'license/@0/team', "team2")
        self.assert_json_equal('', 'license/@0/activity', "activity1")
        self.assert_json_equal('', 'license/@0/value', "abc123")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

        self.factory.xfer = SubscriptionTransition()
        self.calljson('/diacamma.member/subscriptionTransition', {'CONFIRME': 'YES', 'subscription': 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTransition')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 2)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

    def test_valid_bill_of_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'status': 1, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_grid_equal('license', {'team': "group", 'activity': "passion", 'value': "N° licence"}, 1)
        self.assert_json_equal('', 'license/@0/team', "team2")
        self.assert_json_equal('', 'license/@0/activity', "activity1")
        self.assert_json_equal('', 'license/@0/value', "abc123")

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = BillAddModify()
        self.calljson('/diacamma.invoice/billAddModify',
                      {'bill': 1, 'date': '2015-04-01', 'SAVE': 'YES'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.invoice', 'billAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition',
                      {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = BillFromQuotation()
        self.calljson('/diacamma.invoice/billFromQuotation',
                      {'CONFIRME': 'YES', 'bill': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billFromQuotation')
        self.assertEqual(self.response_json['action']['id'], "diacamma.invoice/billShow")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['bill'], 2)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 2)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

    def test_command(self):
        from lucterios.mailing.test_tools import configSMTP, TestReceiver, decode_b64
        Season.objects.get(id=16).set_has_actif()
        self.add_subscriptions(year=2014, season_id=15)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@2/id', "6")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 0)

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2;5;6'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 3)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/team', "team2")
        self.assert_json_equal('', 'AdhCmd/@0/activity', "activity1")
        self.assert_json_equal('', 'AdhCmd/@0/reduce', 0.00)
        self.assert_json_equal('', 'AdhCmd/@1/adherent', "Dalton Joe")
        self.assert_json_equal('', 'AdhCmd/@1/type', "Calendar [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@1/team', "team3")
        self.assert_json_equal('', 'AdhCmd/@1/activity', "activity2")
        self.assert_json_equal('', 'AdhCmd/@1/reduce', 0.00)
        self.assert_json_equal('', 'AdhCmd/@2/adherent', "Luke Lucky")
        self.assert_json_equal('', 'AdhCmd/@2/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@2/team', "team1")
        self.assert_json_equal('', 'AdhCmd/@2/activity', "activity2")
        self.assert_json_equal('', 'AdhCmd/@2/reduce', 0.00)
        cmd_file = self.json_context["CMD_FILE"]
        self.assertEqual(cmd_file[-23:], '/tmp/list-anonymous.cmd')
        self.assertTrue(isfile(cmd_file))

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 3)

        self.factory.xfer = AdherentCommandDelete()
        self.calljson('/diacamma.member/adherentCommandDelete', {'dateref': '2010-10-01', 'CMD_FILE': cmd_file, 'AdhCmd': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentCommandDelete')

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 2)

        self.factory.xfer = AdherentCommandModify()
        self.calljson('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file, 'AdhCmd': '5'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommandModify')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', 'Dalton Joe')

        self.factory.xfer = AdherentCommandModify()
        self.calljson('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file,
                                                                 'AdhCmd': '5', 'type': '3', 'team': '2', 'activity': '1', 'reduce': '7.5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentCommandModify')

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 2)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Joe")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Monthly [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/team', "team2")
        self.assert_json_equal('', 'AdhCmd/@0/activity', "activity1")
        self.assert_json_equal('', 'AdhCmd/@0/reduce', 7.50)
        self.assert_json_equal('', 'AdhCmd/@1/adherent', "Luke Lucky")
        self.assert_json_equal('', 'AdhCmd/@1/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@1/team', "team1")
        self.assert_json_equal('', 'AdhCmd/@1/activity', "activity2")
        self.assert_json_equal('', 'AdhCmd/@1/reduce', 0.00)

        configSMTP('localhost', 2025)
        change_ourdetail()
        server = TestReceiver()
        server.start(2025)
        try:
            self.assertEqual(0, server.count())

            self.factory.xfer = AdherentCommand()
            self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file, 'send_email': True}, False)
            self.assert_observer('core.dialogbox', 'diacamma.member', 'adherentCommand')

            self.assertEqual(2, server.count())
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(0)[1])
            self.assertEqual(['Joe.Dalton@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(0)[2])
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(1)[1])
            self.assertEqual(['Lucky.Luke@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(1)[2])
            msg, msg_txt, msg_file = server.check_first_message('Nouvelle cotisation', 3, {'To': 'Joe.Dalton@worldcompany.com'})
            self.assertEqual('text/plain', msg_txt.get_content_type())
            self.assertEqual('text/html', msg.get_content_type())
            self.assertEqual('base64', msg.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg.get_payload())
            self.assertTrue('Bienvenu' in message, message)
            self.assertTrue('devis_A-1_Dalton Joe.pdf' in msg_file.get('Content-Type', ''), msg_file.get('Content-Type', ''))
            self.save_pdf(base64_content=msg_file.get_payload())
        finally:
            server.stop()

    def test_subscription_with_prestation(self):
        default_adherents()
        default_subscription()
        default_prestation()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_grid_equal('subscription', {'status': "status", 'season': "saison", 'subscriptiontype': "type de cotisation", 'begin_date': "date de début", 'end_date': "date de fin", 'involvement': "participation"}, 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('', 7)
        self.assert_select_equal('season', 20)  # nb=20
        self.assert_select_equal('subscriptiontype', {1: "Annually [76,44 €]", 2: "Periodic [76,44 €]", 3: "Monthly [76,44 €]", 4: "Calendar [76,44 €]"})
        self.assert_json_equal('CHECKLIST', 'prestations', [])
        self.assert_count_equal('#prestations/case', 3)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '1;3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1]", "team3 [activity2]"])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team1 [activity1]', 'team3 [activity2]'])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 413.75)

        self.factory.xfer = SubscriptionTransition()
        self.calljson('/diacamma.member/subscriptionTransition', {'CONFIRME': 'YES', 'subscription': 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 413.75)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_grid_equal('license', {'team': "group", 'activity': "passion", 'value': "N° licence"}, 2)
        self.assert_json_equal('', 'license/@0/team', "team1")
        self.assert_json_equal('', 'license/@0/activity', "activity1")
        self.assert_json_equal('', 'license/@0/value', None)
        self.assert_json_equal('', 'license/@1/team', "team3")
        self.assert_json_equal('', 'license/@1/activity', "activity2")
        self.assert_json_equal('', 'license/@1/value', None)

    def test_subscription_with_prestation_direct(self):
        default_adherents()
        default_subscription()
        default_prestation()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 2, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 133.22)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow',
                      {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_grid_equal('license', {'team': "group", 'activity': "passion", 'value': "N° licence"}, 1)
        self.assert_json_equal('', 'license/@0/team', "team2")
        self.assert_json_equal('', 'license/@0/activity', "activity2")
        self.assert_json_equal('', 'license/@0/value', None)

    def test_renew_with_prestation(self):
        default_adherents()
        default_subscription()
        default_prestation()

        # season °10 / Year : 2009
        Season.objects.get(id=10).set_has_actif()
        new_year = FiscalYear.objects.create(begin='2010-01-01', end='2010-12-31', status=0)
        new_year.set_has_actif()
        fill_accounts_fr(new_year)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 2, 'activity': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 1, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_json_equal('LABELFORM', 'info', [])

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'bill': 1, 'TRANSITION': 'valid', 'CONFIRME': 'YES', 'withpayoff': False, 'sendemail': False}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 76.44)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1]", "team2 [activity2]"])

        # season °11 / Year : 2011
        Season.objects.get(id=11).set_has_actif()
        new_year = FiscalYear.objects.create(begin='2011-01-01', end='2011-12-31', status=0)
        new_year.set_has_actif()
        fill_accounts_fr(new_year)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/id', "2")

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-01', 'CONFIRME': 'YES', 'adherent': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1]", "team2 [activity2]"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team1 [activity1]", "team2 [activity2]"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 458.19)
        self.assert_json_equal('', 'bill/@1/status', 1)
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/total', 76.44)

    def test_command_with_prestation(self):
        default_adherents()
        default_subscription()
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 2, 'activity': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 1, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/id', "2")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 1)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/prestations', "team1 [activity1] 324,97 €{[br/]}team2 [activity2] 56,78 €")
        cmd_file = self.json_context["CMD_FILE"]
        self.assertEqual(cmd_file[-23:], '/tmp/list-anonymous.cmd')
        self.assertTrue(isfile(cmd_file))

        self.factory.xfer = AdherentCommandModify()
        self.calljson('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file, 'AdhCmd': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommandModify')
        self.assert_count_equal('', 6)
        self.assert_json_equal('LABELFORM', 'adherent', 'Dalton Avrel')
        self.assert_json_equal('CHECKLIST', 'prestations', ['2', '3'])
        self.assert_count_equal('#prestations/case', 3)

        self.factory.xfer = AdherentCommandModify()
        self.calljson('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file,
                                                                 'AdhCmd': '2', 'type': '1', 'prestations': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentCommandModify')

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 1)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/prestations', "team3 [activity2] 12,34 €")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file, 'send_email': False}, False)
        self.assert_observer('core.dialogbox', 'diacamma.member', 'adherentCommand')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/total', 76.44)

    def test_import_with_prestation(self):
        csv_content = """'nom','prenom','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','Cours'
'Dalton','Avrel','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','avrel.dalton@worldcompany.com','10/02/2000','BIDON SUR MER','Annually','Presta 1'
'Dalton','Joe','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','joe.dalton@worldcompany.com','18/05/1989','BIDON SUR MER','Annually','Presta 2,Presta 3'
'Luke','Lucky','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','lucky.luke@worldcompany.com','04/06/1979','BIDON SUR MER','Annually','Presta 1;Presta 3'
'GOC','Marie','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Annually','Presta 1,Presta 2;Presta 3'
"""
# Avrel    team3 [activity2]
# Joe      team1 [activity1] team2 [activity2]
# Lucky    team1 [activity1] team3 [activity2]
# Marie    team1 [activity1] team2 [activity2]

        default_adherents()
        default_subscription()
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10, 'prestations': '1;3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/license', ["team1 [activity1]", "team3 [activity2]"])
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/total', 413.75)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 1, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 6 + 18)
        self.assert_select_equal('fld_prestations', 14)  # nb=14
        self.assert_count_equal('CSV', 4)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_prestations': 'Cours', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 2)
        self.assert_json_equal('LABELFORM', 'result', "4 éléments ont été importés")
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/license', ["team3 [activity2]"])
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@1/firstname', "Joe")
        self.assert_json_equal('', 'adherent/@1/license', ["team1 [activity1]", "team2 [activity2]"])
        self.assert_json_equal('', 'adherent/@2/id', "7")
        self.assert_json_equal('', 'adherent/@2/firstname', "Marie")
        self.assert_json_equal('', 'adherent/@2/license', ["team1 [activity1]", "team2 [activity2]", "team3 [activity2]"])
        self.assert_json_equal('', 'adherent/@3/id', "6")
        self.assert_json_equal('', 'adherent/@3/firstname', "Lucky")
        self.assert_json_equal('', 'adherent/@3/license', ["team1 [activity1]", "team3 [activity2]"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 4)
        self.assert_json_equal('', 'bill/@0/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@0/total', 88.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34
        self.assert_json_equal('', 'bill/@1/third', "Dalton Joe")
        self.assert_json_equal('', 'bill/@1/total', 458.19)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78 + art3:324.97
        self.assert_json_equal('', 'bill/@2/third', "Luke Lucky")
        self.assert_json_equal('', 'bill/@2/total', 413.75)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art3:324.97
        self.assert_json_equal('', 'bill/@3/third', "GOC Marie")
        self.assert_json_equal('', 'bill/@3/total', 470.53)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + art3:324.97


class AdherentFamilyTest(BaseAdherentTest):

    def setUp(self):
        BaseAdherentTest.setUp(self)
        Parameter.change_value('member-family-type', 3)
        Parameter.change_value("member-fields", "firstname;lastname;tel1;tel2;email;family")
        set_parameters([])

    def test_show_adherent(self):
        self.add_subscriptions()
        self.assertEqual("famille", six.text_type(Params.getobject('member-family-type')))

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 2 + (15 + 2 + 5) + 2 + 5 + 4 + 2)  # header + identity/family/docs + subscription + financial + invoice + grade
        self.assert_json_equal('LABELFORM', 'family', None)
        self.assert_json_equal('', '#famillybtn/action/icon', "/static/lucterios.CORE/images/add.png")

    def test_new_family(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = AdherentFamilyAdd()
        self.calljson('/diacamma.member/adherentFamilyAdd', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentFamilyAdd')
        self.assert_count_equal('', 4)
        self.assert_count_equal('legal_entity', 0)
        self.assert_json_equal('', '#legal_entity/actions/@1/icon', "/static/lucterios.CORE/images/new.png")
        json_values = self.get_json_path('#legal_entity/actions/@1/params').items()
        self.assertEqual(len(json_values), 9)
        params_value = {'adherent': 2}
        for key, val in json_values:
            params_value[key] = val

        self.factory.xfer = AdherentFamilyCreate()
        self.calljson('/diacamma.member/adherentFamilyCreate', params_value, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentFamilyCreate')
        self.assert_json_equal('EDIT', 'name', 'Dalton')

        params_value['SAVE'] = 'YES'
        self.factory.xfer = AdherentFamilyCreate()
        self.calljson('/diacamma.member/adherentFamilyCreate', params_value, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilyCreate')
        self.assertEqual(self.response_json['action']['action'], 'adherentFamilySelect')
        self.assertEqual(self.response_json['action']['params']['legal_entity'], 7)

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'family', "Dalton")
        self.assert_json_equal('', '#famillybtn/action/icon', "/static/lucterios.CORE/images/edit.png")

        self.factory.xfer = LegalEntityShow()
        self.calljson('/lucterios.contacts/legalEntityShow', {'legal_entity': '7'}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'legalEntityShow')
        self.assert_json_equal('LABELFORM', 'name', "Dalton")
        self.assert_json_equal('LABELFORM', 'structure_type', 'famille')
        self.assert_json_equal('LABELFORM', 'address', 'rue de la liberté')
        self.assert_json_equal('LABELFORM', 'postal_code', '97250')
        self.assert_json_equal('LABELFORM', 'city', 'LE PRECHEUR')
        self.assert_json_equal('LABELFORM', 'country', 'MARTINIQUE')
        self.assert_json_equal('LINK', 'email', 'Avrel.Dalton@worldcompany.com')
        self.assert_json_equal('LABELFORM', 'tel2', '02-78-45-12-95')

    def add_family(self):
        myfamily = LegalEntity()
        myfamily.name = "LES DALTONS"
        myfamily.structure_type_id = 3
        myfamily.address = "Place des cocotiers"
        myfamily.postal_code = "97200"
        myfamily.city = "FORT DE FRANCE"
        myfamily.country = "MARTINIQUE"
        myfamily.tel1 = "01-23-45-67-89"
        myfamily.email = "dalton@worldcompany.com"
        myfamily.save()
        return myfamily.id

    def test_select_family(self):
        default_adherents()
        default_subscription()
        self.add_family()

        self.factory.xfer = AdherentFamilyAdd()
        self.calljson('/diacamma.member/adherentFamilyAdd', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentFamilyAdd')
        self.assert_count_equal('legal_entity', 1)
        self.assert_count_equal('#legal_entity/actions', 3)
        self.assert_json_equal('', 'legal_entity/@0/name', "LES DALTONS")

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'family', "LES DALTONS")
        self.assert_json_equal('', '#famillybtn/action/icon', "/static/lucterios.CORE/images/edit.png")

    def test_add_adherent(self):
        default_adherents()
        default_subscription()
        self.add_family()
        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_json_equal('', '#famillybtn/action/icon', "/static/lucterios.CORE/images/add.png")

        self.factory.xfer = FamilyAdherentAdd()
        self.calljson('/diacamma.member/familyAdherentAdd', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'familyAdherentAdd')
        self.assert_count_equal('legal_entity', 1)
        self.assert_count_equal('#legal_entity/actions', 3)
        self.assert_json_equal('', 'legal_entity/@0/name', "LES DALTONS")

        self.factory.xfer = FamilyAdherentCreate()
        self.calljson('/diacamma.member/familyAdherentCreate', {'legal_entity': 7}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'familyAdherentCreate')
        self.assert_json_equal('EDIT', 'lastname', "LES DALTONS")
        self.assert_json_equal('MEMO', 'address', 'Place des cocotiers')

        self.factory.xfer = FamilyAdherentCreate()
        self.calljson('/diacamma.member/familyAdherentCreate', {"address": 'Place des cocotiers',
                                                                "comment": 'no comment', "firstname": "Ma'a", "lastname": 'DALTON',
                                                                "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                                "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'maa.dalton@worldcompany.com',
                                                                "birthday": "1998-08-04", "birthplace": "Fort-de-France",
                                                                "genre": "2", 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'familyAdherentCreate')
        self.assertEqual(self.response_json['action']['params']['adherent'], 8)

        self.factory.xfer = FamilyAdherentAdded()
        self.calljson('/diacamma.member/familyAdherentAdded', {'adherent': 8, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'familyAdherentAdded')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 8}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Ma'a")
        self.assert_json_equal('LABELFORM', 'lastname', "DALTON")
        self.assert_json_equal('LABELFORM', 'family', "LES DALTONS")
        self.assert_json_equal('', '#famillybtn/action/icon', "/static/lucterios.CORE/images/edit.png")

    def test_subscription_bill(self):
        default_adherents()
        default_subscription()
        family_third = get_or_create_customer(self.add_family())

        self.factory.xfer = BillAddModify()
        self.calljson('/diacamma.invoice/billAddModify', {'bill_type': 1, 'third': family_third.id, 'date': '2015-04-01', 'SAVE': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billAddModify')
        self.factory.xfer = DetailAddModify()
        self.calljson('/diacamma.invoice/detailAddModify', {'article': 0, 'designation': 'article 0', 'price': '100.00', 'quantity': 1, 'SAVE': 'YES', 'bill': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'detailAddModify')

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/total', 100.00)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 100.00)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_json_equal('LINK', 'third', "LES DALTONS")
        self.assert_count_equal('detail', 2)
        self.assert_json_equal('', 'detail/@0/article', 'ABC1')
        self.assert_json_equal('', 'detail/@0/designation', "Article 01{[br/]}Cotisation de 'Dalton Avrel'")
        self.assert_json_equal('', 'detail/@0/price', 12.34)
        self.assert_json_equal('', 'detail/@0/quantity', '1.000')
        self.assert_json_equal('', 'detail/@0/total', 12.34)
        self.assert_json_equal('', 'detail/@1/article', 'ABC5')
        self.assert_json_equal('', 'detail/@1/designation', "Article 05{[br/]}Cotisation de 'Dalton Avrel'")
        self.assert_json_equal('', 'detail/@1/price', 64.10)
        self.assert_json_equal('', 'detail/@1/quantity', '1.00')
        self.assert_json_equal('', 'detail/@1/total', 64.10)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 5, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 1, 'activity': 1, 'value': 'uvw98'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/total', 100.00)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/total', 152.88)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}")

    def test_command(self):
        from lucterios.mailing.test_tools import configSMTP, TestReceiver, decode_b64
        Season.objects.get(id=16).set_has_actif()
        self.add_subscriptions(year=2014, season_id=15)
        self.add_family()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@3/bill_type', 1)
        self.assert_json_equal('', 'bill/@4/bill_type', 1)

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@2/id', "6")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 0)

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2;5'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 2)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/reduce', 0.00)
        self.assert_json_equal('', 'AdhCmd/@1/adherent', "Dalton Joe")
        self.assert_json_equal('', 'AdhCmd/@1/type', "Calendar [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@1/reduce', 0.00)
        cmd_file = self.json_context["CMD_FILE"]
        self.assertEqual(cmd_file[-23:], '/tmp/list-anonymous.cmd')
        self.assertTrue(isfile(cmd_file))

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 2)

        configSMTP('localhost', 2025)
        change_ourdetail()
        server = TestReceiver()
        server.start(2025)
        try:
            self.assertEqual(0, server.count())

            self.factory.xfer = AdherentCommand()
            self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file, 'send_email': True}, False)
            self.assert_observer('core.dialogbox', 'diacamma.member', 'adherentCommand')

            self.assertEqual(1, server.count())
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(0)[1])
            self.assertEqual(['dalton@worldcompany.com', 'Avrel.Dalton@worldcompany.com', 'Joe.Dalton@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(0)[2])
            msg, msg_txt, msg_file = server.check_first_message('Nouvelle cotisation', 3, {'To': 'dalton@worldcompany.com'})
            self.assertEqual('text/plain', msg_txt.get_content_type())
            self.assertEqual('text/html', msg.get_content_type())
            self.assertEqual('base64', msg.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg.get_payload())
            self.assertTrue('Bienvenu' in message, message)
            self.assertTrue('devis_A-1_LES DALTONS.pdf' in msg_file.get('Content-Type', ''), msg_file.get('Content-Type', ''))
            self.save_pdf(base64_content=msg_file.get_payload())
        finally:
            server.stop()

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 6)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/num_txt', "A-1")
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 152.88)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}")
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@3/bill_type', 1)
        self.assert_json_equal('', 'bill/@4/bill_type', 1)
        self.assert_json_equal('', 'bill/@5/bill_type', 1)

    def test_import(self):
        csv_content = """"nom","prenom","sexe","famille","adresse","codePostal","ville","fixe","portable","mail","Type"
"Dalton","Avrel","Homme","LES DALTONS","rue de la liberté","99673","TOUINTOUIN","0502851031","0439423854","avrel.dalton@worldcompany.com","Annually"
"Dalton","Joe","Homme","Dalton","rue de la liberté","99673","TOUINTOUIN","0502851031","0439423854","joe.dalton@worldcompany.com","Annually"
"Dalton","Ma'a","Femme","LES DALTONS","rue de la liberté","99673","TOUINTOUIN","0502851031","0439423854","maa.dalton@worldcompany.com","Annually"
"Luke","Lucky","Homme","Luke","rue de la liberté","99673","TOUINTOUIN","0502851031","0439423854","lucky.luke@worldcompany.com","Annually"
"GOC","Marie","Femme","","33 impasse du 11 novembre","99150","BIDON SUR MER","0632763718","0310231012","marie762@free.fr","Annually"
"UHADIK","Jeanne","Femme","UHADIK-FEPIZIBU","1 impasse de l"Oisan","99410","VIENVITEVOIR","0699821944","0873988470","marie439@orange.fr","Annually"
"FEPIZIBU","Benjamin","Homme","UHADIK-FEPIZIBU","30 cours de la Chartreuse","99247","BELLEVUE","0262009068","0754416670","benjamin475@free.fr","Annually"
"""
        default_adherents()
        default_subscription()
        self.add_family()
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)
        self.assertEqual(len(self.json_actions), 4)

        self.assertEqual(1, LegalEntity.objects.filter(structure_type_id=3).count())

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 1, 'modelname': 'member.Adherent', 'quotechar': '"',
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 6 + 13)
        self.assert_select_equal('fld_family', 12)
        self.assert_count_equal('CSV', 7)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': '"', 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            'fld_subscriptiontype': 'Type', 'fld_family': 'famille', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 2)
        self.assert_json_equal('LABELFORM', 'result', "7 éléments ont été importés")
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 7)
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/family', "LES DALTONS")
        self.assert_json_equal('', 'adherent/@1/firstname', "Joe")
        self.assert_json_equal('', 'adherent/@1/family', "Dalton")
        self.assert_json_equal('', 'adherent/@2/firstname', "Ma'a")
        self.assert_json_equal('', 'adherent/@2/family', "LES DALTONS")
        self.assert_json_equal('', 'adherent/@3/firstname', "Benjamin")
        self.assert_json_equal('', 'adherent/@3/family', "UHADIK-FEPIZIBU")
        self.assert_json_equal('', 'adherent/@4/firstname', "Marie")
        self.assert_json_equal('', 'adherent/@4/family', None)
        self.assert_json_equal('', 'adherent/@5/firstname', "Lucky")
        self.assert_json_equal('', 'adherent/@5/family', "Luke")
        self.assert_json_equal('', 'adherent/@6/firstname', "Jeanne")
        self.assert_json_equal('', 'adherent/@6/family', "UHADIK-FEPIZIBU")

        self.assertEqual(4, LegalEntity.objects.filter(structure_type_id=3).count())

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/total', 152.88)  # Subscription: art1:12.34 + art5:64.10 x 2
        self.assert_json_equal('', 'bill/@1/third', "Dalton")
        self.assert_json_equal('', 'bill/@1/total', 76.44)  # Subscription: art1:12.34 + art5:64.10
        self.assert_json_equal('', 'bill/@2/third', "Luke")
        self.assert_json_equal('', 'bill/@2/total', 76.44)  # Subscription: art1:12.34 + art5:64.10
        self.assert_json_equal('', 'bill/@3/third', "GOC Marie")
        self.assert_json_equal('', 'bill/@3/total', 76.44)  # Subscription: art1:12.34 + art5:64.10
        self.assert_json_equal('', 'bill/@4/third', "UHADIK-FEPIZIBU")
        self.assert_json_equal('', 'bill/@4/total', 152.88)  # Subscription: art1:12.34 + art5:64.10 x 2

        self.factory.xfer = AdherentThirdList()
        self.calljson('/diacamma.member/adherentThirdList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentThirdList')
        self.assert_count_equal('third', 5)
        self.assert_json_equal('', 'third/@0/contact', "Dalton")
        self.assert_json_equal('', 'third/@0/adherents', ["Dalton Joe"])
        self.assert_json_equal('', 'third/@1/contact', "GOC Marie")
        self.assert_json_equal('', 'third/@1/adherents', ["GOC Marie"])
        self.assert_json_equal('', 'third/@2/contact', "LES DALTONS")
        self.assert_json_equal('', 'third/@2/adherents', ["Dalton Avrel", "Dalton Ma'a"])
        self.assert_json_equal('', 'third/@3/contact', "Luke")
        self.assert_json_equal('', 'third/@3/adherents', ["Luke Lucky"])
        self.assert_json_equal('', 'third/@4/contact', "UHADIK-FEPIZIBU")
        self.assert_json_equal('', 'third/@4/adherents', ["FEPIZIBU Benjamin", "UHADIK Jeanne"])

    def test_import_with_prestation(self):
        csv_content = """'nom','prenom','famille','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','Cours'
'Dalton','Avrel','Dalton','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','avrel.dalton@worldcompany.com','10/02/2000','BIDON SUR MER','Annually','Presta 1'
'Dalton','Joe','Dalton','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','joe.dalton@worldcompany.com','18/05/1989','BIDON SUR MER','Annually','Presta 2,Presta 3'
'Luke','Lucky','Luke','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','lucky.luke@worldcompany.com','04/06/1979','BIDON SUR MER','Annually','Presta 1;Presta 3'
'GOC','Marie','','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Annually','Presta 1,Presta 2;Presta 3'
"""
# Avrel    team3 [activity2]
# Joe      team1 [activity1] team2 [activity2]
# Lucky    team1 [activity1] team3 [activity2]
# Marie    team1 [activity1] team2 [activity2]

        Parameter.change_value("member-fields", "firstname;lastname;tel1;tel2;email;family;license")
        set_parameters(["team", "licence"])
        default_adherents()
        default_subscription()
        default_prestation()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 0)
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 1, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 6 + 16)
        self.assert_select_equal('fld_family', 15)
        self.assert_select_equal('fld_prestations', 15)
        self.assert_count_equal('CSV', 4)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_family": "famille", "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            'fld_subscriptiontype': 'Type', 'fld_prestations': 'Cours', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 2)
        self.assert_json_equal('LABELFORM', 'result', "4 éléments ont été importés")
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/family', "Dalton")
        self.assert_json_equal('', 'adherent/@0/license', ["team3"])
        self.assert_json_equal('', 'adherent/@1/firstname', "Joe")
        self.assert_json_equal('', 'adherent/@1/family', "Dalton")
        self.assert_json_equal('', 'adherent/@1/license', ["team1", "team2"])
        self.assert_json_equal('', 'adherent/@2/firstname', "Marie")
        self.assert_json_equal('', 'adherent/@2/family', None)
        self.assert_json_equal('', 'adherent/@2/license', ["team1", "team2", "team3"])
        self.assert_json_equal('', 'adherent/@3/firstname', "Lucky")
        self.assert_json_equal('', 'adherent/@3/family', "Luke")
        self.assert_json_equal('', 'adherent/@3/license', ["team1", "team3"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 3)
        self.assert_json_equal('', 'bill/@0/third', "Dalton")
        self.assert_json_equal('', 'bill/@0/total', 546.97)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78 + art3:324.97
        self.assert_json_equal('', 'bill/@1/third', "Luke")
        self.assert_json_equal('', 'bill/@1/total', 413.75)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art3:324.97
        self.assert_json_equal('', 'bill/@2/third', "GOC Marie")
        self.assert_json_equal('', 'bill/@2/total', 470.53)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + art3:324.97
