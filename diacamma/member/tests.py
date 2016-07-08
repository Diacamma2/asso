# -*- coding: utf-8 -*-
'''
diacamma.member package

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

from lucterios.framework.test import LucteriosTest
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_user_dir

from diacamma.member.views_season import SeasonAddModify, SeasonShow, SeasonSubscription,\
    SeasonActive, DocummentAddModify, DocummentDel, SeasonDocummentClone,\
    PeriodDel, PeriodAddModify, SubscriptionTypeAddModify, SubscriptionTypeShow,\
    SubscriptionTypeDel
from diacamma.member.test_tools import default_season, default_financial
from diacamma.member.views_conf import CategoryConf, ActivityAddModify,\
    ActivityDel, TeamAddModify, TeamDel, AgeAddModify, AgeDel
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params


class SeasonTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)

    def test_add(self):
        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 0)

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonAddModify')
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_xml_equal(
            'COMPONENTS/DATE[@name="begin_date"]', None)

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify',
                  {'SAVE': 'YES', "begin_date": '2014-09-01'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'seasonAddModify')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('COMPONENTS/*', 11)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="designation"]', "2014/2015")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="begin_date"]', "1 septembre 2014")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="end_date"]', "31 août 2015")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/HEADER', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/HEADER', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 0)

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="designation"]', "2014/2015")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="iscurrent"]', "1")

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonAddModify')
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_xml_equal(
            'COMPONENTS/DATE[@name="begin_date"]', '2015-09-01')

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify',
                  {'SAVE': 'YES', "begin_date": '2015-09-01'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'seasonAddModify')

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="designation"]', "2015/2016")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="iscurrent"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[2]/VALUE[@name="designation"]', "2014/2015")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[2]/VALUE[@name="iscurrent"]', "1")

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify',
                  {'SAVE': 'YES', "begin_date": '2015-11-01'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'seasonAddModify')

    def test_list(self):
        default_season()

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal('COMPONENTS/*', 10)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/HEADER[@name="designation"]', "désignation")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/HEADER[@name="period_set"]', "période")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/HEADER[@name="iscurrent"]', "courant")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 5)

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {'show_filter': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 20)

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {'show_filter': 0}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="designation"]', "2011/2012")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[2]/VALUE[@name="designation"]', "2010/2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[3]/VALUE[@name="designation"]', "2009/2010")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[4]/VALUE[@name="designation"]', "2008/2009")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[5]/VALUE[@name="designation"]', "2007/2008")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="iscurrent"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[2]/VALUE[@name="iscurrent"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[3]/VALUE[@name="iscurrent"]', "1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[4]/VALUE[@name="iscurrent"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[5]/VALUE[@name="iscurrent"]', "0")

        self.factory.xfer = SeasonActive()
        self.call('/diacamma.member/seasonActive', {'season': 12}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'seasonActive')

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {'show_filter': 0}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[1]/VALUE[@name="designation"]', "2013/2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[2]/VALUE[@name="designation"]', "2012/2013")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[3]/VALUE[@name="designation"]', "2011/2012")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[4]/VALUE[@name="designation"]', "2010/2011")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD[5]/VALUE[@name="designation"]', "2009/2010")

    def test_doc(self):
        default_season()

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('COMPONENTS/*', 11)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="designation"]', "2009/2010")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/HEADER', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 0)

        self.factory.xfer = DocummentAddModify()
        self.call(
            '/diacamma.member/docummentAddModify', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'docummentAddModify')
        self.assert_count_equal('COMPONENTS/*', 3)

        self.factory.xfer = DocummentAddModify()
        self.call('/diacamma.member/docummentAddModify',
                  {'SAVE': 'YES', 'season': 10, 'name': 'abc123'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'docummentAddModify')
        self.factory.xfer = DocummentAddModify()
        self.call('/diacamma.member/docummentAddModify',
                  {'SAVE': 'YES', 'season': 10, 'name': 'xyz987'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'docummentAddModify')
        self.factory.xfer = DocummentAddModify()
        self.call('/diacamma.member/docummentAddModify',
                  {'SAVE': 'YES', 'season': 10, 'name': 'opq357'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'docummentAddModify')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[1]/VALUE[@name="name"]', "abc123")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[2]/VALUE[@name="name"]', "xyz987")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[3]/VALUE[@name="name"]', "opq357")

        self.factory.xfer = DocummentAddModify()
        self.call(
            '/diacamma.member/docummentAddModify', {'season': 10, 'document': 2}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'docummentAddModify')
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_xml_equal('COMPONENTS/EDIT[@name="name"]', "xyz987")

        self.factory.xfer = DocummentAddModify()
        self.call(
            '/diacamma.member/docummentAddModify', {'SAVE': 'YES', 'season': 10, 'document': 2, 'name': '987xyz'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'docummentAddModify')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[1]/VALUE[@name="name"]', "abc123")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[2]/VALUE[@name="name"]', "987xyz")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[3]/VALUE[@name="name"]', "opq357")

        self.factory.xfer = DocummentDel()
        self.call('/diacamma.member/docummentDel',
                  {'CONFIRME': 'YES', 'season': 10, 'document': 2}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'docummentDel')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[1]/VALUE[@name="name"]', "abc123")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[2]/VALUE[@name="name"]', "opq357")

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 11}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 0)

        self.factory.xfer = SeasonDocummentClone()
        self.call('/diacamma.member/seasonDocummentClone',
                  {'season': 11}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'seasonDocummentClone')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 11}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[1]/VALUE[@name="name"]', "abc123")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD[2]/VALUE[@name="name"]', "opq357")

    def test_period(self):
        default_season()

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('COMPONENTS/*', 11)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="designation"]', "2009/2010")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/HEADER[@name="num"]', "N°")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/HEADER[@name="begin_date"]', "date de début")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/HEADER[@name="end_date"]', "date de fin")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="document"]/RECORD', 0)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="num"]', '1')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="38"]/VALUE[@name="num"]', '2')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="39"]/VALUE[@name="num"]', '3')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="num"]', '4')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="begin_date"]', '1 septembre 2009')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="38"]/VALUE[@name="begin_date"]', '1 décembre 2009')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="39"]/VALUE[@name="begin_date"]', '1 mars 2010')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="begin_date"]', '1 juin 2010')

        self.factory.xfer = PeriodDel()
        self.call('/diacamma.member/periodDel',
                  {'CONFIRME': 'YES', 'period': 38}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'periodDel')
        self.factory.xfer = PeriodDel()
        self.call('/diacamma.member/periodDel',
                  {'CONFIRME': 'YES', 'period': 39}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'periodDel')
        self.factory.xfer = PeriodDel()
        self.call('/diacamma.member/periodDel',
                  {'CONFIRME': 'YES', 'period': 40}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'periodDel')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="num"]', '1')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="num"]', '2')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="begin_date"]', '1 septembre 2009')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="begin_date"]', '1 juin 2010')

        self.factory.xfer = PeriodAddModify()
        self.call(
            '/diacamma.member/periodAddModify', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'periodAddModify')
        self.assert_count_equal('COMPONENTS/*', 7)

        self.factory.xfer = PeriodAddModify()
        self.call(
            '/diacamma.member/periodAddModify', {'SAVE': 'YES', 'season': 10, 'begin_date': '2010-05-30', 'end_date': '2009-12-01'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'periodAddModify')

        self.factory.xfer = PeriodAddModify()
        self.call(
            '/diacamma.member/periodAddModify', {'SAVE': 'YES', 'season': 10, 'begin_date': '2009-12-01', 'end_date': '2010-05-30'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'periodAddModify')

        self.factory.xfer = SeasonShow()
        self.call('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="num"]', '1')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[2]/VALUE[@name="num"]', '2')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="num"]', '3')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="37"]/VALUE[@name="begin_date"]', '1 septembre 2009')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[2]/VALUE[@name="begin_date"]', '1 décembre 2009')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="period"]/RECORD[@id="40"]/VALUE[@name="begin_date"]', '1 juin 2010')

    def test_subscription(self):
        default_financial()
        default_season()

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal('COMPONENTS/*', 10)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER[@name="description"]', "description")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER[@name="duration"]', "durée")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER[@name="unactive"]', "désactivé")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/HEADER[@name="price"]', "prix")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD', 0)

        self.factory.xfer = SubscriptionTypeAddModify()
        self.call('/diacamma.member/subscriptionAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionAddModify')
        self.assert_count_equal('COMPONENTS/*', 19)

        self.factory.xfer = SubscriptionTypeAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'name': 'abc123', 'description': 'blablabla', 'duration': 1, 'articles': '1;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD[1]/VALUE[@name="name"]', "abc123")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD[1]/VALUE[@name="description"]', "blablabla")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD[1]/VALUE[@name="duration"]', "périodique")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD[1]/VALUE[@name="unactive"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD[1]/VALUE[@name="price"]', "76.44€")

        self.factory.xfer = SubscriptionTypeShow()
        self.call(
            '/diacamma.member/subscriptionShow', {"subscriptiontype": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'subscriptionShow')
        self.assert_count_equal('COMPONENTS/*', 13)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="articles"]/HEADER', 6)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="articles"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="articles"]/RECORD[1]/VALUE[@name="reference"]', "ABC1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="articles"]/RECORD[2]/VALUE[@name="reference"]', "ABC5")

        self.factory.xfer = SubscriptionTypeDel()
        self.call(
            '/diacamma.member/subscriptionDel', {"subscriptiontype": 1, 'CONFIRME': 'YES'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionDel')

        self.factory.xfer = SeasonSubscription()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subscriptiontype"]/RECORD', 0)


class CategoriesTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)

    def test_activity(self):
        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 37)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="activity"]/HEADER', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="activity"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="activity"]/HEADER[@name="description"]', "description")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="activity"]/RECORD', 1)

        self.factory.xfer = ActivityAddModify()
        self.call('/diacamma.member/activityAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'activityAddModify')
        self.assert_count_equal('COMPONENTS/*', 5)

        self.factory.xfer = ActivityAddModify()
        self.call('/diacamma.member/activityAddModify',
                  {"SAVE": "YES", "name": "xyz", "description": "abc"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'activityAddModify')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="activity"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="activity"]/RECORD[2]/VALUE[@name="name"]', "xyz")

        self.factory.xfer = ActivityDel()
        self.call('/diacamma.member/activityAddModify',
                  {"CONFIRME": "YES", "activity": 2}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'activityAddModify')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="activity"]/RECORD', 1)

        self.factory.xfer = ActivityDel()
        self.call('/diacamma.member/activityDel',
                  {"CONFIRME": "YES", "activity": 1}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'activityDel')

        Parameter.change_value("member-activite-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 34)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-activite-enable"]', 'Non')
        self.assert_count_equal('COMPONENTS/TAB', 3)
        self.assert_xml_equal('COMPONENTS/TAB[1]', 'Paramètres')
        self.assert_xml_equal('COMPONENTS/TAB[2]', 'Age')
        self.assert_xml_equal('COMPONENTS/TAB[3]', 'Équipe')

    def test_team(self):
        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 37)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="team"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="team"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="team"]/HEADER[@name="description"]', "description")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="team"]/HEADER[@name="unactive"]', "désactivé")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="team"]/RECORD', 0)

        self.factory.xfer = TeamAddModify()
        self.call('/diacamma.member/teamAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'teamAddModify')
        self.assert_count_equal('COMPONENTS/*', 7)

        self.factory.xfer = TeamAddModify()
        self.call('/diacamma.member/teamAddModify',
                  {"SAVE": "YES", "name": "xyz", "description": "abc"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'teamAddModify')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="team"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="team"]/RECORD[1]/VALUE[@name="name"]', "xyz")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="team"]/RECORD[1]/VALUE[@name="unactive"]', "0")

        self.factory.xfer = TeamDel()
        self.call('/diacamma.member/teamDel',
                  {"CONFIRME": "YES", "team": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'teamDel')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="team"]/RECORD', 0)

        Parameter.change_value("member-team-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 34)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-team-enable"]', 'Non')
        self.assert_count_equal('COMPONENTS/TAB', 3)
        self.assert_xml_equal('COMPONENTS/TAB[1]', 'Paramètres')
        self.assert_xml_equal('COMPONENTS/TAB[2]', 'Age')
        self.assert_xml_equal('COMPONENTS/TAB[3]', 'Activité')

    def test_age(self):
        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 37)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="age"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/HEADER[@name="date_min"]', "date min.")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/HEADER[@name="date_max"]', "date max.")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD', 0)

        self.factory.xfer = AgeAddModify()
        self.call('/diacamma.member/ageAddModify', {}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'ageAddModify')

        default_season()

        self.factory.xfer = AgeAddModify()
        self.call('/diacamma.member/ageAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'ageAddModify')
        self.assert_count_equal('COMPONENTS/*', 7)

        self.factory.xfer = AgeAddModify()
        self.call('/diacamma.member/ageAddModify',
                  {"SAVE": "YES", "name": "xyz", "date_min": "1981", "date_max": "1980"}, False)
        self.assert_observer(
            'core.exception', 'diacamma.member', 'ageAddModify')

        self.factory.xfer = AgeAddModify()
        self.call('/diacamma.member/ageAddModify',
                  {"SAVE": "YES", "name": "xyz", "date_min": "1980", "date_max": "1981"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'ageAddModify')
        self.factory.xfer = AgeAddModify()
        self.call('/diacamma.member/ageAddModify',
                  {"SAVE": "YES", "name": "uvw", "date_min": "1979", "date_max": "1980"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'ageAddModify')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="name"]', "uvw")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="date_min"]', "1979")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="date_max"]', "1980")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="name"]', "xyz")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="date_min"]', "1980")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="date_max"]', "1981")

        self.factory.xfer = SeasonActive()
        self.call('/diacamma.member/seasonActive', {'season': 12}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'seasonActive')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="name"]', "uvw")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="date_min"]', "1981")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[1]/VALUE[@name="date_max"]', "1982")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="name"]', "xyz")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="date_min"]', "1982")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD[2]/VALUE[@name="date_max"]', "1983")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-age-enable"]', 'Oui')

        self.factory.xfer = AgeDel()
        self.call('/diacamma.member/ageDel',
                  {"CONFIRME": "YES", "age": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'ageDel')

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="age"]/RECORD', 1)

        Parameter.change_value("member-age-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 34)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-age-enable"]', 'Non')
        self.assert_count_equal('COMPONENTS/TAB', 3)
        self.assert_xml_equal('COMPONENTS/TAB[1]', 'Paramètres')
        self.assert_xml_equal('COMPONENTS/TAB[2]', 'Équipe')
        self.assert_xml_equal('COMPONENTS/TAB[3]', 'Activité')

    def test_params(self):
        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 37)
        self.assert_count_equal('COMPONENTS/TAB', 4)
        self.assert_xml_equal('COMPONENTS/TAB[1]', 'Paramètres')
        self.assert_xml_equal('COMPONENTS/TAB[2]', 'Age')
        self.assert_xml_equal('COMPONENTS/TAB[3]', 'Équipe')
        self.assert_xml_equal('COMPONENTS/TAB[4]', 'Activité')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-team-text"]', 'Équipe')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-activite-text"]', 'Activité')

        Parameter.change_value("member-team-text", 'Cours')
        Parameter.change_value("member-activite-text", 'Sport')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.call('/diacamma.member/categoryConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('COMPONENTS/*', 37)
        self.assert_count_equal('COMPONENTS/TAB', 4)
        self.assert_xml_equal('COMPONENTS/TAB[1]', 'Paramètres')
        self.assert_xml_equal('COMPONENTS/TAB[2]', 'Age')
        self.assert_xml_equal('COMPONENTS/TAB[3]', 'Cours')
        self.assert_xml_equal('COMPONENTS/TAB[4]', 'Sport')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-team-text"]', 'Cours')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="member-activite-text"]', 'Sport')
