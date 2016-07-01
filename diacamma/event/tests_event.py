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

from diacamma.member.test_tools import default_season, default_params,\
    default_adherents, set_parameters, default_financial, default_subscription
from diacamma.member.views import AdherentShow, SubscriptionAddModify
from diacamma.event.test_tools import default_event_params, add_default_degree
from diacamma.event.views import EventList, EventAddModify, EventDel, EventShow,\
    OrganizerAddModify, OrganizerSave, OrganizerResponsible, OrganizerDel,\
    ParticipantAdd, ParticipantSave, ParticipantDel, ParticipantOpen,\
    EventTransition, ParticipantModify
from diacamma.invoice.views import BillList


class EventTest(LucteriosTest):

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()
        default_adherents()
        default_subscription()
        default_event_params()
        set_parameters(
            ["team", "activite", "age", "licence", "genre", 'numero', 'birth'])
        add_default_degree()

    def test_add_remove(self):
        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="activity"]', "passion")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="event_type"]', "type d'évenement")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="status"]', "status")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="date_txt"]', "date")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="comment"]', "commentaire")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 0)

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventAddModify')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_activity"]', "{[b]}passion{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="activity"]/CASE', 2)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="status"]', "en création")

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="lbl_activity"]', "{[b]}passion{[/b]}")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="activity"]', 'activity1')

        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="status"]', "en création")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="event_type"]', "examen")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="date_txt"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="comment"]', "new examination")

        self.factory.xfer = EventDel()
        self.call('/diacamma.event/eventDel',
                  {"CONFIRME": "YES", "event": 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventDel')

        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 0)

    def test_add_organizer(self):
        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/HEADER', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/HEADER[@name="contact"]', "contact")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/HEADER[@name="isresponsible"]', "responsable")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 0)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/ACTIONS/ACTION', 3)

        self.factory.xfer = OrganizerAddModify()
        self.call('/diacamma.event/organizerAddModify', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'organizerAddModify')

        self.factory.xfer = OrganizerSave()
        self.call('/diacamma.event/organizerSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '3;6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="contact"]', "Dalton William")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="isresponsible"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="contact"]', "Luke Lucky")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="isresponsible"]', "0")

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '2'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="contact"]', "Dalton William")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="isresponsible"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="contact"]', "Luke Lucky")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="isresponsible"]', "1")

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '1'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="contact"]', "Dalton William")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="isresponsible"]', "1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="contact"]', "Luke Lucky")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[2]/VALUE[@name="isresponsible"]', "0")

        self.factory.xfer = OrganizerDel()
        self.call('/diacamma.event/organizerDel',
                  {"event": 1, 'organizer': '1', 'CONFIRME': 'YES'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerDel')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="contact"]', "Luke Lucky")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD[1]/VALUE[@name="isresponsible"]', "0")

    def test_add_participant(self):
        self.factory.xfer = SubscriptionAddModify()
        self.call('/diacamma.member/subscriptionAddModify',
                  {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 15, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER', 4)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="contact"]', "contact")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="is_subscripter"]', "adhérent?")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="current_degree"]', "courrant")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="article.ref_price"]', "article")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 0)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/ACTIONS/ACTION', 4)

        self.factory.xfer = ParticipantAdd()
        self.call('/diacamma.event/participantAdd', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'participantAdd')

        self.factory.xfer = ParticipantSave()
        self.call('/diacamma.event/participantSave',
                  {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="is_subscripter"]', "1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="current_degree"]', "level #1.2 sublevel #3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="article.ref_price"]', "---")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="current_degree"]', None)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="article.ref_price"]', "---")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="contact"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="current_degree"]', None)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="article.ref_price"]', "---")

        self.factory.xfer = ParticipantDel()
        self.call('/diacamma.event/participantDel',
                  {"event": 1, 'participant': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantDel')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Joe")

        self.factory.xfer = ParticipantOpen()
        self.call('/diacamma.event/participantOpen',
                  {"event": 1, 'participant': '3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantOpen')
        self.assert_attrib_equal("ACTION", "id", "diacamma.member/adherentShow")
        self.assert_count_equal("ACTION/PARAM", 1)
        self.assert_xml_equal("ACTION/PARAM[@name='adherent']", "5")

    def test_validation(self):
        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'eventShow')

        self.factory.xfer = OrganizerSave()
        self.call('/diacamma.event/organizerSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'eventShow')

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '1'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'eventShow')

        self.factory.xfer = ParticipantSave()
        self.call('/diacamma.event/participantSave',
                  {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 7 + 5 * 3)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_1"]', "{[b]}Dalton Avrel{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_1"]/CASE', 9)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="subdegree_1"]/CASE', 6)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_1"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_2"]', "{[b]}Dalton Jack{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_2"]/CASE', 10)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="subdegree_2"]/CASE', 6)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_2"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_3"]', "{[b]}Dalton Joe{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_3"]/CASE', 10)
        self.assert_count_equal(
            'COMPONENTS/SELECT[@name="subdegree_3"]/CASE', 6)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_3"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow',
                  {"event": 1, 'CONFIRME': 'YES', 'comment_1': 'trop nul!', 'degree_2': 5, 'comment_2': 'ça va...',
                   'degree_3': 3, 'subdegree_3': 4, 'comment_3': 'bien :)', 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventShow')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/ACTIONS/ACTION', 0)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/ACTIONS/ACTION', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER', 6)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="contact"]', "contact")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="degree_result_simple"]', "Grade résultant")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="subdegree_result"]', "Barette résultant")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="comment"]', "commentaire")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="article.ref_price"]', "article")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="degree_result_simple"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="subdegree_result"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="comment"]', 'trop nul!')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="article.ref_price"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="degree_result_simple"]', "level #1.5")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="subdegree_result"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="comment"]', 'ça va...')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="article.ref_price"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="contact"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="degree_result_simple"]', "level #1.3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="subdegree_result"]', "sublevel #4")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="comment"]', 'bien :)')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="article.ref_price"]', '---')

        self.factory.xfer = OrganizerDel()
        self.call('/diacamma.event/organizerDel',
                  {"event": 1, 'organizer': '1', 'CONFIRME': 'YES'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'organizerDel')

        self.factory.xfer = ParticipantDel()
        self.call('/diacamma.event/participantDel',
                  {"event": 1, 'participant': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'participantDel')

        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="event_type"]', "examen")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="status"]', "validé")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="date_txt"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="comment"]', "new examination")

        self.factory.xfer = EventDel()
        self.call('/diacamma.event/eventDel',
                  {"CONFIRME": "YES", "event": 1}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'eventDel')

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Avrel")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="degree"]', "[activity1] level #1.2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="subdegree"]', "sublevel #3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="date"]', "4 novembre 2011")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow', {'adherent': 4}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Jack")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="degree"]', "[activity1] level #1.5")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="subdegree"]', "---")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="date"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="degree"]', "[activity2] level #2.2")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="subdegree"]', "sublevel #1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="date"]', "9 avril 2012")

        self.factory.xfer = AdherentShow()
        self.call('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="firstname"]', "Joe")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD', 2)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="degree"]', "[activity1] level #1.3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="subdegree"]', "sublevel #4")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[1]/VALUE[@name="date"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="degree"]', "[activity2] level #2.6")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="subdegree"]', "---")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="degrees"]/RECORD[2]/VALUE[@name="date"]', "21 septembre 2010")

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.exception', 'diacamma.event', 'eventShow')

    def test_no_activity(self):
        set_parameters([])
        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER', 4)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="status"]', "status")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="event_type"]', "type d'évenement")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="date_txt"]', "date")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/HEADER[@name="comment"]', "commentaire")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 0)

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventAddModify')
        self.assert_count_equal('COMPONENTS/*', 13)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="status"]', "en création")

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 13)

    def test_no_subdegree(self):
        Parameter.change_value("event-subdegree-enable", 0)
        Params.clear()

        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.call('/diacamma.event/organizerSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '1'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.call('/diacamma.event/participantSave',
                  {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 7 + 4 * 3)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_1"]', "{[b]}Dalton Avrel{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_1"]/CASE', 9)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_1"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_2"]', "{[b]}Dalton Jack{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_2"]/CASE', 10)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_2"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="name_3"]', "{[b]}Dalton Joe{[/b]}")
        self.assert_count_equal('COMPONENTS/SELECT[@name="degree_3"]/CASE', 10)
        self.assert_xml_equal(
            'COMPONENTS/MEMO[@name="comment_3"]', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow',
                  {"event": 1, 'CONFIRME': 'YES', 'comment_1': 'trop nul!', 'degree_2': 5, 'comment_2': 'ça va...',
                   'degree_3': 3, 'comment_3': 'bien :)', 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventShow')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 15)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/ACTIONS/ACTION', 0)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/ACTIONS/ACTION', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER', 5)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="contact"]', "contact")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="degree_result_simple"]', "Grade résultant")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="comment"]', "commentaire")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER[@name="article.ref_price"]', "article")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="degree_result_simple"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="comment"]', 'trop nul!')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="article.ref_price"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="degree_result_simple"]', "level #1.5")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="comment"]', 'ça va...')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="article.ref_price"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="contact"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="is_subscripter"]', "0")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="degree_result_simple"]', "level #1.3")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="comment"]', 'bien :)')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="article.ref_price"]', '---')

    def test_outing(self):
        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "date_end": "2014-10-13", "activity": "1", "event_type": 1, "comment": "outing", 'default_article': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.call('/diacamma.event/organizerSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '1'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.call('/diacamma.event/participantSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '2;4;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 17)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/HEADER', 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/ACTIONS/ACTION', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/ACTIONS/ACTION', 5)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="date"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="date_end"]', "13 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="default_article.ref_price"]', "---")

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.dialogbox', 'diacamma.event', 'eventShow')

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow',
                  {"event": 1, 'CONFIRME': 'YES', 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventShow')

        self.factory.xfer = EventList()
        self.call('/diacamma.event/eventList', {}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventList')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD', 1)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="activity"]', "activity1")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="event_type"]', "stage/sortie")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="status"]', "validé")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="date_txt"]', "12 octobre 2014 -> 13 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="event"]/RECORD[1]/VALUE[@name="comment"]', "outing")

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 17)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/HEADER', 2)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/RECORD', 1)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="organizer"]/ACTIONS/ACTION', 0)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/HEADER', 4)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/ACTIONS/ACTION', 1)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="date"]', "12 octobre 2014")
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="date_end"]', "13 octobre 2014")

    def test_bill(self):
        self.factory.xfer = EventAddModify()
        self.call('/diacamma.event/eventAddModify',
                  {"SAVE": "YES", "date": "2014-10-12", "date_end": "2014-10-13", "activity": "1", "event_type": 1, "comment": "outing", 'default_article': 1}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.call('/diacamma.event/organizerSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.call('/diacamma.event/organizerResponsible',
                  {"event": 1, 'organizer': '1'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.call('/diacamma.event/participantSave',
                  {"event": 1, 'pkname': 'contact', 'contact': '2;4;5'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('COMPONENTS/*', 17)
        self.assert_xml_equal(
            'COMPONENTS/LABELFORM[@name="default_article.ref_price"]', "ABC1 [12.34€]")
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="article.ref_price"]', 'ABC1 [12.34€]')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="article.ref_price"]', 'ABC1 [12.34€]')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="contact"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="article.ref_price"]', 'ABC1 [12.34€]')

        self.factory.xfer = ParticipantModify()
        self.call('/diacamma.event/participantModify',
                  {"event": 1, "participant": 1, "SAVE": "YES", 'comment': 'blabla', 'article': 0}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantModify')
        self.factory.xfer = ParticipantModify()
        self.call('/diacamma.event/participantModify',
                  {"event": 1, "participant": 3, "SAVE": "YES", 'comment': 'bou!!!!', 'article': 5}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'participantModify')

        self.factory.xfer = EventShow()
        self.call('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer(
            'core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD', 3)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="contact"]', "Dalton Avrel")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="article.ref_price"]', '---')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[1]/VALUE[@name="comment"]', 'blabla')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="contact"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="article.ref_price"]', 'ABC1 [12.34€]')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[2]/VALUE[@name="comment"]', None)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="contact"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="article.ref_price"]', 'ABC5 [64.10€]')
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="participant"]/RECORD[3]/VALUE[@name="comment"]', 'bou!!!!')

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 0)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)

        self.factory.xfer = EventTransition()
        self.call('/diacamma.event/eventShow',
                  {"event": 1, 'CONFIRME': 'YES', 'TRANSITION': 'validate'}, False)
        self.assert_observer(
            'core.acknowledge', 'diacamma.event', 'eventShow')

        self.factory.xfer = BillList()
        self.call('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/RECORD', 2)
        self.assert_count_equal('COMPONENTS/GRID[@name="bill"]/HEADER', 7)
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="third"]', "Dalton Jack")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[1]/VALUE[@name="total"]', "12.34€")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[2]/VALUE[@name="third"]', "Dalton Joe")
        self.assert_xml_equal(
            'COMPONENTS/GRID[@name="bill"]/RECORD[2]/VALUE[@name="total"]', "64.10€")
