# -*- coding: utf-8 -*-
'''
diacamma.event package

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
from shutil import rmtree

from lucterios.framework.test import LucteriosTest
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.filetools import get_user_dir

from diacamma.member.test_tools import default_adherents, default_season
from diacamma.member.views import AdherentShow
from diacamma.member.models import Activity

from diacamma.event.views_conf import EventConf, DegreeTypeAddModify,\
    DegreeTypeDel, SubDegreeTypeAddModify, SubDegreeTypeDel
from diacamma.event.views_degree import DegreeAddModify, DegreeDel
from diacamma.event.models import DegreeType, SubDegreeType


def default_params():
    activity = Activity.objects.all()[0]
    for level in range(1, 10):
        DegreeType.objects.create(
            name="level #%d" % level, level=level, activity=activity)
    for level in range(1, 6):
        SubDegreeType.objects.create(name="sublevel #%d" % level, level=level)


class ConfigurationTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)

    def test_degreetype(self):
        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal('COMPONENTS/*', 6)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degreetype"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degreetype"]/HEADER[@name="activity"]', "activité")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degreetype"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degreetype"]/HEADER[@name="level"]', "niveau")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degreetype"]/RECORD', 0)

        self.factory.xfer = DegreeTypeAddModify()
        self.call('/diacamma.event/degreeTypeAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'degreeTypeAddModify')
        self.assert_count_equal('COMPONENTS/*', 7)

        self.factory.xfer = DegreeTypeAddModify()
        self.call('/diacamma.event/degreeTypeAddModify',
                  {"SAVE": "YES", "activity": 1, "name": "abc", "level": "5"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'degreeTypeAddModify')

        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degreetype"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degreetype"]/RECORD[1]/VALUE[@name="name"]', "abc")

        self.factory.xfer = DegreeTypeDel()
        self.call('/diacamma.event/degreeTypeDel',
                  {"CONFIRME": "YES", "degreetype": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'degreeTypeDel')

        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degreetype"]/RECORD', 0)

    def test_subdegreetype(self):
        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal('COMPONENTS/*', 6)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/HEADER', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/HEADER[@name="name"]', "nom")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/HEADER[@name="level"]', "niveau")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/RECORD', 0)

        self.factory.xfer = SubDegreeTypeAddModify()
        self.call('/diacamma.event/subdegreeTypeAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'subdegreeTypeAddModify')
        self.assert_count_equal('COMPONENTS/*', 5)

        self.factory.xfer = SubDegreeTypeAddModify()
        self.call('/diacamma.event/subdegreeTypeAddModify',
                  {"SAVE": "YES", "name": "uvw", "level": "10"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'subdegreeTypeAddModify')

        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/RECORD[1]/VALUE[@name="name"]', "uvw")

        self.factory.xfer = SubDegreeTypeDel()
        self.call('/diacamma.event/subdegreeTypeDel',
                  {"CONFIRME": "YES", "subdegreetype": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'subdegreeTypeDel')

        self.factory.xfer = EventConf()
        self.call('/diacamma.event/EventConf', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'EventConf')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="subdegreetype"]/RECORD', 0)


class DegreeTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_season()
        default_adherents()
        default_params()

    def test_degree(self):
        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer(
            'core.custom', 'diacamma.member', 'adherentShow')
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Avrel")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lastname"]', "Dalton")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/HEADER', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/HEADER[@name="degree"]', "diplôme")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/HEADER[@name="subdegree"]', "sous-diplôme")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/HEADER[@name="date"]', "date")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 0)

        self.factory.xfer = DegreeAddModify()
        self.call('/diacamma.event/degreeAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'degreeAddModify')
        self.assert_count_equal('COMPONENTS/*', 9)

        self.factory.xfer = DegreeAddModify()
        self.call('/diacamma.event/degreeAddModify',
                  {"SAVE": "YES", 'adherent': 2, "degree": "3", "subdegree": "2", "date": "2014-10-12"}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'degreeAddModify')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 2}, False)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="degree"]', "[défaut] level #3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="subdegree"]', "sublevel #2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="date"]', "12 octobre 2014")

        self.factory.xfer = DegreeDel()
        self.call('/diacamma.event/degreeDel',
                  {"CONFIRME": "YES", "degrees": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'degreeDel')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentAddModify', {'adherent': 2}, False)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 0)
