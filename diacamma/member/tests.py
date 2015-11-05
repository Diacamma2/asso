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

from diacamma.member.views_season import SeasonAddModify, SeasonShow, MemberConf


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
        self.assert_count_equal('COMPONENTS/*', 10)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/HEADER', 3)
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
        self.assert_count_equal('COMPONENTS/*', 9)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="designation"]', "2014/2015")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="begin_date"]', "1 septembre 2014")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="end_date"]', "31 août 2015")
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

        self.factory.xfer = MemberConf()
        self.call('/diacamma.member/memberConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'memberConf')
        self.assert_count_equal('COMPONENTS/*', 10)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="season"]/RECORD', 1)

        self.factory.xfer = SeasonAddModify()
        self.call('/diacamma.member/seasonAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'seasonAddModify')
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_xml_equal(
            'COMPONENTS/DATE[@name="begin_date"]', '2015-09-01')
