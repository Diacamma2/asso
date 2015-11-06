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

from diacamma.member.views_season import SeasonAddModify, SeasonShow, MemberConf,\
    SeasonActive, DocummentAddModify, DocummentDel, SeasonDocummentClone,\
    PeriodDel, PeriodAddModify
from diacamma.member.test_tools import default_season


class SeasonTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)

    def test_add(self):
        self.factory.xfer = MemberConf()
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

        self.factory.xfer = MemberConf()
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

        self.factory.xfer = MemberConf()
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

        self.factory.xfer = MemberConf()
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
            'COMPONENTS/GRID[@name="season"]/HEADER[@name="iscurrent"]', "courrant")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 5)

        self.factory.xfer = MemberConf()
        self.call('/diacamma.member/memberConf', {'show_filter': 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 20)

        self.factory.xfer = MemberConf()
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

        self.factory.xfer = MemberConf()
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
