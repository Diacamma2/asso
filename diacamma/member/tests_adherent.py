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
from datetime import date, timedelta
from _io import StringIO

from os.path import isfile
from base64 import b64decode

from django.conf import settings

from lucterios.framework.test import LucteriosTest
from lucterios.framework.filetools import get_user_dir
from lucterios.CORE.models import Parameter, LucteriosUser, LucteriosGroup, SavedCriteria
from lucterios.CORE.parameters import Params
from lucterios.CORE.views import ObjectMerge
from lucterios.contacts.views_contacts import LegalEntityShow
from lucterios.contacts.models import LegalEntity, Responsability
from lucterios.contacts.views import ContactImport
from lucterios.contacts.test_tools import change_ourdetail
from lucterios.mailing.test_tools import configSMTP, TestReceiver, decode_b64
from lucterios.documents.models import DocumentContainer

from diacamma.accounting.views import ThirdShow
from diacamma.accounting.models import FiscalYear
from diacamma.accounting.test_tools import fill_accounts_fr, create_account, add_entry
from diacamma.accounting.views_entries import EntryAccountList, EntryAccountClose, EntryAccountLink
from diacamma.invoice.views import BillList, BillTransition, BillToBill, BillAddModify, BillShow, DetailAddModify
from diacamma.invoice.models import get_or_create_customer, Article, AccountPosting, \
    CategoryBill
from diacamma.invoice.test_tools import InvoiceTest, default_categorybill
from diacamma.payoff.views import PayoffAddModify
from diacamma.payoff.test_tools import check_pdfreport, default_paymentmethod

from diacamma.member.models import Season, Adherent, SubscriptionType, \
    Prestation, Subscription, Team
from diacamma.member.views import AdherentActiveList, AdherentAddModify, AdherentShow, \
    SubscriptionAddModify, SubscriptionShow, LicenseAddModify, LicenseDel, \
    AdherentDoc, AdherentLicense, AdherentLicenseSave, AdherentStatistic, \
    AdherentRenewList, AdherentRenew, SubscriptionTransition, AdherentCommand, \
    AdherentCommandDelete, AdherentCommandModify, AdherentFamilyAdd, \
    AdherentFamilySelect, AdherentFamilyCreate, FamilyAdherentAdd, \
    FamilyAdherentCreate, FamilyAdherentAdded, AdherentListing, \
    AdherentContactList, AdherentConnection, SubscriptionDel, AdherentDisableConnection, \
    AdherentPrint, PrestationList, PrestationDel, PrestationAddModify, \
    PrestationShow, AdherentPrestationAdd, AdherentPrestationSave, \
    AdherentPrestationDel, PrestationSwap, PrestationSplit, \
    PrestationPriceAddModify, PrestationPriceDel, AdherentSendSubscription, \
    AdherentLabel, SubscriptionAddForCurrent, SubscriptionConfirmCurrent
from diacamma.member.test_tools import default_season, default_financial, default_params, \
    default_adherents, default_subscription, set_parameters, default_prestation, create_adherent
from diacamma.member.views_conf import TaxReceiptList, TaxReceiptCheck, TaxReceiptShow, TaxReceiptPrint, CategoryConf, TaxReceiptCheckOnlyOn, TaxReceiptValid


