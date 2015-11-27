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

from django.utils import formats

from lucterios.framework.test import LucteriosTest
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_user_dir

from diacamma.member.test_tools import default_season, default_financial, default_params,\
    default_adherents, default_subscription, set_parameters
from diacamma.member.views import AdherentActiveList, AdherentAddModify, AdherentShow,\
    SubscriptionAddModify, SubscriptionShow, LicenseAddModify, LicenseDel,\
    AdherentDoc, AdherentLicense, AdherentLicenseSave, AdherentStatistic,\
    AdherentRenewList, AdherentRenew
from diacamma.invoice.views import BillList


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
        self.assert_count_equal('COMPONENTS/*', 2 + 11 + 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lblteam"]', '{[b]}group{[/b]}')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lblactivity"]', '{[b]}passion{[/b]}')
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
            'COMPONENTS/GRID[@name="adherent"]/ACTIONS/ACTION', 4)
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
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 6) + 1 + 2)
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
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 5)
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
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 5)
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
            'COMPONENTS/*', 13)
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
            'COMPONENTS/*', 13)
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="season"]', '10')
        self.assert_xml_equal(
            'COMPONENTS/SELECT[@name="subscriptiontype"]', '1')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="seasondates"]', "1 sep. 2009 => 31 août 2010")

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
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
            'COMPONENTS/*', 13)
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
            'COMPONENTS/*', 13)
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
            'COMPONENTS/*', 13)
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
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 11)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="team"]', "group")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="activity"]', "passion")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="license"]/HEADER[@name="value"]', "valeur")
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
            'COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "76.44€")

    def add_subscriptions(self):
        default_adherents()
        default_subscription()
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 3, 'dateref': '2009-10-01',
                                                             'subscriptiontype': 2, 'period': 37, 'season': 10, 'team': 1, 'activity': 1, 'value': '645'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 4, 'dateref': '2009-10-01',
                                                             'subscriptiontype': 3, 'month': '2009-10', 'season': 10, 'team': 3, 'activity': 1, 'value': '489'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {'SAVE': 'YES', 'adherent': 5, 'dateref': '2009-10-01',
                                                             'subscriptiontype': 4, 'begin_date': '2009-09-15', 'season': 10, 'team': 3, 'activity': 2, 'value': '470'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 6, 'dateref': '2009-10-01', 'subscriptiontype': 1, 'season': 10, 'team': 1, 'activity': 2, 'value': '159'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

    def test_subscription_bydate(self):
        self.add_subscriptions()

        self.factory.xfer = AdherentActiveList()
        self.call(
            '/diacamma.member/adherentList', {'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentList')
        self.assert_count_equal('COMPONENTS/*', 2 + 11 + 3)
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
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 6) + 1 + 2 + (2 * 2 + 3) + 2)
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
        self.assert_count_equal('COMPONENTS/*', 2 + 3 + 3)

        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/HEADER', 5)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="adherent"]/ACTIONS/ACTION', 3)

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentShow')
        self.assert_count_equal(
            'COMPONENTS/*', 1 + 1 + 2 * (8 + 4 + 2) + 1 + 2 + (2 * 2 + 3) + 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscription"]/HEADER', 4)

        self.factory.xfer = AdherentAddModify()
        self.call('/diacamma.member/adherentAddModify',
                  {'adherent': 2, 'dateref': '2009-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentAddModify')
        self.assert_count_equal('COMPONENTS/*', 1 + 2 * (8 + 3 + 0) + 2)

        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'adherent': 2, 'dateref': '2014-10-01'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal(
            'COMPONENTS/*', 7)

        self.factory.xfer = SubscriptionShow()
        self.call('/diacamma.member/subscriptionShow',
                  {'adherent': 2, 'dateref': '2014-10-01', 'subscription': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 9)

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

        self.assert_count_equal(
            'COMPONENTS/GRID[@name="town_1"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="town_1"]/RECORD[2]/VALUE[@name="ratio"]', '{[b]}2{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="town_2"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="town_2"]/RECORD[2]/VALUE[@name="ratio"]', '{[b]}1{[/b]}')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="town_3"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="town_3"]/RECORD[2]/VALUE[@name="ratio"]', '{[b]}1{[/b]}')

        self.assert_count_equal('COMPONENTS/*', 3 * 5 + 3)

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
