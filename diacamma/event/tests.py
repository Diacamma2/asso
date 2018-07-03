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
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params

from diacamma.member.test_tools import default_adherents, default_season,\
    default_params, set_parameters
from diacamma.member.views import AdherentShow

from diacamma.event.views_conf import EventConf, DegreeTypeAddModify,\
    DegreeTypeDel, SubDegreeTypeAddModify, SubDegreeTypeDel
from diacamma.event.views_degree import DegreeAddModify, DegreeDel
from diacamma.event.test_tools import default_event_params


class ConfigurationTest(LucteriosTest):

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_season()
        default_params()
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])

    def test_degreetype(self):
        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 2 + 7)
        self.assert_grid_equal('degreetype', {'activity': "passion", 'name': "nom", 'level': "niveau"}, 0)

        self.factory.xfer = DegreeTypeAddModify()
        self.calljson('/diacamma.event/degreeTypeAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'degreeTypeAddModify')
        self.assert_count_equal('', 4)
        self.assert_attrib_equal('activity', "description", "passion")
        self.assert_select_equal('activity', 2)  # nb=2

        self.factory.xfer = DegreeTypeAddModify()
        self.calljson('/diacamma.event/degreeTypeAddModify',
                      {"SAVE": "YES", "activity": 1, "name": "abc", "level": "5"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeTypeAddModify')

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('degreetype', 1)
        self.assert_json_equal('', 'degreetype/@0/name', "abc")

        self.factory.xfer = DegreeTypeDel()
        self.calljson('/diacamma.event/degreeTypeDel',
                      {"CONFIRME": "YES", "degreetype": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeTypeDel')

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('degreetype', 0)

    def test_subdegreetype(self):
        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 2 + 7)
        self.assert_grid_equal('subdegreetype', {'name': "nom", 'level': "niveau"}, 0)

        self.factory.xfer = SubDegreeTypeAddModify()
        self.calljson('/diacamma.event/subDegreeTypeAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'subDegreeTypeAddModify')
        self.assert_count_equal('', 3)

        self.factory.xfer = SubDegreeTypeAddModify()
        self.calljson('/diacamma.event/subDegreeTypeAddModify',
                      {"SAVE": "YES", "name": "uvw", "level": "10"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'subDegreeTypeAddModify')

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('subdegreetype', 1)
        self.assert_json_equal('', 'subdegreetype/@0/name', "uvw")

        self.factory.xfer = SubDegreeTypeDel()
        self.calljson('/diacamma.event/subDegreeTypeDel',
                      {"CONFIRME": "YES", "subdegreetype": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'subDegreeTypeDel')

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('subdegreetype', 0)

    def test_no_activity(self):
        set_parameters([])
        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 2 + 7)
        self.assert_grid_equal('degreetype', {'name': "nom", 'level': "niveau"}, 0)

        self.factory.xfer = DegreeTypeAddModify()
        self.calljson('/diacamma.event/degreeTypeAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'degreeTypeAddModify')
        self.assert_count_equal('', 3)

    def test_params(self):
        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 2 + 7)
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Diplôme')
        self.assert_json_equal('TAB', '__tab_3', 'Sous-diplôme')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('LABELFORM', 'event-degree-text', 'Diplôme')
        self.assert_json_equal('LABELFORM', 'event-subdegree-text', 'Sous-diplôme')

        Parameter.change_value("event-degree-text", 'Grade')
        Parameter.change_value("event-subdegree-text", 'Barette')
        Params.clear()

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 2 + 7)
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Grade')
        self.assert_json_equal('TAB', '__tab_3', 'Barette')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('LABELFORM', 'event-degree-text', 'Grade')
        self.assert_json_equal('LABELFORM', 'event-subdegree-text', 'Barette')
        self.assert_json_equal('LABELFORM', 'event-subdegree-enable', 'Oui')
        self.assert_json_equal('LABELFORM', 'event-degree-enable', 'Oui')

        Parameter.change_value("event-subdegree-enable", 0)
        Params.clear()

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 2 + 7)
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Grade')
        self.assertFalse('__tab_3' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('LABELFORM', 'event-subdegree-enable', 'Non')
        self.assert_json_equal('LABELFORM', 'event-degree-enable', 'Oui')

        Parameter.change_value("event-degree-enable", 0)
        Params.clear()

        self.factory.xfer = EventConf()
        self.calljson('/diacamma.event/eventConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventConf')
        self.assert_count_equal('', 2 + 7)
        self.assertFalse('__tab_2' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('LABELFORM', 'event-subdegree-enable', 'Non')
        self.assert_json_equal('LABELFORM', 'event-degree-enable', 'Non')


class DegreeTest(LucteriosTest):

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_season()
        default_params()
        default_adherents()
        default_event_params()
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])

    def test_degree(self):
        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'adherentShow')
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_json_equal('LABELFORM', 'lastname', "Dalton")
        self.assert_grid_equal('degrees', {'degree': "Grade", 'subdegree': "Barette", 'date': "date"}, 0)

        self.factory.xfer = DegreeAddModify()
        self.calljson('/diacamma.event/degreeAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'degreeAddModify')
        self.assert_count_equal('', 5)

        self.factory.xfer = DegreeAddModify()
        self.calljson('/diacamma.event/degreeAddModify',
                      {"SAVE": "YES", 'adherent': 2, "degree": "3", "subdegree": "2", "date": "2014-10-12"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_count_equal('degrees', 1)
        self.assert_json_equal('', 'degrees/@0/degree', "[activity1] level #1.3")
        self.assert_json_equal('', 'degrees/@0/subdegree', "sublevel #2")
        self.assert_json_equal('', 'degrees/@0/date', "2014-10-12")

        self.factory.xfer = DegreeDel()
        self.calljson('/diacamma.event/degreeDel', {"CONFIRME": "YES", "degrees": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeDel')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_count_equal('degrees', 0)

    def test_no_activity(self):
        set_parameters([])
        self.factory.xfer = DegreeAddModify()
        self.calljson('/diacamma.event/degreeAddModify',
                      {"SAVE": "YES", 'adherent': 2, "degree": "3", "subdegree": "2", "date": "2014-10-12"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_grid_equal('degrees', {'degree': 'Grade', 'subdegree': 'Barette', 'date': 'date'}, 1)  # nb=3
        self.assert_json_equal('', 'degrees/@0/degree', "level #1.3")
        self.assert_json_equal('', 'degrees/@0/subdegree', "sublevel #2")
        self.assert_json_equal('', 'degrees/@0/date', "2014-10-12")

    def test_no_subdegree(self):
        Parameter.change_value("event-subdegree-enable", 0)
        Params.clear()

        self.factory.xfer = DegreeAddModify()
        self.calljson('/diacamma.event/degreeAddModify',
                      {"SAVE": "YES", 'adherent': 2, "degree": "3", "date": "2014-10-12"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'degreeAddModify')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_grid_equal('degrees', {'degree': 'Grade', 'date': 'date'}, 1)  # nb=2
        self.assert_json_equal('', 'degrees/@0/degree', "[activity1] level #1.3")
        self.assert_json_equal('', 'degrees/@0/date', "2014-10-12")