class BaseAdherentTest(LucteriosTest):

    def __init__(self, methodName):
        LucteriosTest.__init__(self, methodName)
        if date.today().month > 8:
            self.dateref_expected = date(
                2009, date.today().month, date.today().day)
        else:
            self.dateref_expected = date(
                2010, date.today().month, date.today().day)
        self.is_dates_beginsept = (self.dateref_expected.isoformat() >= '2009-09-01') and (self.dateref_expected.isoformat() < '2009-09-15')

    def setUp(self):
        settings.LOGIN_FIELD = 'username'
        settings.ASK_LOGIN_EMAIL = False
        settings.USER_READONLY = False
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()
        default_categorybill()

    def add_subscriptions(self, year=2009, season_id=10, status=2, create_adh_sub=True):
        if create_adh_sub:
            default_adherents()
            default_subscription()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'status': status, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 3, 'status': status, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 2, 'period': 37 + (year - 2009) * 4, 'season': season_id, 'team': 1, 'activity': 1, 'value': '645'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 4, 'status': status, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 3, 'month': '%s-10' % year, 'season': season_id, 'team': 3, 'activity': 1, 'value': '489'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': status, 'dateref': '%s-10-01' % year,
                                                                 'subscriptiontype': 4, 'begin_date': '%s-09-15' % year, 'season': season_id, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 6, 'status': status, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 1, 'activity': 2, 'value': '159'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

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

    def prep_family(self):
        default_adherents()
        default_subscription(True)
        family_id = self.add_family()
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': family_id}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': family_id}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

    def prep_subscription_family(self):
        self.prep_family()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 1, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 1, 'adherent': 5, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'bill': 1, 'TRANSITION': 'valid', 'CONFIRME': 'YES', 'withpayoff': False, 'sendemail': False}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44 + 76.44)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}")


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
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 3 + (18 + 1) + 2 + 2)  # header + identity + subscription + grade
        self.assert_json_equal('LABELFORM', 'dateref', self.dateref_expected.isoformat(), True)
        self.assert_json_equal('LABELFORM', 'firstname', "Marie")
        self.assert_json_equal('LABELFORM', 'lastname', "DUPOND")
        self.assert_json_equal('LABELFORM', 'num', "1")
        self.assert_json_equal('LABELFORM', 'birthday', "1998-08-04")
        self.assert_json_equal('LABELFORM', 'birthplace', "Fort-de-France")
        self.assert_json_equal('LABELFORM', 'age_category', "Benjamins")
        self.assert_json_equal('LABELFORM', 'user', None)
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
        self.assert_json_equal('LABELFORM', 'user', None)

    def test_add_adherent_with_connexion(self):
        Parameter.change_value('member-connection', 1)
        Parameter.change_value('contacts-createaccount', 1)
        Params.clear()
        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {"address": 'Avenue de la Paix{[newline]}BP 987',
                                                             "comment": 'no comment', "firstname": 'Marie', "lastname": 'DUPOND',
                                                             "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                             "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'marie.dupond@worldcompany.com',
                                                             "birthday": "1998-08-04", "birthplace": "Fort-de-France",
                                                             "genre": "2"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 3 + (18 + 2) + 2 + 2)  # header + identity + subscription + grade
        self.assert_json_equal('LABELFORM', 'dateref', self.dateref_expected.isoformat(), True)
        self.assert_json_equal('LABELFORM', 'firstname', "Marie")
        self.assert_json_equal('LABELFORM', 'lastname', "DUPOND")
        self.assert_json_equal('LABELFORM', 'num', "1")
        self.assert_json_equal('LABELFORM', 'birthday', "1998-08-04")
        self.assert_json_equal('LABELFORM', 'birthplace', "Fort-de-France")
        self.assert_json_equal('LABELFORM', 'age_category', "Benjamins")
        self.assert_json_equal('LABELFORM', 'user', 'marieD')

    def test_add_subscription(self):
        default_adherents()

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_grid_equal('subscription', {'status': "statut", 'season': "saison", 'subscriptiontype': "type de cotisation", 'begin_date': "date de début", 'end_date': "date de fin", 'involvement': "participation"}, 0)

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
        self.assert_json_equal('SELECT', 'status', '1')
        self.assert_json_equal('SELECT', 'subscriptiontype', '1')
        self.assert_json_equal('LABELFORM', 'seasondates', "1 sept. 2009 => 31 août 2010")

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

    def test_adherent_print_pdf(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = AdherentPrint()
        self.calljson('/diacamma.member/adherentPrint', {'adherent': 2, 'dateref': '2014-10-01', "PRINT_MODE": 3}, False)
        self.assert_observer('core.print', 'diacamma.member', 'adherentPrint')
        self.save_pdf()

    def test_adherent_print_ods(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = AdherentPrint()
        self.calljson('/diacamma.member/adherentPrint', {'adherent': 2, 'dateref': '2014-10-01', "PRINT_MODE": 2}, False)
        self.assert_observer('core.print', 'diacamma.member', 'adherentPrint')
        self.save_ods()

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
        self.assert_json_equal('', 'bill/@0/billtype', 'facture')
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

    def test_subscription_noteam(self):
        default_adherents()
        default_subscription()
        Team.objects.all().delete()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'adherent': 2, 'status': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'subscriptionAddModify')
        self.assert_json_equal('', "message", "Pas d'équipe actif par défaut définie !")

    def test_subscription_doc(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_count_equal('', 3 + (19 + 5) + 2 + 6 + 5 + 2)  # header + identity/docs + subscription + financial + invoice + grade
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
        self.assert_count_equal('', 3 + (15 + 5) + 2 + 6 + 5 + 2)  # header + identity + subscription + financial + invoice + grade
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
        csv_value = b64decode(str(self.response_json['print']['content'])).decode("utf-8")
        content_csv = csv_value.split('\n')
        self.assertEqual(len(content_csv), 13, str(content_csv))
        self.assertEqual(content_csv[1].strip(), '"Adhérents cotisants - date de référence : 1 octobre 2009"')
        self.assertEqual(content_csv[4].strip(), '"statut : en création & validé,,passion : activity2,,group : team2,team3,,Âge : Minimes,Benjamins,Poussins,,genre : Femme"', str(content_csv))
        self.assertEqual(content_csv[6].strip(), '"nom";"adresse";"ville";"tel";"courriel";', str(content_csv))

    def test_subscription_printlabel(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01', 'age': '1;2;3', 'team': '2;3', 'activity': '2', 'genre': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')

        new_context = dict(self.json_context)
        new_context['PRINT_MODE'] = 3
        new_context['LABEL'] = 1
        new_context['FIRSTLABEL'] = 1
        self.factory.xfer = AdherentLabel()
        self.calljson('/diacamma.member/adherentLabel', new_context, False)
        self.assert_observer('core.print', 'diacamma.member', 'adherentLabel')

    def test_statistic_18(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('', 4)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_grid_equal('town_1', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<18)', 'MinM': 'jeune homme (<18)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')
        self.assert_grid_equal('town_2', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<18)', 'MinM': 'jeune homme (<18)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_2/@1/ratio', '{[b]}1{[/b]}')
        self.assert_count_equal('seniority_1', 1)
        self.assert_count_equal('team_1', 2)
        self.assert_count_equal('activity_1', 2)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01', 'only_valid': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_grid_equal('town_1', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<18)', 'MinM': 'jeune homme (<18)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')
        self.assert_grid_equal('town_2', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<18)', 'MinM': 'jeune homme (<18)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_2/@1/ratio', '{[b]}1{[/b]}')
        self.assert_count_equal('seniority_1', 1)
        self.assert_count_equal('team_1', 2)
        self.assert_count_equal('activity_1', 2)

    def test_statistic_05(self):
        self.add_subscriptions()
        Params.setvalue("member-age-statistic", 5)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('', 4)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_grid_equal('town_1', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<5)', 'MinM': 'jeune homme (<5)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_1/@1/MajW', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MajM', '{[b]}2{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MinW', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MinM', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')

    def test_statistic_50(self):
        self.add_subscriptions()
        Params.setvalue("member-age-statistic", 50)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('', 4)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_grid_equal('town_1', {'city': 'ville', 'MajW': 'femme adulte', 'MajM': 'homme adulte', 'MinW': 'jeune femme (<50)', 'MinM': 'jeune homme (<50)', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_1/@1/MajW', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MajM', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MinW', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/MinM', '{[b]}2{[/b]}')
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')

    def test_statistic_noage(self):
        self.add_subscriptions()
        Params.setvalue("member-birth", 0)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('', 4)

        self.factory.xfer = AdherentStatistic()
        self.calljson('/diacamma.member/adherentStatistic', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentStatistic')

        self.assertEqual(0, (len(self.json_data) - 3 - 6) % 5, "size of COMPONENTS/* = %d" % len(self.json_data))
        self.assert_grid_equal('town_1', {'city': 'ville', 'Woman': 'femme', 'Man': 'homme', 'ratio': 'total (%)'}, 2)
        self.assert_json_equal('', 'town_1/@1/Woman', '{[b]}0{[/b]}')
        self.assert_json_equal('', 'town_1/@1/Man', '{[b]}2{[/b]}')
        self.assert_json_equal('', 'town_1/@1/ratio', '{[b]}2{[/b]}')

    def test_renew(self):
        configSMTP('localhost', 1125)
        change_ourdetail()
        self.add_subscriptions()

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-01-20', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 2)
        self.assert_json_equal('', 'adherent/@0/id', "4")
        self.assert_json_equal('', 'adherent/@1/id', "3")

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-01', 'CONFIRME': 'YES', 'adherent': '2;5;6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')
        self.assertEqual(self.response_json['action']['id'], "diacamma.member/adherentSendSubscription")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['adherent'], '2;5;6')

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-01-20', 'CONFIRME': 'YES', 'adherent': '3;4'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')
        self.assertEqual(self.response_json['action']['id'], "diacamma.member/adherentSendSubscription")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['adherent'], '3;4')

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-01-20', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 0)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay': 0, 'reminder': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-01-20', 'enddate_delay': 0, 'reminder': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 2)
        self.assert_json_equal('', 'adherent/@0/id', "4")
        self.assert_json_equal('', 'adherent/@1/id', "3")

        self.factory.xfer = AdherentSendSubscription()
        self.calljson('/diacamma.member/adherentSendSubscription', {'dateref': '2010-01-20', 'adherent': '3;4'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentSendSubscription')
        self.assert_select_equal('send_mode', {1: "Envoyer par courriel", 2: "Imprimer le devis"})

        self.factory.xfer = AdherentSendSubscription()
        self.calljson('/diacamma.member/adherentSendSubscription', {'dateref': '2010-01-20', 'adherent': '3;4', 'send_mode': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentSendSubscription')
        self.assertEqual(self.response_json['action']['id'], "diacamma.invoice/billPayableEmail")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['bill'], '9;10')

        self.factory.xfer = AdherentSendSubscription()
        self.calljson('/diacamma.member/adherentSendSubscription', {'dateref': '2010-01-20', 'adherent': '3;4', 'send_mode': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentSendSubscription')
        self.assertEqual(self.response_json['action']['id'], "diacamma.invoice/billPrint")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['bill'], '9;10')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity1] 132"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team2 [activity1] 132"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-12-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-02-28")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] 645"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Periodic")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2009-11-30")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team1 [activity1] 645"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-01-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-01-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity1] 489"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Monthly")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-10-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2009-10-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity1] 489"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-10-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-09-30")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity2] 470"])

    def test_renew_filtered(self):
        change_ourdetail()
        self.add_subscriptions()
        crit = SavedCriteria.objects.create(name="only", modelname=Adherent.get_long_name(), criteria="lastname||5||Dalton")

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('', 7)
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        Params.setvalue('member-renew-filter', crit.id)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'savecritera_renew', '{[b]}nom{[/b]} contenu {[i]}"Dalton"{[/i]}')
        self.assert_count_equal('adherent', 2)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "5")

    def test_renew_withdelay_tolow(self):
        configSMTP('localhost', 1125)
        change_ourdetail()
        self.add_subscriptions()
        Parameter.change_value('member-subscription-delaytorenew', 50)

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-11-01', 'CONFIRME': 'YES', 'adherent': '5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-15")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-09-14")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity2] 470"])

    def test_renew_withdelay_tohigh(self):
        configSMTP('localhost', 1125)
        change_ourdetail()
        self.add_subscriptions()
        Parameter.change_value('member-subscription-delaytorenew', 50)

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2011-03-20', 'CONFIRME': 'YES', 'adherent': '5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2011-03-20")
        self.assert_json_equal('', 'subscription/@0/end_date', "2012-03-19")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/status', 2)
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity2] 470"])

    def test_renew_disabled(self):
        self.add_subscriptions()
        sub1 = SubscriptionType.objects.get(name="Annually")
        sub1.state = SubscriptionType.STATE_UNACTIVATE
        sub1.save()
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2, 'type_filter':-1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-23', 'CONFIRME': 'YES', 'adherent': '2'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'adherentRenew')
        self.assert_json_equal('', "message", "Aucun type de cotisation actif !")

        sub_new = SubscriptionType.objects.create(name="New Annually", description="AAA+", duration=0, order_key=7)
        sub_new.articles.set(Article.objects.filter(id__in=(1, 5)))
        sub_new.save()

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-23', 'CONFIRME': 'YES', 'adherent': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-23', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 2)
        self.assert_json_equal('', 'adherent/@0/id', "6")
        self.assert_json_equal('', 'adherent/@1/id', "5")

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "New Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity1] 132"])
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team2 [activity1] 132"])
        self.assert_json_equal('', 'subscription/@1/status', 2)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2, 'type_filter':-1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 6)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/billtype', 'devis')
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}{[br/]}Cotisation de 'Dalton Avrel'")
        self.assert_json_equal('', 'bill/@0/date', '2011-08-31')
        self.assert_json_equal('', 'bill/@0/total', 76.44)

    def test_renew_calendar(self):
        self.add_subscriptions()
        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@0/status', 2)

        self.factory.xfer = AdherentRenew()
        self.calljson('/diacamma.member/adherentRenew', {'dateref': '2010-10-23', 'CONFIRME': 'YES', 'adherent': '5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 2)
        self.assert_json_equal('', 'subscription/@0/season', "2010/2011")
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-10-23")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-10-22")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@1/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@1/subscriptiontype', "Calendar")
        self.assert_json_equal('', 'subscription/@1/begin_date', "2009-09-15")
        self.assert_json_equal('', 'subscription/@1/end_date', "2010-09-14")
        self.assert_json_equal('', 'subscription/@1/involvement', ["team3 [activity2] 470"])
        self.assert_json_equal('', 'subscription/@1/status', 2)

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
        self.calljson('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 7 + 17)
        self.assert_select_equal('fld_city', 15)  # nb=15
        self.assert_select_equal('fld_country', 16)  # nb=16
        self.assert_count_equal('Array', 6)
        self.assert_count_equal('#Array/actions', 0)
        self.assertEqual(len(self.json_actions), 1)
        self.assertEqual(len(self.json_context), 8)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 5)
        self.assert_count_equal('Array', 6)
        self.assert_count_equal('#Array/actions', 0)
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "5 éléments ont été importés")
        self.assert_json_equal('LABELFORM', 'import_error', [])
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

    def test_bad_import(self):
        csv_content = """'nom','prenom','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','NumLicence','Equipe','Activite'
'USIF','Pierre','Homme','37 avenue de la plage','99673','TOUINTOUIN','0502851031','0439423854','pierre572@free.fr','12/09/1961','BIDON SUR MER','Annua','1000029-00099','team1','activity1'
'NOJAXU','Amandine','Femme','11 avenue du puisatier','99247','BELLEVUE','0022456300','0020055601','amandine723@hotmail.fr','27/02/1976','ZINZIN','Periodic#2','1000030-00099','team7','activity2'
'','',
'GOC','Marie','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Monthly#5','1000031-00099','team3','activity8'
"""
        self.add_subscriptions()
        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 3)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "3 éléments ont été importés")
        self.assert_json_equal('LABELFORM', 'import_error', ["Type de cotisation 'Annua' inconnue !", "group 'team7' inconnu(e) !", "passion 'activity8' inconnu(e) !"])
        self.assertEqual(len(self.json_actions), 1)

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
        cat1 = CategoryBill.objects.get(id=1)
        cat1.change_has_default()

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
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/billtype', 'QQQ')
        self.assert_json_equal('', 'bill/@0/total', 76.44)

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition',
                      {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = BillToBill()
        self.calljson('/diacamma.invoice/billToBill',
                      {'CONFIRME': 'YES', 'bill': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billToBill')
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
        self.assert_json_equal('', 'bill/@0/billtype', 'BBB')
        self.assert_json_equal('', 'bill/@0/total', 76.44)

    def test_command(self):
        Season.objects.get(id=16).set_has_actif()
        self.add_subscriptions(year=2014, season_id=15)

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

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

        configSMTP('localhost', AdherentConnectionTest.smtp_port)
        change_ourdetail()
        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
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
            msg_txt, msg, msg_file = server.check_first_message('Nouvelle cotisation', 3, {'To': 'Joe.Dalton@worldcompany.com'})
            self.assertEqual('text/plain', msg_txt.get_content_type())
            self.assertEqual('text/html', msg.get_content_type())
            self.assertEqual('base64', msg.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg.get_payload())
            self.assertTrue('Bienvenu' in message, message)
            self.assertTrue('devis_A-1_Dalton Joe.pdf' in msg_file.get('Content-Type', ''), msg_file.get('Content-Type', ''))
            self.save_pdf(base64_content=msg_file.get_payload())
        finally:
            server.stop()

    def test_command_disabled(self):
        Season.objects.get(id=16).set_has_actif()
        self.add_subscriptions(year=2014, season_id=15)
        sub1 = SubscriptionType.objects.get(name="Annually")
        sub1.state = SubscriptionType.STATE_UNACTIVATE
        sub1.save()

        self.factory.xfer = AdherentRenewList()
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'adherentCommand')
        self.assert_json_equal('', "message", "Aucun type de cotisation actif !")

        sub_new = SubscriptionType.objects.create(name="New Annually", description="AAA+", duration=0, order_key=7)
        sub_new.articles.set(Article.objects.filter(id__in=(1, 5)))
        sub_new.save()

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 1)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "New Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/team', "team2")
        self.assert_json_equal('', 'AdhCmd/@0/activity', "activity1")
        self.assert_json_equal('', 'AdhCmd/@0/reduce', 0.00)

    def test_subscription_with_prestation(self):
        default_adherents()
        default_subscription()
        default_prestation()
        Parameter.change_value('member-default-categorybill', 2)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_grid_equal('subscription', {'status': "statut", 'season': "saison", 'subscriptiontype': "type de cotisation", 'begin_date': "date de début", 'end_date': "date de fin", 'involvement': "participation"}, 0)

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
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 [activity2] (12,34 €)', 'team1 [activity1] (324,97 €)'])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/billtype', 'Type Q')
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
        self.assert_json_equal('', 'bill/@0/billtype', 'Type B')
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
        accpost = AccountPosting.objects.get(sell_account="601")
        accpost.sell_account = "701"
        accpost.save()

        # season °10 / Year : 2009
        Season.objects.get(id=10).set_has_actif()
        new_year = FiscalYear.objects.create(begin='2010-01-01', end='2010-12-31', status=0)
        new_year.set_has_actif()
        fill_accounts_fr(new_year)

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'status': 2, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 2, 'activity': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')
        self.factory.xfer = LicenseAddModify()
        self.calljson('/diacamma.member/licenseAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1, 'team': 1, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'licenseAddModify')

        self.factory.xfer = BillAddModify()
        self.calljson('/diacamma.invoice/billAddModify', {'bill': 1, 'date': '2010-04-01', 'SAVE': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billAddModify')

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        print('season', Season.objects.get(id=10))
        print('year', new_year)
        print('date', self.get_json_path('date'))
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
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
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
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2010-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2011-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", "team2 [activity2] (56,78 €)"])
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
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
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
                      {'SAVE': 'YES', 'adherent': 2, 'status': 2, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10}, False)
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
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2010-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 1)
        self.assert_json_equal('', 'adherent/@0/id', "2")

        self.factory.xfer = AdherentCommand()
        self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('AdhCmd', 1)
        self.assert_json_equal('', 'AdhCmd/@0/adherent', "Dalton Avrel")
        self.assert_json_equal('', 'AdhCmd/@0/type', "Annually [76,44 €]")
        self.assert_json_equal('', 'AdhCmd/@0/prestations', "team1 [activity1] (324,97 €){[br/]}team2 [activity2] (56,78 €)")
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
        self.assert_json_equal('', 'AdhCmd/@0/prestations', "team3 [activity2] (12,34 €)")

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
'Dalton','Avrel','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','avrel.dalton@worldcompany.com','10/02/2000','BIDON SUR MER','Annually','Team1|price 3'
'Dalton','Joe','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','joe.dalton@worldcompany.com','18/05/1989','BIDON SUR MER','Annually','Team2|price 2,team3'
'Luke','Lucky','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','lucky.luke@worldcompany.com','04/06/1979','BIDON SUR MER','Annually','Team1;Team3'
'GOC','Marie','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Annually','Team1,team2;Team3'
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
        self.assert_json_equal('', 'adherent/@0/license', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])
        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/total', 413.75)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 7 + 18)
        self.assert_select_equal('fld_prestations', 14)  # nb=14
        self.assert_count_equal('Array', 4)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_prestations': 'Cours', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "4 éléments ont été importés")
        self.assert_json_equal('LABELFORM', 'import_error', [])
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/license', ["team1 [activity1] (324,97 €)"])
        self.assert_json_equal('', 'adherent/@1/id', "5")
        self.assert_json_equal('', 'adherent/@1/firstname', "Joe")
        self.assert_json_equal('', 'adherent/@1/license', ["team2 [activity2] (56,78 €)", "team3 [activity2] (12,34 €)"])
        self.assert_json_equal('', 'adherent/@2/id', "7")
        self.assert_json_equal('', 'adherent/@2/firstname', "Marie")
        self.assert_json_equal('', 'adherent/@2/license', ["team1 [activity1] (324,97 €)", "team2 [activity2] (56,78 €)", "team3 [activity2] (12,34 €)"])
        self.assert_json_equal('', 'adherent/@3/id', "6")
        self.assert_json_equal('', 'adherent/@3/firstname', "Lucky")
        self.assert_json_equal('', 'adherent/@3/license', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 0}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 4)
        self.assert_json_equal('', 'bill/@0/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@0/total', 401.41)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art3:324,97
        self.assert_json_equal('', 'bill/@1/third', "Dalton Joe")
        self.assert_json_equal('', 'bill/@1/total', 145.56)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78 + art1:12,34
        self.assert_json_equal('', 'bill/@2/third', "Luke Lucky")
        self.assert_json_equal('', 'bill/@2/total', 413.75)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art3:324.97
        self.assert_json_equal('', 'bill/@3/third', "GOC Marie")
        self.assert_json_equal('', 'bill/@3/total', 470.53)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + art3:324.97

    def test_bad_import_with_prestation(self):
        csv_content = """'nom','prenom','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','Cours'
'Dalton','Avrel','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','avrel.dalton@worldcompany.com','10/02/2000','BIDON SUR MER','Annually','Presta 6'
"""
        default_adherents()
        default_subscription()
        default_prestation()

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                            'fld_prestations': 'Cours', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "1 élément a été importé")
        self.assert_json_equal('LABELFORM', 'import_error', ["Prestation 'Presta 6' inconnue !"])

    def test_connexion(self):
        self.add_subscriptions()
        new_groupe = LucteriosGroup.objects.create(name='new_groupe')
        param = Parameter.objects.get(name='contacts-defaultgroup')
        param.value = '%d' % new_groupe.id
        param.save()
        configSMTP('localhost', AdherentConnectionTest.smtp_port)
        change_ourdetail()
        Parameter.change_value('member-connection', 1)
        Params.clear()
        adh_luke = Adherent.objects.get(firstname='Lucky')
        adh_luke.user = LucteriosUser.objects.create(username='lucky', first_name=adh_luke.firstname, last_name=adh_luke.lastname, email=adh_luke.email, is_active=False)
        adh_luke.save()
        new_adh = create_adherent("Ma'a", 'Dalton', '1961-04-12')
        new_adh.user = LucteriosUser.objects.create(username='maa', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()
        new_adh = create_adherent("Rantanplan", 'Chien', '2010-01-01')
        new_adh.user = LucteriosUser.objects.create(username='rantanplan', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()
        Responsability.objects.create(individual=new_adh, legal_entity_id=1)
        adh_joe = Adherent.objects.get(firstname='Joe')
        adh_joe.email = 'badèèè@worldcompany.com'
        adh_joe.save()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 5)
        self.assertEqual(len(self.json_actions), 4)

        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.assertEqual(3, len(LucteriosUser.objects.filter(is_active=True)))
            self.factory.xfer = AdherentConnection()
            self.calljson('/diacamma.member/adherentConnection', {'CONFIRME': 'YES', 'RELOAD': 'YES'}, False)
            self.assert_observer('core.custom', 'diacamma.member', 'adherentConnection')
            print('email sending %s' % [server.get(srv_id)[2] for srv_id in range(server.count())])
            self.assert_json_equal('LABELFORM', 'info', '{[center]}{[b]}Résultat{[/b]}{[/center]}{[br/]}1 connexion(s) supprimée(s).{[br/]}3 connexion(s) ajoutée(s).{[br/]}1 connexion(s) réactivée(s).{[br/]}{[br/]}1 courriel(s) ont échoué:{[ul]}{[li]}Dalton Joe : ', True)

            self.assertEqual([['Avrel.Dalton@worldcompany.com'], ['Jack.Dalton@worldcompany.com'], ['Lucky.Luke@worldcompany.com'], ['William.Dalton@worldcompany.com']], sorted([server.get(srv_id)[2] for srv_id in range(server.count())]))
            self.assertEqual(4, server.count())
            self.assertEqual(7, len(LucteriosUser.objects.filter(is_active=True)))

            self.factory.xfer = AdherentConnection()
            self.calljson('/diacamma.member/adherentConnection', {'CONFIRME': 'YES', 'RELOAD': 'YES'}, False)
            self.assert_observer('core.custom', 'diacamma.member', 'adherentConnection')
            self.assert_json_equal('LABELFORM', 'info', '{[center]}{[b]}Résultat{[/b]}{[/center]}{[br/]}0 connexion(s) supprimée(s).{[br/]}0 connexion(s) ajoutée(s).{[br/]}0 connexion(s) réactivée(s).')
            self.assertEqual(4, server.count())
            self.assertEqual(7, len(LucteriosUser.objects.filter(is_active=True)))
        finally:
            server.stop()
        user = LucteriosUser.objects.get(first_name='Avrel')
        self.assertEqual('Dalton', user.last_name)
        self.assertEqual('avrelD', user.username)
        self.assertEqual('Avrel.Dalton@worldcompany.com', user.email)
        self.assertEqual(True, user.is_active)
        self.assertEqual([new_groupe], list(user.groups.all()))

        user = LucteriosUser.objects.get(first_name='Lucky')
        self.assertEqual('lucky', user.username)
        self.assertEqual(True, user.is_active)
        self.assertEqual([new_groupe], list(user.groups.all()))

        user = LucteriosUser.objects.get(first_name='Joe')
        self.assertEqual('joeD', user.username)
        self.assertEqual(True, user.is_active)
        self.assertEqual([new_groupe], list(user.groups.all()))

        user = LucteriosUser.objects.get(first_name="Ma'a")
        self.assertEqual('maa', user.username)
        self.assertEqual(False, user.is_active)
        self.assertEqual([], list(user.groups.all()))

        user = LucteriosUser.objects.get(first_name="Rantanplan")
        self.assertEqual('rantanplan', user.username)
        self.assertEqual(True, user.is_active)
        self.assertEqual([], list(user.groups.all()))

    def test_connexion_with_createaccount(self):
        self.add_subscriptions()
        new_groupe = LucteriosGroup.objects.create(name='new_groupe')
        param = Parameter.objects.get(name='contacts-defaultgroup')
        param.value = '%d' % new_groupe.id
        param.save()
        configSMTP('localhost', AdherentConnectionTest.smtp_port)
        change_ourdetail()
        Parameter.change_value('member-connection', 1)
        Parameter.change_value('contacts-createaccount', 1)
        Params.clear()
        adh_luke = Adherent.objects.get(firstname='Lucky')
        adh_luke.user = LucteriosUser.objects.create(username='lucky', first_name=adh_luke.firstname, last_name=adh_luke.lastname, email=adh_luke.email, is_active=False)
        adh_luke.save()
        new_adh = create_adherent("Ma'a", 'Dalton', '1961-04-12')
        new_adh.user = LucteriosUser.objects.create(username='maa', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()
        new_adh = create_adherent("Rantanplan", 'Chien', '2010-01-01')
        new_adh.user = LucteriosUser.objects.create(username='rantanplan', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 5)
        self.assertEqual(len(self.json_actions), 4)

        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.assertEqual(3, len(LucteriosUser.objects.filter(is_active=True)))
            self.factory.xfer = AdherentConnection()
            self.calljson('/diacamma.member/adherentConnection', {'CONFIRME': 'YES', 'RELOAD': 'YES'}, False)
            self.assert_observer('core.custom', 'diacamma.member', 'adherentConnection')
            self.assert_json_equal('LABELFORM', 'info', '{[center]}{[b]}Résultat{[/b]}{[/center]}{[br/]}0 connexion(s) supprimée(s).{[br/]}4 connexion(s) ajoutée(s).{[br/]}1 connexion(s) réactivée(s).')

            print('email sending %s' % [server.get(srv_id)[2] for srv_id in range(server.count())])
            self.assertEqual([['Avrel.Dalton@worldcompany.com'], ['Jack.Dalton@worldcompany.com'], ['Joe.Dalton@worldcompany.com'], ['Lucky.Luke@worldcompany.com'], ['William.Dalton@worldcompany.com']], sorted([server.get(srv_id)[2] for srv_id in range(server.count())]))
            self.assertEqual(5, server.count())
            self.assertEqual(8, len(LucteriosUser.objects.filter(is_active=True)))
        finally:
            server.stop()

    def test_prestation_manage(self):
        default_prestation()

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('', 4)
        self.assert_select_equal('activity', 3)
        self.assert_grid_equal('team_prestation', {'team.name': "nom", 'team.description': "description", 'activity': "passion", "nb_adherent": "nombre d'adhérents", 'prices': "prix"}, 3)
        self.assert_count_equal('#team_prestation/actions', 7)
        self.assert_json_equal('', '#team_prestation/actions/@0/action', "prestationShow")
        self.assert_json_equal('', '#team_prestation/actions/@1/action', "prestationAddModify")
        self.assert_json_equal('', '#team_prestation/actions/@2/action', "prestationDel")
        self.assert_json_equal('', '#team_prestation/actions/@3/action', "prestationAddModify")
        self.assert_json_equal('', '#team_prestation/actions/@4/action', "prestationSwap")
        self.assert_json_equal('', '#team_prestation/actions/@5/action', "prestationSplit")
        self.assert_json_equal('', '#team_prestation/actions/@6/action', "objectMerge")

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'new_group': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 7)
        self.assert_select_equal("new_group", {0: 'nouveau group', 1: 'sélectionner ancien group'})
        self.assert_select_equal("team", {1: 'team1', 2: 'team2', 3: 'team3'})
        self.assert_select_equal("activity", {1: 'activity1', 2: 'activity2'})
        self.assert_select_equal('article', {1: 'ABC1 | Article 01 ', 2: 'ABC2 | Article 02 ', 3: 'ABC3 | Article 03 ', 4: 'ABC4 | Article 04 '})

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify',
                      {'SAVE': 'YES', 'team': 3, 'activity': 2, 'article': 1, 'new_group': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationAddModify')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 4)
        self.assert_json_equal('', 'team_prestation/@3/id', 4)
        self.assert_json_equal('', 'team_prestation/@3/team.name', "team3")
        self.assert_json_equal('', 'team_prestation/@3/team.description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('', 'team_prestation/@3/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@3/prices', [12.34])

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'new_group': 0, 'team_prestation': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 8)
        self.assert_json_equal('EDIT', 'team_name', "team3")
        self.assert_json_equal('MEMO', 'team_description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('SELECT', 'activity', 2)
        self.assert_json_equal('SELECT', 'article', 1)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify',
                      {'SAVE': 'YES', "team_name": "team #3", "team_description": "The team number 3", 'activity': 1, 'article': 2, 'new_group': 0, 'team_prestation': 4}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationAddModify')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 4)
        self.assert_json_equal('', 'team_prestation/@0/id', 4)
        self.assert_json_equal('', 'team_prestation/@0/team.name', "team #3")
        self.assert_json_equal('', 'team_prestation/@0/team.description', "The team number 3")
        self.assert_json_equal('', 'team_prestation/@0/activity', "activity1")
        self.assert_json_equal('', 'team_prestation/@0/prices', [56.78])

        self.factory.xfer = PrestationDel()
        self.calljson('/diacamma.member/prestationDel', {"team_prestation": 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationDel')
        self.assert_count_equal('', 3)
        self.assert_select_equal("group_mode", {0: 'désactivation group', 1: 'suppression group', 2: 'laisser group'})
        self.assertEqual(len(self.json_actions), 2)
        self.assert_action_equal('DELETE', self.json_actions[0], (str('Ok'), 'mdi:mdi-check', 'diacamma.member', 'prestationDel', 1, 1, 1, {'CONFIRME': 'YES'}))
        self.assert_action_equal('GET', self.json_actions[1], (str('Annuler'), 'mdi:mdi-cancel'))

        self.factory.xfer = PrestationDel()
        self.calljson('/diacamma.member/prestationDel', {"team_prestation": 4, 'CONFIRME': 'YES', 'group_mode': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationDel')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 3)

    def test_prestation_multi_price(self):
        default_prestation()

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify',
                      {'SAVE': 'YES', 'team': 3, 'activity': 2, 'article': 1, 'new_group': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationAddModify')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 4)

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('', 7)
        self.assert_json_equal('LABELFORM', 'team.name', 'team3')
        self.assert_json_equal('LABELFORM', 'activity', "activity2")
        self.assert_json_equal('LABELFORM', 'article', 'ABC1')
        self.assert_count_equal('adherent', 0)
        self.assert_count_equal('#adherent/actions', 3)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'team_prestation': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 8)
        self.assert_json_equal('EDIT', 'team_name', 'team3')
        self.assert_json_equal('MEMO', 'team_description', 'team N°3{[br/]}The newbies')
        self.assert_select_equal("activity", {1: 'activity1', 2: 'activity2'})
        self.assert_select_equal('article', {1: 'ABC1 | Article 01 ', 2: 'ABC2 | Article 02 ', 3: 'ABC3 | Article 03 ', 4: 'ABC4 | Article 04 '})
        self.assert_json_equal('CHECK', 'multiprice', False)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'team_prestation': 4, 'multiprice': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 5)
        self.assert_count_equal('prestation', 1)
        self.assert_json_equal('', 'prestation/@0/id', 4)
        self.assert_json_equal('', 'prestation/@0/name', "défaut")
        self.assert_json_equal('', 'prestation/@0/article', "ABC1")
        self.assert_json_equal('', 'prestation/@0/article.price', "12.34")
        self.assert_count_equal('#prestation/actions', 2)
        self.assert_json_equal('', '#prestation/actions/@0/action', "prestationPriceAddModify")
        self.assert_json_equal('', '#prestation/actions/@1/action', "prestationPriceAddModify")

        self.factory.xfer = PrestationPriceAddModify()
        self.calljson('/diacamma.member/prestationPriceAddModify', {'team_prestation': 4, 'multiprice': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationPriceAddModify')
        self.assert_count_equal('', 5)

        self.factory.xfer = PrestationPriceAddModify()
        self.calljson('/diacamma.member/prestationPriceAddModify', {'SAVE': 'YES', 'team_prestation': 4, 'multiprice': True,
                                                                    'name': 'price 4', 'article': 4}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationPriceAddModify')

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'team_prestation': 4, 'multiprice': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 5)
        self.assert_count_equal('prestation', 2)
        self.assert_json_equal('', 'prestation/@0/id', 4)
        self.assert_json_equal('', 'prestation/@0/name', "défaut")
        self.assert_json_equal('', 'prestation/@0/article', "ABC1")
        self.assert_json_equal('', 'prestation/@0/article.price', "12.34")
        self.assert_json_equal('', 'prestation/@1/id', 5)
        self.assert_json_equal('', 'prestation/@1/name', "price 4")
        self.assert_json_equal('', 'prestation/@1/article', "ABC4")
        self.assert_json_equal('', 'prestation/@1/article.price', "1.31")
        self.assert_count_equal('#prestation/actions', 3)
        self.assert_json_equal('', '#prestation/actions/@0/action', "prestationPriceAddModify")
        self.assert_json_equal('', '#prestation/actions/@1/action', "prestationPriceDel")
        self.assert_json_equal('', '#prestation/actions/@2/action', "prestationPriceAddModify")

        self.factory.xfer = PrestationPriceDel()
        self.calljson('/diacamma.member/prestationPriceDel', {'CONFIRME': 'YES', 'team_prestation': 4, 'multiprice': True, 'prestation': 4}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationPriceDel')

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {'team_prestation': 4, 'multiprice': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 5)
        self.assert_count_equal('prestation', 1)
        self.assert_json_equal('', 'prestation/@0/id', 5)
        self.assert_json_equal('', 'prestation/@0/name', "price 4")
        self.assert_json_equal('', 'prestation/@0/article', "ABC4")
        self.assert_json_equal('', 'prestation/@0/article.price', "1.31")
        self.assert_count_equal('#prestation/actions', 2)
        self.assert_json_equal('', '#prestation/actions/@0/action', "prestationPriceAddModify")
        self.assert_json_equal('', '#prestation/actions/@1/action', "prestationPriceAddModify")

    def test_prestation_change_subscription_multiprice(self):
        default_prestation()
        self.add_subscriptions(status=1)
        Prestation.objects.create(name="price 4", team_prestation_id=1, article_id=4)

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 76.44)

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('', 10)
        self.assert_json_equal('LABELFORM', 'team.name', 'team3')
        self.assert_json_equal('LABELFORM', 'activity', "activity2")
        self.assert_json_equal('LABELFORM', 'name_1', 'price 1')
        self.assert_json_equal('LABELFORM', 'price_1', 'ABC1 (12,34 €)')
        self.assert_json_equal('LABELFORM', 'name_4', 'price 4')
        self.assert_json_equal('LABELFORM', 'price_4', 'ABC4 (1,31 €)')
        self.assert_count_equal('adherent', 0)
        self.assert_count_equal('#adherent/actions', 3)

        self.factory.xfer = AdherentPrestationAdd()
        self.calljson('/diacamma.member/adherentPrestationAdd', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentPrestationAdd')

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentPrestationSave')
        self.assert_count_equal('', 3)
        self.assert_select_equal('prestation', {1: "price 1 (12,34 €)", 4: "price 4 (1,31 €)"})

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6', 'prestation': 4}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 2)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (1,31 €)"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (1,31 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 77.75)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 77.75)

        self.factory.xfer = AdherentPrestationDel()
        self.calljson('/diacamma.member/adherentPrestationDel', {'team_prestation': 1, 'adherent': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationDel')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (1,31 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 77.75)

    def test_prestation_change_subscription(self):
        default_prestation()
        self.add_subscriptions(status=1)

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('', 4)
        self.assert_select_equal('activity', 3)
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 76.44)

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('', 7)
        self.assert_json_equal('LABELFORM', 'team.name', 'team3')
        self.assert_json_equal('LABELFORM', 'activity', "activity2")
        self.assert_json_equal('LABELFORM', 'article', 'ABC1')
        self.assert_count_equal('adherent', 0)
        self.assert_count_equal('#adherent/actions', 3)
        self.assert_json_equal('', '#adherent/actions/@0/action', "adherentShow")
        self.assert_json_equal('', '#adherent/actions/@1/action', "adherentPrestationDel")
        self.assert_json_equal('', '#adherent/actions/@2/action', "adherentPrestationAdd")

        self.factory.xfer = AdherentPrestationAdd()
        self.calljson('/diacamma.member/adherentPrestationAdd', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentPrestationAdd')

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 2)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 88.78)

        self.factory.xfer = AdherentPrestationDel()
        self.calljson('/diacamma.member/adherentPrestationDel', {'team_prestation': 1, 'adherent': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationDel')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 88.78)

    def test_prestation_new_subscription(self):
        default_prestation()
        default_adherents()
        default_subscription()

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('', 4)
        self.assert_select_equal('activity', 3)
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 0)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 0)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentPrestationSave')
        self.assert_count_equal('', 8)
        self.assert_json_equal('LABELFORM', 'no_subscription', ['Dalton Avrel', 'Luke Lucky'])
        self.assert_json_equal('LABELFORM', 'season', 10)
        self.assert_select_equal('subscriptiontype', {1: "Annually [76,44 €]", 2: "Periodic [76,44 €]", 3: "Monthly [76,44 €]", 4: "Calendar [76,44 €]"})
        self.assert_select_equal('status', {1: 'en création', 2: 'validé'})
        self.assert_json_equal('LABELFORM', 'prestation_lbl', "price 1 (12,34 €)")

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 2)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 88.78)

        self.factory.xfer = AdherentPrestationDel()
        self.calljson('/diacamma.member/adherentPrestationDel', {'team_prestation': 1, 'adherent': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationDel')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 1)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 88.78)

    def test_prestation_subscription_validated(self):
        default_prestation()
        self.add_subscriptions(status=2)

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('', 4)
        self.assert_select_equal('activity', 3)
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 1)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 1)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 76.44)

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('', 7)
        self.assert_json_equal('LABELFORM', 'team.name', 'team3')
        self.assert_json_equal('LABELFORM', 'activity', "activity2")
        self.assert_json_equal('LABELFORM', 'article', 'ABC1')
        self.assert_count_equal('adherent', 0)
        self.assert_count_equal('#adherent/actions', 3)
        self.assert_json_equal('', '#adherent/actions/@0/action', "adherentShow")
        self.assert_json_equal('', '#adherent/actions/@1/action', "adherentPrestationDel")
        self.assert_json_equal('', '#adherent/actions/@2/action', "adherentPrestationAdd")

        self.factory.xfer = AdherentPrestationAdd()
        self.calljson('/diacamma.member/adherentPrestationAdd', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentPrestationAdd')

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 2)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2]"])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2]"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 1)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 1)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 88.78)

        self.factory.xfer = AdherentPrestationDel()
        self.calljson('/diacamma.member/adherentPrestationDel', {'team_prestation': 1, 'adherent': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationDel')

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('adherent', 1)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', [])

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/season', "2009/2010")
        self.assert_json_equal('', 'subscription/@0/status', 2)
        self.assert_json_equal('', 'subscription/@0/subscriptiontype', "Annually")
        self.assert_json_equal('', 'subscription/@0/begin_date', "2009-09-01")
        self.assert_json_equal('', 'subscription/@0/end_date', "2010-08-31")
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2]"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 6)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 1)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@2/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 1)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 76.44)
        self.assert_json_equal('', 'bill/@4/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@4/bill_type', 1)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 88.78)
        self.assert_json_equal('', 'bill/@5/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@5/bill_type', 2)
        self.assert_json_equal('', 'bill/@5/status', 0)
        self.assert_json_equal('', 'bill/@5/total', 12.34)

    def test_prestation_merge(self):
        default_prestation()
        default_adherents()
        default_subscription()
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;3;6', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 2, 'adherent': '3;4;5;6', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 3, 'adherent': '2;3', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 3)
        self.assert_json_equal('', 'team_prestation/@0/id', 3)
        self.assert_json_equal('', 'team_prestation/@0/team.name', "team1")
        self.assert_json_equal('', 'team_prestation/@0/team.description', "team N°1{[br/]}The bests")
        self.assert_json_equal('', 'team_prestation/@0/activity', "activity1")
        self.assert_json_equal('', 'team_prestation/@0/nb_adherent', 2)
        self.assert_json_equal('', 'team_prestation/@0/prices', [324.97])
        self.assert_json_equal('', 'team_prestation/@1/id', 2)
        self.assert_json_equal('', 'team_prestation/@1/team.name', "team2")
        self.assert_json_equal('', 'team_prestation/@1/team.description', "team N°2{[br/]}The chalengers")
        self.assert_json_equal('', 'team_prestation/@1/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@1/nb_adherent', 4)
        self.assert_json_equal('', 'team_prestation/@1/prices', [56.78])
        self.assert_json_equal('', 'team_prestation/@2/id', 1)
        self.assert_json_equal('', 'team_prestation/@2/team.name', "team3")
        self.assert_json_equal('', 'team_prestation/@2/team.description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('', 'team_prestation/@2/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@2/nb_adherent', 3)
        self.assert_json_equal('', 'team_prestation/@2/prices', [12.34])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 413.75)  # 76.44 + 12,34 (1) + 324,97 (3)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 470.53)  # 76.44 + 12,34 (1) + 56,78 (2) + 324,97 (3)
        self.assert_json_equal('', 'bill/@2/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 145.56)  # 76.44 + 12,34 (1) + 69,12 (2)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 133.22)  # 76.44 + 56,78(2)
        self.assert_json_equal('', 'bill/@4/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 133.22)  # 76.44 + 56,78(2)

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", 'team2 [activity2] (56,78 €)', "team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] (56,78 €)"])

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('team', 3)
        self.assert_json_equal('', 'team/@0/name', "team1")
        self.assert_json_equal('', 'team/@1/name', "team2")
        self.assert_json_equal('', 'team/@2/name', "team3")

        self.factory.xfer = ObjectMerge()
        self.calljson('/CORE/objectMerge', {'modelname': 'member.TeamPrestation', 'field_id': 'team_prestation', 'team_prestation': '2;3', 'CONFIRME': 'YES', 'mrg_object': '3'}, False)
        self.assert_observer('core.acknowledge', 'CORE', 'objectMerge')
        self.assert_action_equal('GET', self.response_json['action'], ('Editer', 'mdi:mdi-text-box-outline', 'diacamma.member', 'prestationShow', 1, 1, 1, {"team_prestation": 3}))

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 2)
        self.assert_json_equal('', 'team_prestation/@0/id', 3)
        self.assert_json_equal('', 'team_prestation/@0/team.name', "team1")
        self.assert_json_equal('', 'team_prestation/@0/team.description', "team N°1{[br/]}The bests")
        self.assert_json_equal('', 'team_prestation/@0/activity', "activity1")
        self.assert_json_equal('', 'team_prestation/@0/nb_adherent', 5)
        self.assert_json_equal('', 'team_prestation/@0/prices', [56.78, 324.97])
        self.assert_json_equal('', 'team_prestation/@1/id', 1)
        self.assert_json_equal('', 'team_prestation/@1/team.name', "team3")
        self.assert_json_equal('', 'team_prestation/@1/team.description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('', 'team_prestation/@1/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@1/nb_adherent', 3)
        self.assert_json_equal('', 'team_prestation/@1/prices', [12.34])

        self.factory.xfer = PrestationShow()
        self.calljson('/diacamma.member/prestationShow', {'team_prestation': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationShow')
        self.assert_count_equal('', 10)
        self.assert_json_equal('LABELFORM', 'team.name', 'team1')
        self.assert_json_equal('LABELFORM', 'activity', "activity1")
        self.assert_json_equal('LABELFORM', 'name_2', 'price 2')
        self.assert_json_equal('LABELFORM', 'price_2', 'ABC2 (56,78 €)')
        self.assert_json_equal('LABELFORM', 'name_3', 'price 3')
        self.assert_json_equal('LABELFORM', 'price_3', 'ABC3 (324,97 €)')
        self.assert_count_equal('adherent', 5)
        self.assert_count_equal('#adherent/actions', 3)

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('team', 2)
        self.assert_json_equal('', 'team/@0/name', "team1")
        self.assert_json_equal('', 'team/@1/name', "team3")

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)", "team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('subscription', 1)
        self.assert_json_equal('', 'subscription/@0/involvement', ["team1 [activity1] (324,97 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 413.75)  # 76.44 + 12.34 (1) + 324.97 (3)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 413.75)  # 76.44 + 12.34 (1) + 324.97 (3)
        self.assert_json_equal('', 'bill/@2/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 413.75)  # 76.44 + 12.34 (1) + 324.97 (3)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 401.41)  # 76.44 + 324,97 (3)
        self.assert_json_equal('', 'bill/@4/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 401.41)  # 76.44 + 56,78(2)

    def test_prestation_swap(self):
        default_prestation()
        default_adherents()
        default_subscription()
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;4;6', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 2, 'adherent': '3;5', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] (56,78 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] (56,78 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 88.78)
        self.assert_json_equal('', 'bill/@2/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 88.78)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 133.22)
        self.assert_json_equal('', 'bill/@4/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 133.22)

        self.factory.xfer = PrestationSwap()
        self.calljson('/diacamma.member/prestationSwap', {'team_prestation': '1;2'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationSwap')
        self.assert_count_equal('', 4)
        self.assert_json_equal('LABELFORM', 'lbl_left', '          team2 [activity2]', txtrange=True)
        self.assert_json_equal('LABELFORM', 'lbl_right', '          team3 [activity2]', txtrange=True)
        self.assert_json_equal('CHECKLIST', 'swaps', ['2', '4', '6'])
        self.assert_select_equal('swaps', {2: 'Dalton Avrel', 3: 'Dalton William', 4: 'Dalton Jack', 5: 'Dalton Joe', 6: 'Luke Lucky'}, True)

        self.factory.xfer = PrestationSwap()
        self.calljson('/diacamma.member/prestationSwap', {'team_prestation': '1;2', 'CONFIRME': 'YES', 'swaps': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationSwap')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 3, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] (56,78 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team3 [activity2] (12,34 €)"])
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 6, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('', 'subscription/@0/involvement', ["team2 [activity2] (56,78 €)"])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 5)
        self.assert_json_equal('', 'bill/@0/third', 'Dalton Avrel')
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 88.78)
        self.assert_json_equal('', 'bill/@1/third', 'Dalton Jack')
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 88.78)
        self.assert_json_equal('', 'bill/@2/third', 'Luke Lucky')
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 133.22)
        self.assert_json_equal('', 'bill/@3/third', 'Dalton Joe')
        self.assert_json_equal('', 'bill/@3/bill_type', 0)
        self.assert_json_equal('', 'bill/@3/status', 0)
        self.assert_json_equal('', 'bill/@3/total', 88.78)
        self.assert_json_equal('', 'bill/@4/third', 'Dalton William')
        self.assert_json_equal('', 'bill/@4/bill_type', 0)
        self.assert_json_equal('', 'bill/@4/status', 0)
        self.assert_json_equal('', 'bill/@4/total', 133.22)

    def test_prestation_split(self):
        default_prestation()
        default_adherents()
        default_subscription()
        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 1, 'adherent': '2;3;4;5;6', 'NEW_SUB': 'YES', 'subscriptiontype': 1, 'status': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 3)

        self.factory.xfer = PrestationSplit()
        self.calljson('/diacamma.member/prestationSplit', {'team_prestation': '1'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationSplit')
        self.assert_count_equal('', 8)
        self.assert_json_equal('EDIT', 'team_name', "team3")
        self.assert_json_equal('MEMO', 'team_description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('SELECT', 'activity', 2)
        self.assert_json_equal('SELECT', 'article', 1)

        self.factory.xfer = PrestationSplit()
        self.calljson('/diacamma.member/prestationSplit', {'team_prestation': '1', 'CONFIRME': 'YES', 'team_name': 'team3b', 'team_description': "team N°3b{[br/]}The newbies+", 'activity': 2, 'article': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationSplit')
        self.assert_action_equal('POST', self.response_json['action'], ('Permuter entre prestations', 'mdi:mdi-badge-account-horizontal-outline', 'diacamma.member', 'prestationSwap', 1, 1, 1, {"team_prestation": '1;4'}))

        self.factory.xfer = PrestationList()
        self.calljson('/diacamma.member/prestationList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationList')
        self.assert_count_equal('team_prestation', 4)
        self.assert_json_equal('', 'team_prestation/@0/id', 3)
        self.assert_json_equal('', 'team_prestation/@0/team.name', "team1")
        self.assert_json_equal('', 'team_prestation/@0/team.description', "team N°1{[br/]}The bests")
        self.assert_json_equal('', 'team_prestation/@0/activity', "activity1")
        self.assert_json_equal('', 'team_prestation/@0/prices', [324.970])
        self.assert_json_equal('', 'team_prestation/@1/id', 2)
        self.assert_json_equal('', 'team_prestation/@1/team.name', "team2")
        self.assert_json_equal('', 'team_prestation/@1/team.description', "team N°2{[br/]}The chalengers")
        self.assert_json_equal('', 'team_prestation/@1/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@1/prices', [56.780])
        self.assert_json_equal('', 'team_prestation/@2/id', 1)
        self.assert_json_equal('', 'team_prestation/@2/team.name', "team3")
        self.assert_json_equal('', 'team_prestation/@2/team.description', "team N°3{[br/]}The newbies")
        self.assert_json_equal('', 'team_prestation/@2/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@2/prices', [12.340])
        self.assert_json_equal('', 'team_prestation/@3/id', 4)
        self.assert_json_equal('', 'team_prestation/@3/team.name', "team3b")
        self.assert_json_equal('', 'team_prestation/@3/team.description', "team N°3b{[br/]}The newbies+")
        self.assert_json_equal('', 'team_prestation/@3/activity', "activity2")
        self.assert_json_equal('', 'team_prestation/@3/prices', [12.340])


class AdherentFamilyTest(BaseAdherentTest):

    def setUp(self):
        BaseAdherentTest.setUp(self)
        Parameter.change_value('member-family-type', 3)
        Parameter.change_value("member-fields", "firstname;lastname;tel1;tel2;email;family")
        set_parameters([])

    def test_show_adherent(self):
        self.add_subscriptions()
        self.assertEqual("famille", str(Params.getobject('member-family-type')))

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow',
                      {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal('', 3 + (15 + 2 + 5) + 2 + 6 + 5 + 2)  # header + identity/family/docs + subscription + financial + invoice + grade
        self.assert_json_equal('LABELFORM', 'family', None)
        self.assert_json_equal('', '#famillybtn/action/short_icon', "mdi:mdi-pencil-plus-outline")

    def test_new_family(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = AdherentFamilyAdd()
        self.calljson('/diacamma.member/adherentFamilyAdd', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentFamilyAdd')
        self.assert_count_equal('', 4)
        self.assert_count_equal('legal_entity', 0)
        self.assert_json_equal('', '#legal_entity/actions/@1/short_icon', "mdi:mdi-pencil-plus")
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
        self.assert_json_equal('', '#famillybtn/action/short_icon', "mdi:mdi-pencil-outline")

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
        self.assert_json_equal('', '#famillybtn/action/short_icon', "mdi:mdi-pencil-outline")

    def test_add_adherent(self):
        default_adherents()
        default_subscription()
        self.add_family()
        self.factory.xfer = AdherentAddModify()
        self.calljson('/diacamma.member/adherentAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_json_equal('', '#famillybtn/action/short_icon', "mdi:mdi-pencil-plus-outline")

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
        self.assert_json_equal('', '#famillybtn/action/short_icon', "mdi:mdi-pencil-outline")

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
        self.assert_json_equal('', 'detail/@0/designation', "Article 01{[br/]}Cotisation de 'Dalton Avrel'{[br/]}Pour la période 01/09/2009 -> 31/08/2010")
        self.assert_json_equal('', 'detail/@0/price', 12.34)
        self.assert_json_equal('', 'detail/@0/quantity_txt', '1,000')
        self.assert_json_equal('', 'detail/@0/total', 12.34)
        self.assert_json_equal('', 'detail/@1/article', 'ABC5')
        self.assert_json_equal('', 'detail/@1/designation', "Article 05{[br/]}Cotisation de 'Dalton Avrel'{[br/]}Pour la période 01/09/2009 -> 31/08/2010")
        self.assert_json_equal('', 'detail/@1/price', 64.10)
        self.assert_json_equal('', 'detail/@1/quantity_txt', '1,00')
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

    def test_change_cotation(self):
        self.prep_subscription_family()

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'subscriptiontype': 5, 'subscription': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 12.34 + 76.44)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}")
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/status', 2)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44 + 76.44)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_action_equal('GET', self.get_json_path('#parentbill/action'), ("origine", "mdi:mdi-invoice-edit-outline",
                                                                                   "diacamma.invoice", "billShow", 0, 1, 1, {'bill': 1}))

    def test_cancel_cotation(self):
        self.prep_subscription_family()

        self.factory.xfer = SubscriptionTransition()
        self.calljson('/diacamma.member/subscriptionTransition', {'CONFIRME': 'YES', 'subscription': 1, 'TRANSITION': 'cancel'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}")
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/status', 2)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44 + 76.44)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_action_equal('GET', self.get_json_path('#parentbill/action'), ("origine", "mdi:mdi-invoice-edit-outline",
                                                                                   "diacamma.invoice", "billShow", 0, 1, 1, {'bill': 1}))

    def test_delete_cotation(self):
        self.prep_subscription_family()

        self.factory.xfer = SubscriptionDel()
        self.calljson('/diacamma.member/subscriptionDel', {'CONFIRME': 'YES', 'subscription': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionDel')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/total', 76.44)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}cotisation{[/b]}")
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/status', 2)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/total', 76.44 + 76.44)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_action_equal('GET', self.get_json_path('#parentbill/action'), ("origine", "mdi:mdi-invoice-edit-outline",
                                                                                   "diacamma.invoice", "billShow", 0, 1, 1, {'bill': 1}))

    def test_command(self):
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
        self.calljson('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01', 'enddate_delay':-90, 'reminder': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('adherent', 3)
        self.assert_json_equal('', 'adherent/@0/id', "2")
        self.assert_json_equal('', 'adherent/@1/id', "6")
        self.assert_json_equal('', 'adherent/@2/id', "5")

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

        configSMTP('localhost', AdherentConnectionTest.smtp_port)
        change_ourdetail()
        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.assertEqual(0, server.count())

            self.factory.xfer = AdherentCommand()
            self.calljson('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file, 'send_email': True}, False)
            self.assert_observer('core.dialogbox', 'diacamma.member', 'adherentCommand')

            self.assertEqual(1, server.count())
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(0)[1])
            self.assertEqual(['dalton@worldcompany.com', 'Avrel.Dalton@worldcompany.com', 'Joe.Dalton@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(0)[2])
            msg_txt, msg, msg_file = server.check_first_message('Nouvelle cotisation', 3, {'To': 'dalton@worldcompany.com'})
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

    def test_merge(self):
        default_adherents()
        default_subscription()
        self.add_family()
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 1, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 3, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 4, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 3, 'activity': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 5, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 1, 'activity': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'status': 2, 'adherent': 6, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 5)
        self.assert_json_equal('', 'adherent/@0/id', 2)
        self.assert_json_equal('', 'adherent/@0/firstname', 'Avrel')
        self.assert_json_equal('', 'adherent/@0/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@0/family', 'LES DALTONS')
        self.assert_json_equal('', 'adherent/@1/id', 4)
        self.assert_json_equal('', 'adherent/@1/firstname', 'Jack')
        self.assert_json_equal('', 'adherent/@1/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@1/family', None)
        self.assert_json_equal('', 'adherent/@2/id', 5)
        self.assert_json_equal('', 'adherent/@2/firstname', 'Joe')
        self.assert_json_equal('', 'adherent/@2/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@2/family', 'LES DALTONS')
        self.assert_json_equal('', 'adherent/@3/id', 3)
        self.assert_json_equal('', 'adherent/@3/firstname', 'William')
        self.assert_json_equal('', 'adherent/@3/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@3/family', None)
        self.assert_json_equal('', 'adherent/@4/id', 6)
        self.assert_json_equal('', 'adherent/@4/firstname', 'Lucky')
        self.assert_json_equal('', 'adherent/@4/lastname', 'Luke')
        self.assert_json_equal('', 'adherent/@4/family', None)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 4)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/third', "Dalton William")
        self.assert_json_equal('', 'bill/@2/third', "Dalton Jack")
        self.assert_json_equal('', 'bill/@3/third', "Luke Lucky")

        self.factory.xfer = ObjectMerge()
        self.calljson('/CORE/objectMerge',
                      {'modelname': 'contacts.Individual', 'field_id': 'individual', 'individual': '2;3', 'CONFIRME': 'YES', 'mrg_object': '3'}, False)
        self.assert_observer('core.acknowledge', 'CORE', 'objectMerge')

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/id', 4)
        self.assert_json_equal('', 'adherent/@0/firstname', 'Jack')
        self.assert_json_equal('', 'adherent/@0/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@0/family', None)
        self.assert_json_equal('', 'adherent/@1/id', 5)
        self.assert_json_equal('', 'adherent/@1/firstname', 'Joe')
        self.assert_json_equal('', 'adherent/@1/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@1/family', 'LES DALTONS')
        self.assert_json_equal('', 'adherent/@2/id', 3)
        self.assert_json_equal('', 'adherent/@2/firstname', 'William')
        self.assert_json_equal('', 'adherent/@2/lastname', 'Dalton')
        self.assert_json_equal('', 'adherent/@2/family', 'LES DALTONS')
        self.assert_json_equal('', 'adherent/@3/id', 6)
        self.assert_json_equal('', 'adherent/@3/firstname', 'Lucky')
        self.assert_json_equal('', 'adherent/@3/lastname', 'Luke')
        self.assert_json_equal('', 'adherent/@3/family', None)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 4)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@2/third', "Dalton Jack")
        self.assert_json_equal('', 'bill/@3/third', "Luke Lucky")

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
        self.assertEqual(len(self.json_actions), 3)

        self.assertEqual(1, LegalEntity.objects.filter(structure_type_id=3).count())

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type': 1}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 0)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': '"',
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 7 + 13)
        self.assert_select_equal('fld_family', 12)
        self.assert_count_equal('Array', 7)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': '"', 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            'fld_subscriptiontype': 'Type', 'fld_family': 'famille', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "7 éléments ont été importés")
        self.assert_json_equal('LABELFORM', 'import_error', [])
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

        self.factory.xfer = AdherentContactList()
        self.calljson('/diacamma.member/adherentContactList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentContactList')
        self.assert_count_equal('abstractcontact', 5)
        self.assert_json_equal('', 'abstractcontact/@0/ident', "Dalton")
        self.assert_json_equal('', 'abstractcontact/@0/adherents', ["Dalton Joe"])
        self.assert_json_equal('', 'abstractcontact/@1/ident', "GOC Marie")
        self.assert_json_equal('', 'abstractcontact/@1/adherents', ["GOC Marie"])
        self.assert_json_equal('', 'abstractcontact/@2/ident', "LES DALTONS")
        self.assert_json_equal('', 'abstractcontact/@2/adherents', ["Dalton Avrel", "Dalton Ma'a"])
        self.assert_json_equal('', 'abstractcontact/@3/ident', "Luke")
        self.assert_json_equal('', 'abstractcontact/@3/adherents', ["Luke Lucky"])
        self.assert_json_equal('', 'abstractcontact/@4/ident', "UHADIK-FEPIZIBU")
        self.assert_json_equal('', 'abstractcontact/@4/adherents', ["FEPIZIBU Benjamin", "UHADIK Jeanne"])

    def test_import_with_prestation(self):
        csv_content = """'nom','prenom','famille','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','Cours'
'Dalton','Avrel','Dalton','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','avrel.dalton@worldcompany.com','10/02/2000','BIDON SUR MER','Annually','Team1'
'Dalton','Joe','Dalton','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','joe.dalton@worldcompany.com','18/05/1989','BIDON SUR MER','Annually','team2,Team3'
'Luke','Lucky','Luke','Homme','rue de la liberté','99673','TOUINTOUIN','0502851031','0439423854','lucky.luke@worldcompany.com','04/06/1979','BIDON SUR MER','Annually','Team1;Team3'
'GOC','Marie','','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Annually','Team1,Team2;team3'
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
        self.calljson('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                            'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent': StringIO(csv_content)}, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 7 + 16)
        self.assert_select_equal('fld_family', 15)
        self.assert_select_equal('fld_prestations', 15)
        self.assert_count_equal('Array', 4)

        self.factory.xfer = ContactImport()
        self.calljson('/lucterios.contacts/contactImport', {'step': 4, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                            'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'importcontent0': csv_content,
                                                            "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                            "fld_family": "famille", "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                            'fld_subscriptiontype': 'Type', 'fld_prestations': 'Cours', }, False)
        self.assert_observer('core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('', 3)
        self.assert_json_equal('LABELFORM', 'result', "4 éléments ont été importés")
        self.assert_json_equal('LABELFORM', 'import_error', [])
        self.assertEqual(len(self.json_actions), 1)

        self.factory.xfer = AdherentActiveList()
        self.calljson('/diacamma.member/adherentActiveList', {'dateref': '2010-01-15'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentActiveList')
        self.assert_count_equal('adherent', 4)
        self.assert_json_equal('', 'adherent/@0/firstname', "Avrel")
        self.assert_json_equal('', 'adherent/@0/family', "Dalton")
        self.assert_json_equal('', 'adherent/@0/license', ["team1 (324,97 €)"])
        self.assert_json_equal('', 'adherent/@1/firstname', "Joe")
        self.assert_json_equal('', 'adherent/@1/family', "Dalton")
        self.assert_json_equal('', 'adherent/@1/license', ["team2 (56,78 €)", 'team3 (12,34 €)'])
        self.assert_json_equal('', 'adherent/@2/firstname', "Marie")
        self.assert_json_equal('', 'adherent/@2/family', None)
        self.assert_json_equal('', 'adherent/@2/license', ["team1 (324,97 €)", "team2 (56,78 €)", "team3 (12,34 €)"])
        self.assert_json_equal('', 'adherent/@3/firstname', "Lucky")
        self.assert_json_equal('', 'adherent/@3/family', "Luke")
        self.assert_json_equal('', 'adherent/@3/license', ["team1 (324,97 €)", "team3 (12,34 €)"])

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

    def test_with_prestation_valid_subscription(self):
        self.prep_family()
        set_parameters(["team"])
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '1;2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/id', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team2 (56,78 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 5, 'dateref': '2014-10-01', 'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = SubscriptionTransition()
        self.calljson('/diacamma.member/subscriptionTransition', {'CONFIRME': 'YES', 'subscription': 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTransition')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 2)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 5, 'dateref': '2014-10-01', 'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 1)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 3)
        self.assert_json_equal('', 'bill/@1/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

    def test_with_prestation_convert_bill(self):
        self.prep_family()
        set_parameters(["team"])
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '1;2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/id', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team2 (56,78 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 5, 'dateref': '2014-10-01', 'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = BillToBill()
        self.calljson('/diacamma.invoice/billToBill', {'CONFIRME': 'YES', 'bill': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billToBill')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 2)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 5, 'dateref': '2014-10-01', 'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 1)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 1)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 3)
        self.assert_json_equal('', 'bill/@1/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = BillAddModify()
        self.calljson('/diacamma.invoice/billAddModify', {'bill': 2, 'date': '2015-04-01', 'SAVE': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billAddModify')

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'bill': 2, 'TRANSITION': 'valid', 'CONFIRME': 'YES', 'withpayoff': False, 'sendemail': False}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = AdherentPrestationSave()
        self.calljson('/diacamma.member/adherentPrestationSave', {'team_prestation': 3, 'adherent': '2;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentPrestationSave')

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 3)

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'adherent': 5, 'dateref': '2014-10-01', 'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 2)
        self.assert_count_equal('license', 2)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 3)
        self.assert_json_equal('', 'bill/@2/id', 3)
        self.assert_json_equal('', 'bill/@2/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@2/bill_type', 1)
        self.assert_json_equal('', 'bill/@2/status', 0)
        self.assert_json_equal('', 'bill/@2/total', 649.94)  # 2 x art 3 = 2 x 324.97€

    def test_with_prestation_modify(self):
        self.prep_family()
        set_parameters(["team"])
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '1;2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)
        self.assert_json_equal('', 'bill/@0/id', 1)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team2 (56,78 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'subscription': 1, 'prestations': '1;3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 0)
        self.assert_json_equal('', 'bill/@0/status', 0)
        self.assert_json_equal('', 'bill/@0/total', 546.97)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art3:324.97 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 2)
        self.assert_json_equal('', 'bill/@1/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team1 (324,97 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])

    def test_with_prestation_and_order_modify(self):
        Params.setvalue('invoice-order-mode', 2)
        self.prep_family()
        set_parameters(["team"])
        default_prestation()
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 2, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '1;2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 1, 'dateref': '2014-10-01',
                                                                 'subscriptiontype': 1, 'season': 10, 'prestations': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillTransition()
        self.calljson('/diacamma.invoice/billTransition', {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.invoice', 'billTransition')

        self.call_ex('/diacamma.invoice/invoiceValidQuotation', {'payid': 1, 'CONFIRME': 'True', 'firstname': 'Jean', 'lastname': 'Valjean'}, 'post', 200)
        self.assertTrue(self.content.startswith("<!DOCTYPE html>"), self.content)
        self.assertIn('devis validé par Jean Valjean', self.content)

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 4)
        self.assert_json_equal('', 'bill/@0/status', 1)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@1/id', 1)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 3)
        self.assert_json_equal('', 'bill/@1/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team2 (56,78 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])

        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'subscription': 1, 'prestations': '1;3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {'bill_type':-1, 'status_filter':-2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 3)
        self.assert_json_equal('', 'bill/@0/id', 2)
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/bill_type', 4)
        self.assert_json_equal('', 'bill/@0/status', 2)
        self.assert_json_equal('', 'bill/@0/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@1/id', 3)
        self.assert_json_equal('', 'bill/@1/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@1/bill_type', 0)
        self.assert_json_equal('', 'bill/@1/status', 0)
        self.assert_json_equal('', 'bill/@1/total', 546.97)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art3:324.97 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78
        self.assert_json_equal('', 'bill/@2/id', 1)
        self.assert_json_equal('', 'bill/@2/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@2/bill_type', 0)
        self.assert_json_equal('', 'bill/@2/status', 3)
        self.assert_json_equal('', 'bill/@2/total', 278.78)  # Subscription: art1:12.34 + art5:64.10 / Prestations: art1:12.34 + art2:56.78 + Subscription: art1:12.34 + art5:64.10 / Prestations: art2:56.78

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team3 (12,34 €)', 'team1 (324,97 €)'])

        self.factory.xfer = SubscriptionShow()
        self.calljson('/diacamma.member/subscriptionShow', {'subscription': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_json_equal('LABELFORM', 'status', 1)
        self.assert_json_equal('LABELFORM', 'prestations', ['team2 (56,78 €)'])


class SubscriptionModeTest(BaseAdherentTest):

    smtp_port = 3025

    def setUp(self):
        BaseAdherentTest.setUp(self)
        change_ourdetail()
        default_paymentmethod()
        Parameter.change_value('member-family-type', 0)
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])
        ThirdShow.url_text
        adherent_list = default_adherents()
        self.joe_adh = adherent_list[3]
        self.joe_adh.activate_adherent()
        default_subscription()
        SubscriptionModeTest.smtp_port += 1
        configSMTP('localhost', SubscriptionModeTest.smtp_port)

    def valid_check_email(self, params, nb_mail, subscriptid=1):
        server = TestReceiver()
        server.start(SubscriptionModeTest.smtp_port)
        try:
            params.update({"SAVE": "YES", "adherent": 5, 'autocreate': 1})
            self.factory.xfer = SubscriptionAddForCurrent()
            self.calljson('/diacamma.member/subscriptionAddForCurrent', params, False)
            self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddForCurrent')
            self.assertEqual(self.response_json['action']['id'], "diacamma.member/subscriptionConfirmCurrent")
            self.assertEqual(len(self.response_json['action']['params']), 1)
            self.assertEqual(self.response_json['action']['params']['subscription'], subscriptid)

            self.factory.xfer = SubscriptionConfirmCurrent()
            self.calljson('/diacamma.member/subscriptionConfirmCurrent', {'subscription': subscriptid}, False)
            self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionConfirmCurrent')
            if nb_mail == 1:
                self.assertEqual(self.response_json['action']['id'], "diacamma.invoice/currentPayableShow")
                self.assertEqual(len(self.response_json['action']['params']), 2)
                self.assertEqual(list(self.response_json['action']['params'].keys()), ['item_name', 'bill'])
            else:
                self.assertNotIn('action', self.response_json)

            last_subscription = Subscription.objects.all().first()
            self.assertEqual(last_subscription.adherent_id, 5)
            self.assertEqual(last_subscription.subscriptiontype_id, params['subscriptiontype'])
            self.assertEqual(last_subscription.begin_date.isoformat(), params['begin_date'] if 'begin_date' in params else '2009-09-01')
            self.assertEqual(last_subscription.license_set.first().team_id, params['team'])
            self.assertEqual(last_subscription.license_set.first().activity_id, params['activity'])
            self.assertEqual(nb_mail, server.count())
            if nb_mail == 1:
                _msg_txt, msg, msg_file = server.check_first_message('Nouvelle cotisation', 3, {'To': 'Joe.Dalton@worldcompany.com'})
                self.assertIn('Bienvenu', decode_b64(msg.get_payload()))
                self.assertIn('devis_A-1_Dalton Joe.pdf', msg_file.get('Content-Type', ''))
        finally:
            server.stop()

    def test_nohimself(self):
        Parameter.change_value('member-subscription-mode', 0)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'subscriptionAddForCurrent')

    def test_withmoderation_new(self):
        Parameter.change_value('member-subscription-mode', 1)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '0')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '2')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_select_equal('period', 4)
        self.assert_json_equal('SELECT', 'period', 37)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 0)

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {"subscriptiontype": 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '0')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_json_equal('DATE', 'begin_date', self.dateref_expected)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 0)

        self.valid_check_email(params={"status": 0, "subscriptiontype": 2, 'period': 37,
                                       "activity": 1, "team": 1}, nb_mail=0)

    def test_withmoderation_renew(self):
        Parameter.change_value('member-subscription-mode', 1)
        self.add_subscriptions(year=2008, season_id=9, status=2, create_adh_sub=False)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '0')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '2')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '3')
        self.assert_json_equal('DATE', 'begin_date', self.dateref_expected if not self.is_dates_beginsept else '2009-09-15')
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 0)
        self.valid_check_email(params={"status": 0, "subscriptiontype": 4, 'begin_date': '2009-09-15',
                                       "activity": 2, "team": 3}, nb_mail=0, subscriptid=6)

    def test_automatic_new(self):
        Parameter.change_value('member-subscription-mode', 2)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '2')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_select_equal('period', 4)
        self.assert_json_equal('SELECT', 'period', 37)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {"subscriptiontype": 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_json_equal('LABELFORM', 'begin_date', self.dateref_expected)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)
        self.assertEqual(self.json_context['begin_date'], self.dateref_expected.isoformat())

        self.valid_check_email(params={"status": 1, "subscriptiontype": 2, 'period': 37,
                                       "activity": 1, "team": 1}, nb_mail=1)

    def test_automatic_renew(self):
        Parameter.change_value('member-subscription-mode', 2)
        self.add_subscriptions(year=2008, season_id=9, status=2, create_adh_sub=False)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '2')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '3')
        self.assert_json_equal('LABELFORM', 'begin_date', self.dateref_expected if not self.is_dates_beginsept else '2009-09-15')
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)
        self.assertEqual(self.json_context['begin_date'], self.dateref_expected.isoformat() if not self.is_dates_beginsept else '2009-09-15')
        self.valid_check_email(params={"status": 1, "subscriptiontype": 4, 'begin_date': '2009-09-15',
                                       "activity": 2, "team": 3}, nb_mail=1, subscriptid=6)

    def test_withmoderationfornew_new(self):
        Parameter.change_value('member-subscription-mode', 3)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '0')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '2')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_select_equal('period', 4)
        self.assert_json_equal('SELECT', 'period', 37)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 0)

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {"subscriptiontype": 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '0')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '1')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '1')
        self.assert_json_equal('DATE', 'begin_date', self.dateref_expected)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 0)

        self.valid_check_email(params={"status": 0, "subscriptiontype": 2, 'period': 37,
                                       "activity": 1, "team": 1}, nb_mail=0)

    def test_withmoderationfornew_renew(self):
        Parameter.change_value('member-subscription-mode', 3)
        self.add_subscriptions(year=2008, season_id=9, status=2, create_adh_sub=False)
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '2')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '3')
        self.assert_json_equal('LABELFORM', 'begin_date', self.dateref_expected if not self.is_dates_beginsept else '2009-09-15')
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)
        self.assertEqual(self.json_context['begin_date'], self.dateref_expected.isoformat() if not self.is_dates_beginsept else '2009-09-15')
        self.valid_check_email(params={"status": 1, "subscriptiontype": 4, 'begin_date': '2009-09-15',
                                       "activity": 2, "team": 3}, nb_mail=1, subscriptid=6)

    def test_withmoderationfornew_withdelay_tolow(self):
        Parameter.change_value('member-subscription-mode', 3)
        Parameter.change_value('member-subscription-delaytorenew', 30)
        self.factory.xfer = SubscriptionAddModify()
        begin_date = self.dateref_expected - timedelta(days=365 + 10)
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 2, 'dateref': '2009-10-01',
                                                                 'subscriptiontype': 4, 'begin_date': begin_date, 'season': 9, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.user = self.joe_adh.user

        new_date = date(year=begin_date.year + 1, month=begin_date.month, day=begin_date.day)
        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '2')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '3')
        self.assert_json_equal('LABELFORM', 'begin_date', new_date)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)
        self.assertEqual(self.json_context['begin_date'], new_date.isoformat())

    def test_withmoderationfornew_withdelay_tohigh(self):
        Parameter.change_value('member-subscription-mode', 3)
        Parameter.change_value('member-subscription-delaytorenew', 30)
        self.factory.xfer = SubscriptionAddModify()
        begin_date = self.dateref_expected - timedelta(days=365 + 50)
        self.calljson('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'status': 2, 'dateref': '2009-10-01',
                                                                 'subscriptiontype': 4, 'begin_date': begin_date, 'season': 9, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.user = self.joe_adh.user

        self.factory.xfer = SubscriptionAddForCurrent()
        self.calljson('/diacamma.member/subscriptionAddForCurrent', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddForCurrent')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'adherent', '5')
        self.assert_json_equal('LABELFORM', 'season', '10')
        self.assert_json_equal('LABELFORM', 'status', '1')
        self.assert_select_equal('subscriptiontype', {2: "Periodic [76,44 €]", 1: "Annually [76,44 €]", 4: "Calendar [76,44 €]", 3: "Monthly [76,44 €]"})
        self.assert_json_equal('SELECT', 'subscriptiontype', '4')
        self.assert_select_equal('activity', {1: "activity1", 2: "activity2"})
        self.assert_json_equal('SELECT', 'activity', '2')
        self.assert_select_equal('team', {1: "team1", 2: "team2", 3: "team3"})
        self.assert_json_equal('SELECT', 'team', '3')
        self.assert_json_equal('LABELFORM', 'begin_date', self.dateref_expected)
        self.assertEqual(self.json_context['autocreate'], 1)
        self.assertEqual(self.json_context['status'], 1)
        self.assertEqual(self.json_context['begin_date'], self.dateref_expected.isoformat())


class TaxtReceiptTest(InvoiceTest):

    def setUp(self):
        InvoiceTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()
        create_account(['708'], 3)
        default_adherents(True)
        change_ourdetail()

    def test_no_valid(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        bill_id = self._create_bill(details, 1, '2015-04-01', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supporting': bill_id, 'amount': '100.0', 'payer': "Ma'a Dalton", 'date': '2015-04-03', 'mode': 0, 'reference': 'abc', 'bank_account': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '0'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 4)
        self.assert_json_equal('LABELFORM', 'result', [100.00, 0.00, 100.00, 100.00, 0.00])

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

    def test_valid_only_bill(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        bill_id = self._create_bill(details, 1, '2015-04-01', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supporting': bill_id, 'amount': '100.0', 'payer': "Ma'a Dalton", 'date': '2015-04-03', 'mode': 0, 'reference': 'abc', 'bank_account': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 2)
        self.assert_json_equal('LABELFORM', 'result', [100.00, 0.00, 100.00, 100.00, 0.00])

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

    def test_valid(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        bill_id = self._create_bill(details, 1, '2015-04-01', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supporting': bill_id, 'amount': '100.0', 'payer': "Ma'a Dalton", 'date': '2015-04-03', 'mode': 0, 'reference': 'abc', 'bank_account': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;3"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 4)
        self.assert_json_equal('LABELFORM', 'result', [100.00, 0.00, 100.00, 100.00, 100.00])

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 1)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-04-03')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'espèces')

        self.assertTrue(DocumentContainer.objects.filter(metadata='TaxReceipt-2').first() is None)
        self.factory.xfer = TaxReceiptPrint()
        self.calljson('/diacamma.member/taxReceiptPrint', {'taxreceipt': '2', 'PRINT_MODE': 3, 'MODEL': 8}, False)
        self.assert_observer('core.print', 'diacamma.member', 'taxReceiptPrint')
        self.save_pdf()

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 100.0)

        self.factory.xfer = TaxReceiptPrint()
        self.calljson('/diacamma.member/taxReceiptPrint', {'taxreceipt': '2', 'PRINT_PERSITENT_MODE': 0, 'PRINT_MODE': 3, 'MODEL': 8}, False)
        self.assert_observer('core.print', 'diacamma.member', 'taxReceiptPrint')
        check_pdfreport(self, 'TaxReceipt', 2, True)
        self.save_pdf()

    def test_valid_onlyone(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1},
                   {'article': 1, 'designation': 'article 1', 'price': '100.00', 'quantity': 1}]
        bill_id = self._create_bill(details, 1, '2015-06-21', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': bill_id,
                                                           'amount': '200.0', 'payer': "Ma'a Dalton", 'date': '2015-06-30', 'mode': 3, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 2}]
        self._create_bill(details, 1, '2015-11-11', 4, True)

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;2;3;4;5;6;7"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        current_year = FiscalYear.get_current()
        current_year.closed()

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 7 + 5)
        self.assert_json_equal('LABELFORM', 'result', [400.00, 0.00, 400.00, 200.00, 200.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 1)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-06-30')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'carte de crédit')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 100.0)

    def test_multi(self):
        current_year = FiscalYear.get_current()
        current_year.begin = '2014-09-01'
        current_year.end = '2015-08-31'
        current_year.save()

        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1},
                   {'article': 1, 'designation': 'article 1', 'price': '100.00', 'quantity': 1}]
        bill_id1 = self._create_bill(details, 1, '2014-10-23', 4, True)
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 2}]
        bill_id2 = self._create_bill(details, 1, '2014-11-11', 4, True)

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '250.0', 'payer': "Ma'a Dalton", 'date': '2014-12-03', 'mode': 1, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '150.0', 'payer': "Ma'a Dalton", 'date': '2015-02-25', 'mode': 2, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;2;3;4;5;6;7;8;9"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 11)
        self.assert_json_equal('LABELFORM', 'result', [400.00, 0.00, 400.00, 400.00, 400.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2014, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2014}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 2)
        self.assert_json_equal('LABELFORM', 'total', 300.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-02-25')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'chèque, virement')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 300.0)

    def test_waiver_fee(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        self._create_bill(details, 1, '2015-03-29', 4, True)
        add_entry(1, 2, '2015-03-15', 'depense 1', '-1|12|0|100.000000|0|0|None|\n-2|1|4|-100.000000|0|0|None|', True)

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '0', "entryline": "1;2"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountLink()
        self.calljson('/diacamma.accounting/entryAccountLink', {'year': '1', 'journal': '0', 'filter': '0', 'entryline': '4;1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountLink')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '0'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 4)
        self.assert_json_equal('LABELFORM', 'result', [100.00, 100.00, 0.00, 0.00, 0.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 1)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-03-15')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'abandon de frais')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 100.0)

    def test_waiver_revenu(self):
        details = [{'article': 2, 'designation': 'article 2', 'price': '100.00', 'quantity': 1}]
        self._create_bill(details, 2, '2015-03-25', 4, True)
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        self._create_bill(details, 3, '2015-03-29', 4, True)

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '0', "entryline": "1;2;3;4"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountLink()
        self.calljson('/diacamma.accounting/entryAccountLink', {'year': '1', 'journal': '0', 'filter': '0', 'entryline': '3;1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountLink')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '0'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 4)
        self.assert_json_equal('LABELFORM', 'result', [0.00, 0.00, 0.00, 0.00, 0.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 1)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-03-25')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'abandon de revenus ou de produits')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 100.0)

    def test_double_year(self):
        current_year = FiscalYear.get_current()

        # Last year
        old_year = FiscalYear.objects.create(begin='2014-01-01', end='2014-12-31', status=1)
        old_year.set_has_actif()
        fill_accounts_fr(old_year, True, False)
        create_account(['708'], 3, old_year)
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1},
                   {'article': 1, 'designation': 'article 1', 'price': '100.00', 'quantity': 1}]
        bill_id1 = self._create_bill(details, 1, '2014-10-23', 4, True)
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 2}]
        bill_id2 = self._create_bill(details, 1, '2014-11-11', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '250.0', 'payer': "Ma'a Dalton", 'date': '2014-12-03', 'mode': 1, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '2', 'journal': '0', "entryline": "1;2;3;4;5;6;7"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        old_year.set_context(self.factory.xfer)
        old_year.closed()

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '2', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 8 + 8)
        self.assert_json_equal('LABELFORM', 'result', [400.00, 0.00, 400.00, 250.00, 250.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2014, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')
        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2014}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        # New year
        current_year.last_fiscalyear = old_year
        current_year.set_has_actif()
        current_year.run_report_lastyear(True)

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '150.0', 'payer': "Ma'a Dalton", 'date': '2015-02-25', 'mode': 2, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "25;26;27"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountLink()
        self.calljson('/diacamma.accounting/entryAccountLink', {'year': '1', 'journal': '0', 'filter': '0', 'entryline': '21;22;23;24;25;26'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountLink')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '0'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 8 + 3)
        self.assert_json_equal('LABELFORM', 'result', [0.00, 0.00, 0.00, 400.00, 400.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')
        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2014, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')
        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2014}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

    def test_bill_and_asset(self):
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1}]
        bill_id1 = self._create_bill(details, 1, '2015-04-01', 4, True)
        asset_id = self._create_bill(details, 2, '2015-04-02', 4, True)
        bill_id2 = self._create_bill(details, 1, '2015-04-04', 4, True)

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': bill_id2,
                                                           'amount': '100.0', 'payer': "Ma'a Dalton", 'date': '2015-04-05', 'mode': 1, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;2;3;4;5;6;7;8"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 8)
        self.assert_json_equal('LABELFORM', 'result', [100.00, 0.00, 100.00, 100.00, 100.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 1)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-04-05')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'chèque')

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supporting': bill_id1, 'amount': '100.0',
                                                           'date': '2015-04-03', 'mode': 6, 'linked_supporting': asset_id}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = TaxReceiptCheckOnlyOn()
        self.calljson('/diacamma.member/taxReceiptCheckOnlyOn', {'taxreceipt': 4, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheckOnlyOn')

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 4}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 9)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 3)
        self.assert_json_equal('LABELFORM', 'total', 100.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-04-05')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'chèque')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 100.0)

    def test_multi_with_reason(self):
        Params.setvalue("member-tax-reason-payoff", "708:GGG{[br/]}")
        current_year = FiscalYear.get_current()
        current_year.begin = '2015-01-01'
        current_year.end = '2015-12-31'
        current_year.save()

        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1},
                   {'article': 1, 'designation': 'article 1', 'price': '100.00', 'quantity': 1}]
        bill_id1 = self._create_bill(details, 1, '2015-04-23', 4, True)
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 2}]
        bill_id2 = self._create_bill(details, 1, '2015-05-11', 4, True)

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '250.0', 'payer': "Ma'a Dalton", 'date': '2015-06-03', 'mode': 1, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': "%d;%d" % (bill_id1, bill_id2),
                                                           'amount': '150.0', 'payer': "Ma'a Dalton", 'date': '2015-08-25', 'mode': 2, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;2;3;4;5;6;7;8;9"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 11)
        self.assert_json_equal('LABELFORM', 'result', [400.00, 0.00, 400.00, 400.00, 400.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2014, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2014}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)

        self.factory.xfer = TaxReceiptShow()
        self.calljson('/diacamma.member/taxReceiptShow', {'taxreceipt': 3}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptShow')
        self.assert_count_equal('', 11)
        self.assert_json_equal('LABELFORM', 'num', None)
        self.assert_json_equal('LABELFORM', 'third', 'Dalton Joe')
        self.assert_count_equal('entryline', 2)
        self.assert_json_equal('LABELFORM', 'total', 300.0)
        self.assert_json_equal('LABELFORM', 'date_payoff', '2015-08-25')
        self.assert_json_equal('LABELFORM', 'mode_payoff', 'chèque, virement')
        self.assert_json_equal('LABELFORM', '__empty__', '')
        self.assert_json_equal('LABELFORM', 'type_gift', 'GGG')

        self.factory.xfer = TaxReceiptValid()
        self.calljson('/diacamma.member/taxReceiptValid', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptValid')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 1)
        self.assert_json_equal('', 'taxreceipt/@0/num', 1)
        self.assert_json_equal('', 'taxreceipt/@0/third', 'Dalton Joe')
        self.assert_json_equal('', 'taxreceipt/@0/total', 300.0)

    def test_exclude_bankcode(self):
        Params.setvalue("member-tax-exclude-payoff", "1")
        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 1},
                   {'article': 1, 'designation': 'article 1', 'price': '100.00', 'quantity': 1}]
        bill_id = self._create_bill(details, 1, '2015-06-21', 4, True)
        self.factory.xfer = PayoffAddModify()
        self.calljson('/diacamma.payoff/payoffAddModify', {'SAVE': 'YES', 'supportings': bill_id,
                                                           'amount': '200.0', 'payer': "Ma'a Dalton", 'date': '2015-06-30', 'mode': 3, 'reference': 'abc', 'bank_account': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.payoff', 'payoffAddModify')

        details = [{'article': 4, 'designation': 'article 4', 'price': '100.00', 'quantity': 2}]
        self._create_bill(details, 1, '2015-11-11', 4, True)

        self.factory.xfer = EntryAccountClose()
        self.calljson('/diacamma.accounting/entryAccountClose',
                      {'CONFIRME': 'YES', 'year': '1', 'journal': '2', "entryline": "1;2;3;4;5;6;7"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.accounting', 'entryAccountClose')

        current_year = FiscalYear.get_current()
        current_year.closed()

        self.factory.xfer = EntryAccountList()
        self.calljson('/diacamma.accounting/entryAccountList',
                      {'year': '1', 'journal': '0', 'filter': '2'}, False)
        self.assert_observer('core.custom', 'diacamma.accounting', 'entryAccountList')
        self.assert_count_equal('entryline', 7 + 5)
        self.assert_json_equal('LABELFORM', 'result', [400.00, 0.00, 400.00, 200.00, 200.00])

        self.factory.xfer = TaxReceiptCheck()
        self.calljson('/diacamma.member/taxReceiptCheck', {'year': 2015, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'taxReceiptCheck')

        self.factory.xfer = TaxReceiptList()
        self.calljson('/diacamma.member/taxReceiptList', {'year': 2015}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'taxReceiptList')
        self.assert_count_equal('taxreceipt', 0)


class AdherentConnectionTest(BaseAdherentTest):

    smtp_port = 3425

    def setUp(self):
        BaseAdherentTest.setUp(self)
        Parameter.change_value('member-family-type', 3)
        Parameter.change_value("member-fields", "firstname;lastname;tel1;tel2;email;family")
        Parameter.change_value('member-connection', 2)
        set_parameters([])
        AdherentConnectionTest.smtp_port += 1
        configSMTP('localhost', AdherentConnectionTest.smtp_port)
        change_ourdetail()

    def test_connection_ask_failed(self):
        self.assertEqual(LucteriosUser.objects.all().count(), 1)
        self.add_subscriptions(year=2008, season_id=9)
        self.calljson('/diacamma.member/askAdherentAccess', {})
        self.assert_observer('core.custom', 'diacamma.member', 'askAdherentAccess')
        self.assertEqual(len(self.json_context), 0)
        self.assertEqual(len(self.json_actions), 2)
        self.assert_count_equal('', 3)
        self.assert_json_equal('EDIT', "email", '')

        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "inconnu@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Ce courriel ne correspond pas avec un adhérent actif !')

            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "Joe.Dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Ce courriel ne correspond pas avec un adhérent actif !')
            self.assertEqual(0, server.count())
        finally:
            server.stop()
        self.assertEqual(LucteriosUser.objects.all().count(), 1)

    def test_connection_ask_simple(self):
        self.assertEqual(LucteriosUser.objects.all().count(), 1)
        self.add_subscriptions()
        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "Joe.Dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Les paramètres de connexion ont été envoyé.')

            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "William.Dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Les paramètres de connexion ont été envoyé.')

            self.assertEqual(2, server.count())
            _msg, msg = server.check_first_message('Mot de passe de connexion', 2)
            self.assertEqual('text/html', msg.get_content_type())
            self.assertEqual('base64', msg.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg.get_payload())
            self.assertEqual('<html><p>Bienvenue<br/><br/>Confirmation de connexion à votre application :'
                             '<br/> - Identifiant : joeD<br/> - Mot de passe : ', message[:124])
            password = message[124:].split('<br/>')[0]
        finally:
            server.stop()

        self.calljson('/CORE/authentification', {'login': 'joeD', 'password': password})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.calljson('/lucterios.contacts/account', {}, 'get')
        self.assert_observer('core.custom', 'lucterios.contacts', 'account')
        self.assert_json_equal('LABELFORM', 'genre', 1)
        self.assert_json_equal('LABELFORM', 'firstname', "Joe")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_json_equal('LINK', 'email', "Joe.Dalton@worldcompany.com")
        self.assert_count_equal('subscription', 1)
        self.assertEqual(LucteriosUser.objects.all().count(), 3)
        self.assertEqual(LucteriosUser.objects.filter(is_active=True).count(), 3)

    def test_connection_ask_family(self):
        self.assertEqual(LucteriosUser.objects.all().count(), 1)
        self.prep_subscription_family()
        server = TestReceiver()
        server.start(AdherentConnectionTest.smtp_port)
        try:
            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Les paramètres de connexion ont été envoyé.')

            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "Joe.Dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Les paramètres de connexion ont été envoyé.')

            self.calljson('/diacamma.member/askAdherentAccess', {"CONFIRME": "YES", "email": "Avrel.Dalton@worldcompany.com"})
            self.assert_observer('core.dialogbox', 'diacamma.member', 'askAdherentAccess')
            self.assert_json_equal('', 'text', 'Les paramètres de connexion ont été envoyé.')

            self.assertEqual(3, server.count())

            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(0)[1])
            self.assertEqual(['dalton@worldcompany.com'], server.get(0)[2])
            _msg, msg1 = server.check_first_message('Mot de passe de connexion', 2)
            self.assertEqual('text/html', msg1.get_content_type())
            self.assertEqual('base64', msg1.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg1.get_payload())
            self.assertEqual('<html><p>Bienvenue<br/><br/>Confirmation de connexion à votre application :'
                             '<br/> - Identifiant : LES DALTONS<br/> - Mot de passe : ', message[:131])
            password1 = message[131:].split('<br/>')[0]

            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(1)[1])
            self.assertEqual(['Joe.Dalton@worldcompany.com'], server.get(1)[2])
            _msg, msg2 = server.get_msg_index(1, 'Mot de passe de connexion')
            message = decode_b64(msg2.get_payload())
            self.assertEqual('<html><p>Bienvenue<br/><br/>Confirmation de connexion à votre application :'
                             '<br/> - Identifiant : LES DALTONS<br/> - Mot de passe : ', message[:131])
            password2 = message[131:].split('<br/>')[0]

            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(2)[1])
            self.assertEqual(['Avrel.Dalton@worldcompany.com'], server.get(2)[2])
            _msg, msg3 = server.get_msg_index(2, 'Mot de passe de connexion')
            message = decode_b64(msg3.get_payload())
            self.assertEqual('<html><p>Bienvenue<br/><br/>Confirmation de connexion à votre application :'
                             '<br/> - Identifiant : LES DALTONS<br/> - Mot de passe : ', message[:131])
            password3 = message[131:].split('<br/>')[0]
        finally:
            server.stop()

        self.calljson('/CORE/authentification', {'login': 'LES DALTONS', 'password': password1})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'BADAUTH')

        self.calljson('/CORE/authentification', {'login': 'LES DALTONS', 'password': password2})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'BADAUTH')

        self.calljson('/CORE/authentification', {'login': 'LES DALTONS', 'password': password3})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.calljson('/lucterios.contacts/account', {}, 'get')
        self.assert_observer('core.custom', 'lucterios.contacts', 'account')
        self.assert_json_equal('LABELFORM', 'legalentity_structure_type', "famille")
        self.assert_json_equal('LABELFORM', 'legalentity_name', "LES DALTONS")
        self.assert_json_equal('LINK', 'legalentity_email', "dalton@worldcompany.com")
        self.assert_action_equal('POST', self.get_json_path('#btn_edit/action'), ("Editer", "mdi:mdi-pencil-outline",
                                                                                  "lucterios.contacts", "currentLegalEntityModify", 0, 1, 1, {'legal_entity': 7}))
        self.assert_count_equal('subscription', 2)
        self.assertEqual(LucteriosUser.objects.all().count(), 2)
        self.assertEqual(LucteriosUser.objects.filter(is_active=True).count(), 2)

        self.calljson('/lucterios.contacts/currentLegalEntityModify', {'legal_entity': 7})
        self.assert_observer('core.custom', 'lucterios.contacts', 'currentLegalEntityModify')
        self.assert_count_equal('', 12)

    def test_disable_connexion(self):
        self.add_subscriptions()
        adh_luke = Adherent.objects.get(firstname='Lucky')
        adh_luke.user = LucteriosUser.objects.create(username='lucky', first_name=adh_luke.firstname, last_name=adh_luke.lastname, email=adh_luke.email, is_active=False)
        adh_luke.save()
        new_adh = create_adherent("Ma'a", 'Dalton', '1961-04-12')
        new_adh.user = LucteriosUser.objects.create(username='maa', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()
        new_adh = create_adherent("Rantanplan", 'Chien', '2010-01-01')
        new_adh.user = LucteriosUser.objects.create(username='rantanplan', first_name=new_adh.firstname, last_name=new_adh.lastname, email=new_adh.email, is_active=True)
        new_adh.save()
        Responsability.objects.create(individual=new_adh, legal_entity_id=1)

        self.assertEqual(LucteriosUser.objects.all().count(), 4)
        self.assertEqual(len(LucteriosUser.objects.filter(is_active=True)), 3)
        self.factory.xfer = AdherentDisableConnection()
        self.calljson('/diacamma.member/adherentDisableConnection', {'CONFIRME': 'YES', 'RELOAD': 'YES'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentDisableConnection')
        self.assert_json_equal('LABELFORM', 'info', '{[center]}{[b]}Résultat{[/b]}{[/center]}{[br/]}1 connexion(s) supprimée(s).', True)
        self.assertEqual(LucteriosUser.objects.all().count(), 4)
        self.assertEqual(len(LucteriosUser.objects.filter(is_active=True)), 2)

    def test_add_active_group(self):
        self.add_subscriptions()
        active_group = LucteriosGroup.objects.create(name='active')
        Parameter.change_value('member-activegroup', active_group.id)
        adh_avrel = Adherent.objects.get(firstname='Avrel')
        adh_avrel.user = LucteriosUser.objects.create(username='avrelD', first_name=adh_avrel.firstname, last_name=adh_avrel.lastname, email=adh_avrel.email, is_active=True)
        adh_avrel.user.set_password('abcd')
        adh_avrel.user.save()
        adh_avrel.save()
        self.assertEqual([str(grp) for grp in LucteriosUser.objects.get(username='avrelD').groups.all()], [])

        self.calljson('/CORE/authentification', {'login': 'avrelD', 'password': 'abcd'})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.assertEqual([str(grp) for grp in LucteriosUser.objects.get(username='avrelD').groups.all()], ['active'])

    def test_remove_active_group(self):
        self.add_subscriptions(year=2007, season_id=7, status=2)
        active_group = LucteriosGroup.objects.create(name='active')
        Parameter.change_value('member-activegroup', active_group.id)
        adh_avrel = Adherent.objects.get(firstname='Avrel')
        adh_avrel.user = LucteriosUser.objects.create(username='avrelD', first_name=adh_avrel.firstname, last_name=adh_avrel.lastname, email=adh_avrel.email, is_active=True)
        adh_avrel.user.set_password('abcd')
        adh_avrel.user.groups.add(active_group)
        adh_avrel.user.save()
        adh_avrel.save()
        self.assertEqual([str(grp) for grp in LucteriosUser.objects.get(username='avrelD').groups.all()], ['active'])

        self.calljson('/CORE/authentification', {'login': 'avrelD', 'password': 'abcd'})
        self.assert_observer('core.auth', 'CORE', 'authentification')
        self.assert_json_equal('', '', 'OK')

        self.assertEqual([str(grp) for grp in LucteriosUser.objects.get(username='avrelD').groups.all()], [])
