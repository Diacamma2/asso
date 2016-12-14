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
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_user_dir
from lucterios.contacts.views import ContactImport
from lucterios.contacts.tests_contacts import change_ourdetail

from diacamma.member.test_tools import default_season, default_financial, default_params,\
    default_adherents, default_subscription, set_parameters
from diacamma.member.views import AdherentActiveList, AdherentAddModify, AdherentShow,\
    SubscriptionAddModify, SubscriptionShow, LicenseAddModify, LicenseDel,\
    AdherentDoc, AdherentLicense, AdherentLicenseSave, AdherentStatistic,\
    AdherentRenewList, AdherentRenew, SubscriptionTransition, AdherentCommand,\
    AdherentCommandDelete, AdherentCommandModify
from diacamma.invoice.views import BillList, BillTransition, BillFromQuotation,\
    BillAddModify

from diacamma.member.models import Season


class AdherentTest(LucteriosTest):

    def __init__(self, methodName):
        LucteriosTest.__init__(self, methodName)
        if date.today().month > 8:
            self.dateref_expected = date(
                2009, date.today().month, date.today().day)
        else:
            self.dateref_expected = date(
                2010, date.today().month, date.today().day)

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()
        set_parameters(
            ["team", "activite", "age", "licence", "genre", 'numero', 'birth'])

    def test_defaultlist(self):
        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/*', 2 + 11 + 2 + 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lblteam"]', '{[b]}group{[/b]}')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lblactivity"]', '{[b]}passion{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="status"]/CASE', 3)
        self.assert_count_equal(
            'COMPONENTS/CHECKLIST[@name="age"]/CASE', 8)
        self.assert_count_equal(
            'COMPONENTS/CHECKLIST[@name="team"]/CASE', 3)
        self.assert_count_equal(
            'COMPONENTS/CHECKLIST[@name="activity"]/CASE', 2)
        self.assert_xml_equal(
            'COMPONENTS/DATE[@name="dateref"]', self.dateref_expected.isoformat())
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="genre"]/CASE', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER', 7)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/ACTIONS/ACTION', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="num"]', "N°")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="firstname"]', "prénom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="lastname"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="tel1"]', "tel1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="tel2"]', "tel2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="email"]', "courriel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER[@name="license"]', "licence")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

    def test_add_adherent(self):
        self.factory.xfer = AdherentAddModify()
        self.call('/diacamma.member/adherentAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal('COMPONENTS/*', 1 + 2 * (8 + 3 + 2) + 2)

        self.factory.xfer = AdherentAddModify()
        self.call('/diacamma.member/adherentAddModify', {"address": 'Avenue de la Paix{[newline]}BP 987',
                                                         "comment": 'no comment', "firstname": 'Marie', "lastname": 'DUPOND',
                                                         "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                         "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'marie.dupond@worldcompany.com',
                                                         "birthday": "1998-08-04", "birthplace": "Fort-de-France",
                                                         "genre": "2"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 2}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 6) + 1 + 2 + 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="dateref"]', formats.date_format(self.dateref_expected, "DATE_FORMAT"))
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Marie")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "DUPOND")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="num"]', "1")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="birthday"]', "4 août 1998")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="birthplace"]', "Fort-de-France")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Benjamins")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 6)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 0)

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="birthday"]', "4 août 1998")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Cadets")

        self.factory.xfer = AdherentAddModify()
        self.call('/diacamma.member/adherentAddModify', {"address": 'Avenue de la Paix{[newline]}BP 987',
                                                         "comment": 'no comment', "firstname": 'Jean', "lastname": 'DUPOND',
                                                         "city": 'ST PIERRE', "country": 'MARTINIQUE', "tel2": '06-54-87-19-34', "SAVE": 'YES',
                                                         "tel1": '09-96-75-15-00', "postal_code": '97250', "email": 'jean.dupond@worldcompany.com',
                                                         "birthday": "2000-06-22", "birthplace": "Fort-de-France",
                                                         "genre": "1"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 3}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Jean")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "DUPOND")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="num"]', "2")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="birthday"]', "22 juin 2000")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Poussins")

    def test_add_subscription(self):
        default_adherents()

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Avrel")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "Dalton")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 6)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="status"]', "status")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="season"]', "saison")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="subscriptiontype"]', "type de cotisation")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="begin_date"]', "date de début")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="end_date"]', "date de fin")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER[@name="license_set"]', "licence")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 0)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'subscriptionAddModify')

        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 17)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="season"]/CASE', 20)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]/CASE', 4)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]/CASE[1]', "Annually [76.44€]")
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]/CASE[2]', "Periodic [76.44€]")
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]/CASE[3]', "Monthly [76.44€]")
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]/CASE[4]', "Calendar [76.44€]")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_team"]', '{[b]}group{[/b]}')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_activity"]', '{[b]}passion{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="team"]/CASE', 3)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="activity"]/CASE', 2)

    def test_add_subscription_annually(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 17)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="season"]', '10')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="status"]/CASE', 2)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="status"]', '2')
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]', '1')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="seasondates"]', "1 sep. 2009 => 31 août 2010")

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'status': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="status"]', "validé")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Annually")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 août 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team2 [activity1] abc123")

    def test_add_subscription_periodic(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 2}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 17)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="season"]', '10')
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]', '2')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="period"]/CASE', 4)
        self.assert_attrib_equal(
            'COMPONENTS/SELECT[@name="period"]/CASE[3]', 'id', '39')

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 2, 'season': 10, 'period': 39, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Periodic")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 mars 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 mai 2010")

    def test_add_subscription_monthly(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 3}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 17)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="season"]', '10')
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]', '3')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="month"]/CASE', 12)
        self.assert_attrib_equal(
            'COMPONENTS/SELECT[@name="month"]/CASE[4]', 'id', "2009-12")

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 3, 'season': 10, 'month': '2009-12', 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Monthly")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 décembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 décembre 2009")

    def test_add_subscription_calendar(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 4}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 17)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="season"]', '10')
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]', '4')
        self.assert_xml_equal(
            'COMPONENTS/DATE[@name="begin_date"]', self.dateref_expected.isoformat())

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 4, 'season': 10, 'begin_date': '2009-10-01', 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Calendar")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 octobre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "30 septembre 2010")

    def test_show_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'status': 2, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="status"]', 'validé')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="team"]', "group")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="activity"]', "passion")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="value"]', "N° licence")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="team"]', "team2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="value"]', "abc123")

        self.factory.xfer = LicenseAddModify()
        self.call('/diacamma.member/licenseAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'licenseAddModify')
        self.assert_count_equal('COMPONENTS/*', 7)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_team"]', '{[b]}group{[/b]}')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_activity"]', '{[b]}passion{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="team"]/CASE', 3)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="activity"]/CASE', 2)

        self.factory.xfer = LicenseAddModify()
        self.call('/diacamma.member/licenseAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1, 'team': 1, 'activity': 2, 'value': '987xyz'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'licenseAddModify')

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[1]/VALUE[@name="license"]', "team2 [activity1] abc123{[br/]}team1 [activity2] 987xyz")

        self.factory.xfer = AdherentLicense()
        self.call('/diacamma.member/adherentLicense',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentLicense')
        self.assert_count_equal('COMPONENTS/*', 21)
        self.assert_xml_equal(
            'COMPONENTS/EDIT[@name="value_1"]', 'abc123')
        self.assert_xml_equal(
            'COMPONENTS/EDIT[@name="value_2"]', '987xyz')

        self.factory.xfer = AdherentLicenseSave()
        self.call('/diacamma.member/adherentLicenseSave',
                  {'adherent': 2, 'dateref': '2009-10-01', 'value_1': 'abcd1234', 'value_2': '9876wxyz'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentLicenseSave')

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[1]/VALUE[@name="license"]', "team2 [activity1] abcd1234{[br/]}team1 [activity2] 9876wxyz")

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD', 2)

        self.factory.xfer = LicenseDel()
        self.call('/diacamma.member/licenseDel',
                  {'CONFIRME': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1, 'license': 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'licenseDel')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2009-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD', 1)

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="bill_type"]', "facture")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

    def add_subscriptions(self, year=2009, season_id=10):
        default_adherents()
        default_subscription()
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 3, 'dateref': '%s-10-01' % year,
                                                             'subscriptiontype': 2, 'period': 37 + (year - 2009) * 4, 'season': season_id, 'team': 1, 'activity': 1, 'value': '645'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 4, 'dateref': '%s-10-01' % year,
                                                             'subscriptiontype': 3, 'month': '%s-10' % year, 'season': season_id, 'team': 3, 'activity': 1, 'value': '489'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'dateref': '%s-10-01' % year,
                                                             'subscriptiontype': 4, 'begin_date': '%s-09-15' % year, 'season': season_id, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 6, 'dateref': '%s-10-01' % year, 'subscriptiontype': 1, 'season': season_id, 'team': 1, 'activity': 2, 'value': '159'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

    def test_subscription_bydate(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/*', 2 + 11 + 3 + 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="3"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="4"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-11-15'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="3"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2010-01-20'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-09-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="3"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2010-09-10'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)

    def test_subscription_byage(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2010-09-10'}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Poussins")
        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 3, 'dateref': '2010-09-10'}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Benjamins")
        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 4, 'dateref': '2010-09-10'}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Juniors")
        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 5, 'dateref': '2010-09-10'}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Espoirs")
        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 6}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="age_category"]', "Seniors")

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'age': '1;2;3'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 2)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'age': '4;5;6'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 2)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'age': '7;8'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'age': '1;3;5;7'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)

    def test_subscription_byteam(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'team': '1'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 2)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'team': '2;3'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)

    def test_subscription_byactivity(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'activity': '1'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'activity': '2'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 2)

    def test_subscription_bygenre(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01', 'genre': '2'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

    def test_subscription_doc(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_count_equal(
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 6) + 1 + 2 + (2 * 2 + 3) + 2 + 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_doc_1"]', "Doc 1")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_doc_2"]', "Doc 2")
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_1"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_2"]', "0")

        self.factory.xfer = AdherentDoc()
        self.call('/diacamma.member/adherentDoc',
                  {'adherent': 2, 'dateref': '2009-10-01', 'doc_1': 1, 'doc_2': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentDoc')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_1"]', "1")
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_2"]', "0")

        self.factory.xfer = AdherentDoc()
        self.call('/diacamma.member/adherentDoc',
                  {'adherent': 2, 'dateref': '2009-10-01', 'doc_1': 0, 'doc_2': 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentDoc')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_1"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/CHECK[@name="doc_2"]', "1")

    def test_subscription_withoutparams(self):
        self.add_subscriptions()
        set_parameters([])

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/*', 2 + 3 + 3 + 2)

        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/ACTIONS/ACTION', 4)

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal(
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 2) + 1 + 2 + (2 * 2 + 3) + 2 + 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 5)

        self.factory.xfer = AdherentAddModify()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal('COMPONENTS/*', 1 + 2 * (8 + 3 + 0) + 2)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('COMPONENTS/*', 11)

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 13)

    def test_statistic(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentStatistic()
        self.call('/diacamma.member/adherentStatistic',
                  {'season': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentStatistic')
        self.assert_count_equal('COMPONENTS/*', 4)

        self.factory.xfer = AdherentStatistic()
        self.call('/diacamma.member/adherentStatistic',
                  {'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentStatistic')

        xml_values = self.response_xml.xpath('COMPONENTS/*')
        self.assertEqual(0, (len(xml_values) - 3) % 5, "size of COMPONENTS/* = %d" % len(xml_values))
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="town_1"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="town_1"]/RECORD[2]/VALUE[@name="ratio"]', '{[b]}2{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="town_2"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="town_2"]/RECORD[2]/VALUE[@name="ratio"]', '{[b]}1{[/b]}')

    def test_renew(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentRenewList()
        self.call('/diacamma.member/adherentRenewList',
                  {'dateref': '2010-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentRenewList()
        self.call('/diacamma.member/adherentRenewList',
                  {'dateref': '2010-01-20'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="3"]', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD[@id="4"]', 1)

        self.factory.xfer = AdherentRenew()
        self.call('/diacamma.member/adherentRenew',
                  {'dateref': '2010-10-01', 'CONFIRME': 'YES', 'adherent': '2;5;6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentRenew()
        self.call('/diacamma.member/adherentRenew',
                  {'dateref': '2010-01-20', 'CONFIRME': 'YES', 'adherent': '3;4'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'adherentRenew')

        self.factory.xfer = AdherentRenewList()
        self.call('/diacamma.member/adherentRenewList',
                  {'dateref': '2010-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = AdherentRenewList()
        self.call('/diacamma.member/adherentRenewList',
                  {'dateref': '2010-01-20'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 2}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Annually")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 août 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team2 [activity1] 132")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="season"]', "2010/2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="subscriptiontype"]', "Annually")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="begin_date"]', "1 septembre 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="end_date"]', "31 août 2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="license_set"]', "team2 [activity1] 132")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 3}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Periodic")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "30 novembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team1 [activity1] 645")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="subscriptiontype"]', "Periodic")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="begin_date"]', "1 décembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="end_date"]', "28 février 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="license_set"]', "team1 [activity1] 645")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 4}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Monthly")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 octobre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 octobre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team3 [activity1] 489")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="subscriptiontype"]', "Monthly")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="begin_date"]', "1 janvier 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="end_date"]', "31 janvier 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="license_set"]', "team3 [activity1] 489")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 5}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Calendar")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "15 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "14 septembre 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team3 [activity2] 470")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="season"]', "2010/2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="subscriptiontype"]', "Calendar")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="begin_date"]', "1 octobre 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="end_date"]', "30 septembre 2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[2]/VALUE[@name="license_set"]', "team3 [activity2] 470")

    def test_import(self):
        csv_content = """'nom','prenom','sexe','adresse','codePostal','ville','fixe','portable','mail','DateNaissance','LieuNaissance','Type','NumLicence','Equipe','Activite'
'USIF','Pierre','Homme','37 avenue de la plage','99673','TOUINTOUIN','0502851031','0439423854','pierre572@free.fr','12/09/1961','BIDON SUR MER','Annually','1000029-00099','team1','activity1'
'NOJAXU','Amandine','Femme','11 avenue du puisatier','99247','BELLEVUE','0022456300','0020055601','amandine723@hotmail.fr','27/02/1976','ZINZIN','Periodic#2','1000030-00099','team2','activity2'
'GOC','Marie','Femme','33 impasse du 11 novembre','99150','BIDON SUR MER','0632763718','0310231012','marie762@free.fr','16/05/1998','KIKIMDILUI','Monthly#5','1000031-00099','team3','activity1'
'UHADIK','Marie','Femme','1 impasse de l'Oisan','99410','VIENVITEVOIR','0699821944','0873988470','marie439@orange.fr','27/08/1981','TOUINTOUIN','Calendar#01/11/2009','1000032-00099','team1','activity2'
'FEPIZIBU','Benjamin','Homme','30 cours de la Chartreuse','99247','BELLEVUE','0262009068','0754416670','benjamin475@free.fr','25/03/1979','KIKIMDILUI','Annually','1000033-00099','team2','activity2'
"""
        self.add_subscriptions()
        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2010-01-15'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 3)
        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 5)

        self.factory.xfer = ContactImport()
        self.call('/lucterios.contacts/contactImport', {'step': 1, 'modelname': 'member.Adherent', 'quotechar': "'",
                                                        'delimiter': ',', 'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent': StringIO(csv_content)}, False)
        self.assert_observer(
            'core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('COMPONENTS/*', 7 + 2 * 17)
        self.assert_count_equal('COMPONENTS/SELECT[@name="fld_city"]/CASE', 15)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="fld_country"]/CASE', 16)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/HEADER', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/RECORD', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/ACTIONS', 0)
        self.assert_count_equal('ACTIONS/ACTION', 3)
        self.assert_action_equal('ACTIONS/ACTION[1]', (six.text_type(
            'Retour'), 'images/left.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '0'}))
        self.assert_action_equal('ACTIONS/ACTION[2]', (six.text_type(
            'Ok'), 'images/ok.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '2'}))
        self.assert_count_equal('CONTEXT/PARAM', 8)

        self.factory.xfer = ContactImport()
        self.call('/lucterios.contacts/contactImport', {'step': 2, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                        'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                        "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                        "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                        "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                        'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer(
            'core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('COMPONENTS/*', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/HEADER', 12)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/RECORD', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="CSV"]/ACTIONS', 0)
        self.assert_count_equal('ACTIONS/ACTION', 3)
        self.assert_action_equal('ACTIONS/ACTION[2]', (six.text_type(
            'Ok'), 'images/ok.png', 'lucterios.contacts', 'contactImport', 0, 2, 1, {'step': '3'}))

        self.factory.xfer = ContactImport()
        self.call('/lucterios.contacts/contactImport', {'step': 3, 'modelname': 'member.Adherent', 'quotechar': "'", 'delimiter': ',',
                                                        'encoding': 'utf-8', 'dateformat': '%d/%m/%Y', 'csvcontent0': csv_content,
                                                        "fld_lastname": "nom", "fld_firstname": "prenom", "fld_address": "adresse",
                                                        "fld_postal_code": "codePostal", "fld_city": "ville", "fld_email": "mail",
                                                        "fld_birthday": "DateNaissance", "fld_birthplace": "LieuNaissance", 'fld_subscriptiontype': 'Type',
                                                        'fld_team': 'Equipe', 'fld_activity': 'Activite', 'fld_value': 'NumLicence', }, False)
        self.assert_observer(
            'core.custom', 'lucterios.contacts', 'contactImport')
        self.assert_count_equal('COMPONENTS/*', 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="result"]', "{[center]}{[i]}5 contacts ont été importés{[/i]}{[/center]}")
        self.assert_count_equal('ACTIONS/ACTION', 1)

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 7}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "USIF")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Annually")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 août 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team1 [activity1] 1000029-00099")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 8}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "NOJAXU")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Periodic")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 décembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "28 février 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team2 [activity2] 1000030-00099")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 9}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "GOC")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Monthly")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 janvier 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 janvier 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team3 [activity1] 1000031-00099")

        self.factory.xfer = AdherentShow()
        self.call(
            '/diacamma.member/adherentAddModify', {'adherent': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "UHADIK")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Calendar")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 novembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 octobre 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team1 [activity2] 1000032-00099")

        self.factory.xfer = AdherentShow()
        self.call(
            '/diacamma.member/adherentAddModify', {'adherent': 11}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "FEPIZIBU")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="season"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="subscriptiontype"]', "Annually")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="begin_date"]', "1 septembre 2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="end_date"]', "31 août 2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscription"]/RECORD[1]/VALUE[@name="license_set"]', "team2 [activity2] 1000033-00099")

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2010-01-15'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/RECORD', 8)

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 10)

    def test_status_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'status': 1, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="status"]', 'en création')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="team"]', "group")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="activity"]', "passion")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="value"]', "N° licence")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="team"]', "team2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="value"]', "abc123")

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="bill_type"]', "devis")
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

        self.factory.xfer = SubscriptionTransition()
        self.call('/diacamma.member/subscriptionTransition', {'CONFIRME': 'YES', 'subscription': 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTransition')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="status"]', 'validé')

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="bill_type"]', "facture")
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

    def test_valid_bill_of_subscription(self):
        default_adherents()
        default_subscription()

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'status': 1, 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="status"]', 'en création')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="team"]', "group")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="activity"]', "passion")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="value"]', "N° licence")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="team"]', "team2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/RECORD[1]/VALUE[@name="value"]', "abc123")

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = BillAddModify()
        self.call('/diacamma.invoice/billAddModify',
                  {'bill': 1, 'date': '2015-04-01', 'SAVE': 'YES'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.invoice', 'billAddModify')

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="status"]', "en création")
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="bill_type"]', "devis")
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

        self.factory.xfer = BillTransition()
        self.call('/diacamma.invoice/billValid',
                  {'CONFIRME': 'YES', 'bill': 1, 'withpayoff': False, 'TRANSITION': 'valid'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.invoice', 'billValid')

        self.factory.xfer = BillFromQuotation()
        self.call('/diacamma.invoice/billFromQuotation',
                  {'CONFIRME': 'YES', 'bill': 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.invoice', 'billFromQuotation')
        self.assert_attrib_equal(
            "ACTION", "id", "diacamma.invoice/billShow")
        self.assert_count_equal("ACTION/PARAM", 1)
        self.assert_xml_equal("ACTION/PARAM[@name='bill']", "2")

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="status"]', 'validé')

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 0)

        self.factory.xfer = AdherentActiveList()
        self.call('/diacamma.member/adherentList', {'dateref': '2009-10-01', 'status': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 1)

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="bill_type"]', "facture")
        self.assert_xml_equal('COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

    def test_command(self):
        from lucterios.mailing.test_tools import configSMTP, TestReceiver, decode_b64
        Season.objects.get(id=16).set_has_actif()
        self.add_subscriptions(year=2014, season_id=15)

        self.factory.xfer = AdherentRenewList()
        self.call('/diacamma.member/adherentRenewList', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentRenewList')
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD', 3)
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD[@id="2"]', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD[@id="5"]', 1)
        self.assert_count_equal('COMPONENTS/GRID[@name="adherent"]/RECORD[@id="6"]', 1)

        self.factory.xfer = AdherentCommand()
        self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD', 0)

        self.factory.xfer = AdherentCommand()
        self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'adherent': '2;5;6'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD', 3)
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="adherent"]', "Dalton Avrel")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="type"]', "Annually [76.44€]")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="team"]', "team2")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="reduce"]', "0.00€")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="adherent"]', "Dalton Joe")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="type"]', "Calendar [76.44€]")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="team"]', "team3")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="activity"]', "activity2")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="reduce"]', "0.00€")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[3]/VALUE[@name="adherent"]', "Luke Lucky")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[3]/VALUE[@name="type"]', "Annually [76.44€]")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[3]/VALUE[@name="team"]', "team1")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[3]/VALUE[@name="activity"]', "activity2")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[3]/VALUE[@name="reduce"]', "0.00€")
        cmd_file = self.get_first_xpath('CONTEXT/PARAM[@name="CMD_FILE"]').text
        self.assertEqual(cmd_file[-13:], '/tmp/list.cmd')
        self.assertTrue(isfile(cmd_file))

        self.factory.xfer = AdherentCommand()
        self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD', 3)

        self.factory.xfer = AdherentCommandDelete()
        self.call('/diacamma.member/adherentCommandDelete', {'dateref': '2010-10-01', 'CMD_FILE': cmd_file, 'AdhCmd': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentCommandDelete')

        self.factory.xfer = AdherentCommand()
        self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD', 2)

        self.factory.xfer = AdherentCommandModify()
        self.call('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file, 'AdhCmd': '5'}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommandModify')
        self.assert_count_equal('COMPONENTS/*', 16)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="adherent"]', 'Dalton Joe')

        self.factory.xfer = AdherentCommandModify()
        self.call('/diacamma.member/adherentCommandModify', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file,
                                                             'AdhCmd': '5', 'type': '3', 'team': '2', 'activity': '1', 'reduce': '7.5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentCommandModify')

        self.factory.xfer = AdherentCommand()
        self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'CMD_FILE': cmd_file}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentCommand')
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD', 2)
        self.assert_count_equal('COMPONENTS/GRID[@name="AdhCmd"]/HEADER', 7)
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="adherent"]', "Dalton Joe")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="type"]', "Monthly [76.44€]")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="team"]', "team2")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[1]/VALUE[@name="reduce"]', "7.50€")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="adherent"]', "Luke Lucky")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="type"]', "Annually [76.44€]")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="team"]', "team1")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="activity"]', "activity2")
        self.assert_xml_equal('COMPONENTS/GRID[@name="AdhCmd"]/RECORD[2]/VALUE[@name="reduce"]', "0.00€")

        configSMTP('localhost', 1025)
        change_ourdetail()
        server = TestReceiver()
        server.start(1025)
        try:
            self.assertEqual(0, server.count())

            self.factory.xfer = AdherentCommand()
            self.call('/diacamma.member/adherentCommand', {'dateref': '2015-10-01', 'SAVE': 'YES', 'CMD_FILE': cmd_file, 'send_email': True}, False)
            self.assert_observer('core.dialogbox', 'diacamma.member', 'adherentCommand')

            self.assertEqual(2, server.count())
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(0)[1])
            self.assertEqual(['Joe.Dalton@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(0)[2])
            self.assertEqual('mr-sylvestre@worldcompany.com', server.get(1)[1])
            self.assertEqual(['Lucky.Luke@worldcompany.com', 'mr-sylvestre@worldcompany.com'], server.get(1)[2])
            msg, msg_file = server.check_first_message('Nouvelle cotisation', 2, {'To': 'Joe.Dalton@worldcompany.com'})
            self.assertEqual('text/html', msg.get_content_type())
            self.assertEqual('base64', msg.get('Content-Transfer-Encoding', ''))
            message = decode_b64(msg.get_payload())
            self.assertTrue('Bienvenu' in message, message)
            self.assertTrue('devis_A-1_Dalton Joe.pdf' in msg_file.get('Content-Type', ''), msg_file.get('Content-Type', ''))
            self.assertEqual("%PDF".encode('ascii', 'ignore'), b64decode(msg_file.get_payload())[:4])
        finally:
            server.stop()
