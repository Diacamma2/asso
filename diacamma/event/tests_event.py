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
from lucterios.framework.filetools import get_user_dir
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import LegalEntity

from diacamma.member.test_tools import default_season, default_params, default_adherents, set_parameters, default_financial, default_subscription
from diacamma.member.views import AdherentShow, SubscriptionAddModify, AdherentFamilySelect
from diacamma.invoice.views import BillList, BillShow

from diacamma.event.test_tools import default_event_params, add_default_degree
from diacamma.event.views import EventListExamination, EventListOuting, EventAddModify, EventDel, EventShow, OrganizerAddModify, OrganizerSave, OrganizerResponsible, OrganizerDel,\
    ParticipantAdd, ParticipantSave, ParticipantDel, ParticipantOpen, EventTransition, ParticipantModify


class EventTest(LucteriosTest):

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        default_financial()
        default_season()
        default_params()
        default_adherents()
        default_subscription()
        default_event_params()
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])
        add_default_degree()

    def test_add_remove(self):
        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_grid_equal('event', {'activity': "passion", 'status': "status", 'date_txt': "date", 'comment': "commentaire"}, 0)
        self.assertEqual(self.json_context['event_type'], 0)

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventAddModify')
        self.assert_count_equal('', 9)
        self.assert_attrib_equal('activity', "description", "passion")
        self.assert_select_equal('activity', 2)  # nb=2
        self.assert_json_equal('LABELFORM', 'status', 0)

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_attrib_equal('activity', "description", "passion")
        self.assert_json_equal('LABELFORM', 'activity', 'activity1')

        self.factory.xfer = EventListOuting()
        self.calljson('/diacamma.event/eventListOuting', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListOuting')
        self.assert_count_equal('event', 0)

        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_count_equal('event', 1)
        self.assert_json_equal('', 'event/@0/activity', "activity1")
        self.assert_json_equal('', 'event/@0/status', 0)
        self.assert_json_equal('', 'event/@0/date_txt', "12 octobre 2014")
        self.assert_json_equal('', 'event/@0/comment', "new examination")

        self.factory.xfer = EventDel()
        self.calljson('/diacamma.event/eventDel', {"CONFIRME": "YES", "event": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventDel')

        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_count_equal('event', 0)

    def test_add_organizer(self):
        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_grid_equal('organizer', {'contact': "contact", 'isresponsible': "responsable"}, 0)
        self.assert_count_equal('#organizer/actions', 3)

        self.factory.xfer = OrganizerAddModify()
        self.calljson('/diacamma.event/organizerAddModify', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'organizerAddModify')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '3;6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('organizer', 2)
        self.assert_json_equal('', 'organizer/@0/contact', "Dalton William")
        self.assert_json_equal('', 'organizer/@0/isresponsible', False)
        self.assert_json_equal('', 'organizer/@1/contact', "Luke Lucky")
        self.assert_json_equal('', 'organizer/@1/isresponsible', False)

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '2'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('organizer', 2)
        self.assert_json_equal('', 'organizer/@0/contact', "Dalton William")
        self.assert_json_equal('', 'organizer/@0/isresponsible', False)
        self.assert_json_equal('', 'organizer/@1/contact', "Luke Lucky")
        self.assert_json_equal('', 'organizer/@1/isresponsible', True)

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('organizer', 2)
        self.assert_json_equal('', 'organizer/@0/contact', "Dalton William")
        self.assert_json_equal('', 'organizer/@0/isresponsible', True)
        self.assert_json_equal('', 'organizer/@1/contact', "Luke Lucky")
        self.assert_json_equal('', 'organizer/@1/isresponsible', False)

        self.factory.xfer = OrganizerDel()
        self.calljson('/diacamma.event/organizerDel',
                      {"event": 1, 'organizer': '1', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerDel')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('organizer', 1)
        self.assert_json_equal('', 'organizer/@0/contact', "Luke Lucky")
        self.assert_json_equal('', 'organizer/@0/isresponsible', False)

    def test_add_participant(self):
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 15, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_grid_equal('participant', {'contact': "contact", 'is_subscripter': "adhérent ?", 'current_degree': "courrant", 'article_ref_price': "article"}, 0)
        self.assert_count_equal('#participant/actions', 5)

        self.factory.xfer = ParticipantAdd()
        self.calljson('/diacamma.event/participantAdd', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'participantAdd')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave',
                      {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('participant', 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/is_subscripter', True)
        self.assert_json_equal('', 'participant/@0/current_degree', "level #1.2 sublevel #3")
        self.assert_json_equal('', 'participant/@0/article_ref_price', None)
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/is_subscripter', False)
        self.assert_json_equal('', 'participant/@1/current_degree', '')
        self.assert_json_equal('', 'participant/@1/article_ref_price', None)
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/is_subscripter', False)
        self.assert_json_equal('', 'participant/@2/current_degree', '')
        self.assert_json_equal('', 'participant/@2/article_ref_price', None)

        self.factory.xfer = ParticipantDel()
        self.calljson('/diacamma.event/participantDel',
                      {"event": 1, 'participant': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantDel')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('participant', 2)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Joe")

        self.factory.xfer = ParticipantOpen()
        self.calljson('/diacamma.event/participantOpen',
                      {"event": 1, 'participant': '3'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantOpen')
        self.assertEqual(self.response_json['action']['id'], "diacamma.member/adherentShow")
        self.assertEqual(len(self.response_json['action']['params']), 1)
        self.assertEqual(self.response_json['action']['params']['adherent'], "5")

    def test_validation(self):
        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'eventTransition')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'eventTransition')

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'eventTransition')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave',
                      {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventTransition')
        self.assert_count_equal('', 5 + 5 * 3)
        self.assert_json_equal('LABELFORM', 'name_1', "Dalton Avrel")
        self.assert_select_equal('degree_1', 9)  # nb=9
        self.assert_select_equal('subdegree_1', 6)  # nb=6
        self.assert_json_equal('MEMO', 'comment_1', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_json_equal('LABELFORM', 'name_2', "Dalton Jack")
        self.assert_select_equal('degree_2', 10)  # nb=10
        self.assert_select_equal('subdegree_2', 6)  # nb=6
        self.assert_json_equal('MEMO', 'comment_2', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_json_equal('LABELFORM', 'name_3', "Dalton Joe")
        self.assert_select_equal('degree_3', 10)  # nb=10
        self.assert_select_equal('subdegree_3', 6)  # nb=6
        self.assert_json_equal('MEMO', 'comment_3', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition',
                      {"event": 1, 'CONFIRME': 'YES', 'comment_1': 'trop nul!', 'degree_2': 5, 'comment_2': 'ça va...',
                       'degree_3': 3, 'subdegree_3': 4, 'comment_3': 'bien :)', 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventTransition')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('#organizer/actions', 0)
        self.assert_count_equal('#participant/actions', 1)
        self.assert_grid_equal('participant', {'contact': "contact", "is_subscripter": "adhérent ?", 'degree_result_simple': "Grade résultant", 'subdegree_result': "Barette résultant", 'comment': "commentaire", 'article_ref_price': "article"}, 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/is_subscripter', False)
        self.assert_json_equal('', 'participant/@0/degree_result_simple', None)
        self.assert_json_equal('', 'participant/@0/subdegree_result', None)
        self.assert_json_equal('', 'participant/@0/comment', 'trop nul!')
        self.assert_json_equal('', 'participant/@0/article_ref_price', None)
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/is_subscripter', False)
        self.assert_json_equal('', 'participant/@1/degree_result_simple', "level #1.5")
        self.assert_json_equal('', 'participant/@1/subdegree_result', None)
        self.assert_json_equal('', 'participant/@1/comment', 'ça va...')
        self.assert_json_equal('', 'participant/@1/article_ref_price', None)
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/is_subscripter', False)
        self.assert_json_equal('', 'participant/@2/degree_result_simple', "level #1.3")
        self.assert_json_equal('', 'participant/@2/subdegree_result', "sublevel #4")
        self.assert_json_equal('', 'participant/@2/comment', 'bien :)')
        self.assert_json_equal('', 'participant/@2/article_ref_price', None)

        self.factory.xfer = OrganizerDel()
        self.calljson('/diacamma.event/organizerDel',
                      {"event": 1, 'organizer': '1', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'organizerDel')

        self.factory.xfer = ParticipantDel()
        self.calljson('/diacamma.event/participantDel',
                      {"event": 1, 'participant': '2', 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'participantDel')

        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_count_equal('event', 1)
        self.assert_json_equal('', 'event/@0/activity', "activity1")
        self.assert_json_equal('', 'event/@0/status', 1)
        self.assert_json_equal('', 'event/@0/date_txt', "12 octobre 2014")
        self.assert_json_equal('', 'event/@0/comment', "new examination")

        self.factory.xfer = EventDel()
        self.calljson('/diacamma.event/eventDel', {"CONFIRME": "YES", "event": 1}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'eventDel')

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 2}, False)
        self.assert_json_equal('LABELFORM', 'firstname', "Avrel")
        self.assert_count_equal('degrees', 1)
        self.assert_json_equal('', 'degrees/@0/degree', "[activity1] level #1.2")
        self.assert_json_equal('', 'degrees/@0/subdegree', "sublevel #3")
        self.assert_json_equal('', 'degrees/@0/date', "2011-11-04")

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 4}, False)
        self.assert_json_equal('LABELFORM', 'firstname', "Jack")
        self.assert_count_equal('degrees', 2)
        self.assert_json_equal('', 'degrees/@0/degree', "[activity1] level #1.5")
        self.assert_json_equal('', 'degrees/@0/subdegree', None)
        self.assert_json_equal('', 'degrees/@0/date', "2014-10-12")
        self.assert_json_equal('', 'degrees/@1/degree', "[activity2] level #2.2")
        self.assert_json_equal('', 'degrees/@1/subdegree', "sublevel #1")
        self.assert_json_equal('', 'degrees/@1/date', "2012-04-09")

        self.factory.xfer = AdherentShow()
        self.calljson('/diacamma.member/adherentShow', {'adherent': 5}, False)
        self.assert_json_equal('LABELFORM', 'firstname', "Joe")
        self.assert_count_equal('degrees', 2)
        self.assert_json_equal('', 'degrees/@0/degree', "[activity1] level #1.3")
        self.assert_json_equal('', 'degrees/@0/subdegree', "sublevel #4")
        self.assert_json_equal('', 'degrees/@0/date', "2014-10-12")
        self.assert_json_equal('', 'degrees/@1/degree', "[activity2] level #2.6")
        self.assert_json_equal('', 'degrees/@1/subdegree', None)
        self.assert_json_equal('', 'degrees/@1/date', "2010-09-21")

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.exception', 'diacamma.event', 'eventTransition')

    def test_no_activity(self):
        set_parameters([])
        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_grid_equal('event', {'status': "status", 'date_txt': "date", 'comment': "commentaire"}, 0)

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventAddModify')
        self.assert_count_equal('', 8)
        self.assert_json_equal('', '#status/formatnum', {'0': "en création", "1": "validé"})
        self.assert_json_equal('LABELFORM', 'status', 0)

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 8)

    def test_no_subdegree(self):
        Parameter.change_value("event-subdegree-enable", 0)
        Params.clear()

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "activity": "1", "event_type": 0, "comment": "new examination", 'default_article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave',
                      {"event": 1, 'adherent': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventTransition')
        self.assert_count_equal('', 5 + 4 * 3)
        self.assert_json_equal('LABELFORM', 'name_1', "Dalton Avrel")
        self.assert_select_equal('degree_1', 9)  # nb=9
        self.assert_json_equal('MEMO', 'comment_1', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_json_equal('LABELFORM', 'name_2', "Dalton Jack")
        self.assert_select_equal('degree_2', 10)  # nb=10
        self.assert_json_equal('MEMO', 'comment_2', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")
        self.assert_json_equal('LABELFORM', 'name_3', "Dalton Joe")
        self.assert_select_equal('degree_3', 10)  # nb=10
        self.assert_json_equal('MEMO', 'comment_3', "Epreuve 1:{[br/]}Epreuve 2:{[br/]}")

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition',
                      {"event": 1, 'CONFIRME': 'YES', 'comment_1': 'trop nul!', 'degree_2': 5, 'comment_2': 'ça va...',
                       'degree_3': 3, 'comment_3': 'bien :)', 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventTransition')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 9)
        self.assert_count_equal('#organizer/actions', 0)
        self.assert_count_equal('#participant/actions', 1)
        self.assert_grid_equal('participant', {'contact': "contact", "is_subscripter": "adhérent ?", 'degree_result_simple': "Grade résultant", 'comment': "commentaire", 'article_ref_price': "article"}, 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/is_subscripter', False)
        self.assert_json_equal('', 'participant/@0/degree_result_simple', None)
        self.assert_json_equal('', 'participant/@0/comment', 'trop nul!')
        self.assert_json_equal('', 'participant/@0/article_ref_price', None)
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/is_subscripter', False)
        self.assert_json_equal('', 'participant/@1/degree_result_simple', "level #1.5")
        self.assert_json_equal('', 'participant/@1/comment', 'ça va...')
        self.assert_json_equal('', 'participant/@1/article_ref_price', None)
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/is_subscripter', False)
        self.assert_json_equal('', 'participant/@2/degree_result_simple', "level #1.3")
        self.assert_json_equal('', 'participant/@2/comment', 'bien :)')
        self.assert_json_equal('', 'participant/@2/article_ref_price', None)

    def test_outing(self):
        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "date": "2014-10-12", "date_end": "2014-10-13", "activity": "1", "event_type": 1, "comment": "outing", 'default_article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 10)
        self.assert_count_equal('organizer', 1)
        self.assert_count_equal('#organizer/actions', 3)
        self.assert_count_equal('participant', 3)
        self.assert_count_equal('#participant/actions', 5)
        self.assert_json_equal('LABELFORM', 'date', "2014-10-12")
        self.assert_json_equal('LABELFORM', 'date_end', "2014-10-13")
        self.assert_json_equal('LABELFORM', "default_article.ref_price", None)
        self.assert_json_equal('LABELFORM', "default_article_nomember.ref_price", None)

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition', {"event": 1, 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.dialogbox', 'diacamma.event', 'eventTransition')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition',
                      {"event": 1, 'CONFIRME': 'YES', 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventTransition')

        self.factory.xfer = EventListExamination()
        self.calljson('/diacamma.event/eventListExamination', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListExamination')
        self.assert_count_equal('event', 0)

        self.factory.xfer = EventListOuting()
        self.calljson('/diacamma.event/eventListOuting', {}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventListOuting')
        self.assert_count_equal('event', 1)
        self.assert_json_equal('', 'event/@0/activity', "activity1")
        self.assert_json_equal('', 'event/@0/status', 1)
        self.assert_json_equal('', 'event/@0/date_txt', "12 octobre 2014 -> 13 octobre 2014")
        self.assert_json_equal('', 'event/@0/comment', "outing")
        self.assertEqual(self.json_context['event_type'], 1)

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 10)
        self.assert_count_equal('organizer', 1)
        self.assert_count_equal('#organizer/actions', 0)
        self.assert_count_equal('participant', 3)
        self.assert_count_equal('#participant/actions', 1)
        self.assert_json_equal('LABELFORM', 'date', "2014-10-12")
        self.assert_json_equal('LABELFORM', 'date_end', "2014-10-13")

    def test_bill(self):
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 15, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify',
                      {"SAVE": "YES", "comment": "la fiesta", "date": "2014-10-12", "date_end": "2014-10-13", "activity": "1", "event_type": 1, 'default_article': 1, 'default_article_nomember': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible',
                      {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('', 10)
        self.assert_json_equal('LABELFORM', "default_article.ref_price", "ABC1 [12,34 €]")
        self.assert_json_equal('LABELFORM', 'comment', "la fiesta")
        self.assert_count_equal('participant', 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/is_subscripter', True)
        self.assert_json_equal('', 'participant/@0/article_ref_price', 'ABC1 [12,34 €]')
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/is_subscripter', False)
        self.assert_json_equal('', 'participant/@1/article_ref_price', 'ABC2 [56,78 €]')
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/is_subscripter', False)
        self.assert_json_equal('', 'participant/@2/article_ref_price', 'ABC2 [56,78 €]')

        self.factory.xfer = ParticipantModify()
        self.calljson('/diacamma.event/participantModify',
                      {"event": 1, "participant": 2, "SAVE": "YES", 'comment': 'blabla', 'article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantModify')
        self.factory.xfer = ParticipantModify()
        self.calljson('/diacamma.event/participantModify',
                      {"event": 1, "participant": 3, "SAVE": "YES", 'comment': 'bou!!!!', 'article': 5, 'reduce': 10.0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantModify')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('participant', 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/article_ref_price', 'ABC1 [12,34 €]')
        self.assert_json_equal('', 'participant/@0/comment', '')
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/article_ref_price', None)
        self.assert_json_equal('', 'participant/@1/comment', 'blabla')
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/article_ref_price', 'ABC5 [64,10 €] (-10,00 €)')
        self.assert_json_equal('', 'participant/@2/comment', 'bou!!!!')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 1)

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition',
                      {"event": 1, 'CONFIRME': 'YES', 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 3)
        self.assert_json_equal('', 'bill/@0/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@0/total', 12.34)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}stage/sortie{[/b]}: 12 octobre 2014 -> 13 octobre 2014{[br/]}{[i]}la fiesta{[/i]}")
        self.assert_json_equal('', 'bill/@1/third', "Dalton Joe")
        self.assert_json_equal('', 'bill/@1/total', 54.10)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}stage/sortie{[/b]}: 12 octobre 2014 -> 13 octobre 2014{[br/]}{[i]}la fiesta{[/i]}{[br/]}bou!!!!")
        self.assert_json_equal('', 'bill/@2/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@2/total', 76.44)
        self.assert_json_equal('', 'bill/@2/comment', "{[b]}cotisation{[/b]}{[br/]}Cotisation de 'Dalton Avrel'")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 3}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_json_equal('LINK', 'third', "Dalton Joe")
        self.assert_count_equal('detail', 1)
        self.assert_json_equal('', 'detail/@0/article', 'ABC5')
        self.assert_json_equal('', 'detail/@0/designation', 'Article 05')
        self.assert_json_equal('', 'detail/@0/price', 64.10)
        self.assert_json_equal('', 'detail/@0/quantity', '1.00')
        self.assert_json_equal('', 'detail/@0/reduce_txt', '10,00 €(15.60%)')
        self.assert_json_equal('', 'detail/@0/total', 54.10)
        self.assert_json_equal('LABELFORM', 'total_excltax', 54.10)

    def _test_bill_with_family(self):
        self.factory.xfer = SubscriptionAddModify()
        self.calljson('/diacamma.member/subscriptionAddModify',
                      {'SAVE': 'YES', 'adherent': 2, 'dateref': '2014-10-01', 'subscriptiontype': 1, 'season': 15, 'team': 2, 'activity': 1, 'value': '132'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionAddModify')

        Parameter.change_value('member-family-type', 3)
        Params.clear()
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
        self.assertEqual(myfamily.id, 7)

        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 2, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 4, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')
        self.factory.xfer = AdherentFamilySelect()
        self.calljson('/diacamma.member/adherentFamilySelect', {'adherent': 5, 'legal_entity': 7}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'adherentFamilySelect')

        self.factory.xfer = EventAddModify()
        self.calljson('/diacamma.event/eventAddModify', {"SAVE": "YES", "comment": "la fiesta", "date": "2014-10-12", "date_end": "2014-10-13",
                                                         "activity": "1", "event_type": 1, 'default_article': 1, 'default_article_nomember': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventAddModify')

        self.factory.xfer = OrganizerSave()
        self.calljson('/diacamma.event/organizerSave',
                      {"event": 1, 'pkname': 'contact', 'contact': '6'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerSave')

        self.factory.xfer = OrganizerResponsible()
        self.calljson('/diacamma.event/organizerResponsible', {"event": 1, 'organizer': '1'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'organizerResponsible')

        self.factory.xfer = ParticipantSave()
        self.calljson('/diacamma.event/participantSave', {"event": 1, 'pkname': 'contact', 'contact': '2;4;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantSave')

        self.factory.xfer = ParticipantModify()
        self.calljson('/diacamma.event/participantModify', {"event": 1, "participant": 2, "SAVE": "YES", 'comment': 'blabla', 'article': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantModify')
        self.factory.xfer = ParticipantModify()
        self.calljson('/diacamma.event/participantModify', {"event": 1, "participant": 3, "SAVE": "YES", 'comment': 'bou!!!!', 'article': 5, 'reduce': 10.0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'participantModify')

        self.factory.xfer = EventShow()
        self.calljson('/diacamma.event/eventShow', {"event": 1}, False)
        self.assert_observer('core.custom', 'diacamma.event', 'eventShow')
        self.assert_count_equal('participant', 3)
        self.assert_json_equal('', 'participant/@0/contact', "Dalton Avrel")
        self.assert_json_equal('', 'participant/@0/article_ref_price', 'ABC1 [12,34 €]')
        self.assert_json_equal('', 'participant/@0/comment', '')
        self.assert_json_equal('', 'participant/@1/contact', "Dalton Jack")
        self.assert_json_equal('', 'participant/@1/article_ref_price', None)
        self.assert_json_equal('', 'participant/@1/comment', 'blabla')
        self.assert_json_equal('', 'participant/@2/contact', "Dalton Joe")
        self.assert_json_equal('', 'participant/@2/article_ref_price', 'ABC5 [64,10 €] (-10,00 €)')
        self.assert_json_equal('', 'participant/@2/comment', 'bou!!!!')

        self.factory.xfer = EventTransition()
        self.calljson('/diacamma.event/eventTransition',
                      {"event": 1, 'CONFIRME': 'YES', 'TRANSITION': 'validate'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.event', 'eventTransition')

        self.factory.xfer = BillList()
        self.calljson('/diacamma.invoice/billList', {}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billList')
        self.assert_count_equal('bill', 2)
        self.assert_json_equal('', 'bill/@0/bill_type', "facture")
        self.assert_json_equal('', 'bill/@0/status', 'en création')
        self.assert_json_equal('', 'bill/@0/third', "LES DALTONS")
        self.assert_json_equal('', 'bill/@0/total', 66.44)
        self.assert_json_equal('', 'bill/@0/comment', "{[b]}stage/sortie{[/b]}: 12 octobre 2014 -> 13 octobre 2014{[br/]}{[i]}la fiesta{[/i]}")
        self.assert_json_equal('', 'bill/@1/bill_type', "facture")
        self.assert_json_equal('', 'bill/@1/status', 'en création')
        self.assert_json_equal('', 'bill/@1/third', "Dalton Avrel")
        self.assert_json_equal('', 'bill/@1/total', 76.44)
        self.assert_json_equal('', 'bill/@1/comment', "{[b]}cotisation{[/b]}{[br/]}Cotisation de 'Dalton Avrel'")

        self.factory.xfer = BillShow()
        self.calljson('/diacamma.invoice/billShow', {'bill': 2}, False)
        self.assert_observer('core.custom', 'diacamma.invoice', 'billShow')
        self.assert_json_equal('LINK', 'third', "LES DALTONS")
        self.assert_count_equal('detail', 2)
        self.assert_json_equal('', 'detail/@0/article', 'ABC1')
        self.assert_json_equal('', 'detail/@0/designation', "Article 01{[br/]}Participant : Dalton Avrel")
        self.assert_json_equal('', 'detail/@0/price', 12.34)
        self.assert_json_equal('', 'detail/@0/quantity', '1.000')
        self.assert_json_equal('', 'detail/@0/total', 12.34)
        self.assert_json_equal('', 'detail/@1/article', 'ABC5')
        self.assert_json_equal('', 'detail/@1/designation', "Article 05{[br/]}Participant : Dalton Joe{[br/]}bou!!!!")
        self.assert_json_equal('', 'detail/@1/price', 64.10)
        self.assert_json_equal('', 'detail/@1/quantity', '1.00')
        self.assert_json_equal('', 'detail/@1/total', 54.10)
