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

from django.utils.translation import ugettext_lazy as _

from lucterios.framework.editors import LucteriosEditor
from lucterios.framework.tools import SELECT_SINGLE

from diacamma.event.models import Participant, Organizer
from lucterios.framework.xfercomponents import DEFAULT_ACTION_LIST
from diacamma.member.models import Activity
from lucterios.framework.error import LucteriosException, IMPORTANT


class DegreeEditor(LucteriosEditor):

    def edit(self, xfer):
        xfer.change_to_readonly('adherent')


class EventEditor(LucteriosEditor):

    def before_save(self, xfer):
        if self.item.activity_id is None:
            activities = Activity.objects.all()
            if len(activities) == 0:
                raise LucteriosException(IMPORTANT, _('No activity!'))
            self.item.activity = activities[0]

    def edit(self, xfer):
        xfer.change_to_readonly('status')

    def show(self, xfer):
        organizer = xfer.get_components('organizer')
        participant = xfer.get_components('participant')
        organizer.actions = []
        if self.item.status == 0:
            organizer.add_actions(
                xfer, action_list=[('responsible', _("Responsible"), "images/ok.png", SELECT_SINGLE)], model=Organizer)
            organizer.add_actions(xfer, model=Organizer)
            participant.delete_header('degree_result_simple')
            participant.delete_header('subdegree_result')
            participant.delete_header('comment')
        else:
            participant.delete_header('current_degree')
            participant.actions = []
            participant.add_actions(
                xfer, action_list=DEFAULT_ACTION_LIST[:1], model=Participant)
