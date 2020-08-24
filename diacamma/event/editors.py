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
from datetime import date

from django.utils.translation import ugettext_lazy as _

from lucterios.framework.editors import LucteriosEditor
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import FORMTYPE_REFRESH, CLOSE_NO

from diacamma.member.models import Activity
from diacamma.event.models import Event


class DegreeEditor(LucteriosEditor):

    def edit(self, xfer):
        xfer.change_to_readonly('adherent')


class ParticipantEditor(LucteriosEditor):

    def edit(self, xfer):
        xfer.change_to_readonly('contact')
        xfer.get_components('article').set_action(xfer.request, xfer.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        if xfer.item.article_id is None:
            xfer.remove_component('reduce')
        if xfer.item.event.event_type == Event.EVENTTYPE_EXAMINATION:
            xfer.remove_component('comment')


class EventEditor(LucteriosEditor):

    def before_save(self, xfer):
        if self.item.activity_id is None:
            activities = Activity.objects.all()
            if len(activities) == 0:
                raise LucteriosException(IMPORTANT, _('No activity!'))
            self.item.activity = activities[0]

    def edit(self, xfer):
        xfer.change_to_readonly('status')
        xfer.change_to_readonly('event_type')
        date_end = xfer.get_components('date_end')
        date_end.set_needed(True)
        if date_end.value is None:
            date_end.value = date.today()
        xfer.get_components('default_article').set_action(xfer.request, xfer.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        xfer.get_components('default_article_nomember').set_action(xfer.request, xfer.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)

    def show(self, xfer):
        participant = xfer.get_components('participant')
        participant.change_type_header('is_subscripter', 'B')
        if self.item.status == 0:
            participant.delete_header('degree_result_simple')
            participant.delete_header('subdegree_result')
            if self.item.event_type == Event.EVENTTYPE_EXAMINATION:
                participant.delete_header('comment')
        else:
            participant.delete_header('current_degree')
        img = xfer.get_components('img')
        if self.item.event_type == Event.EVENTTYPE_TRAINING:
            participant.delete_header('degree_result_simple')
            participant.delete_header('subdegree_result')
            participant.delete_header('current_degree')
            xfer.caption = _("Show trainning/outing")
            img.set_value("/static/diacamma.event/images/outing.png")
        else:
            xfer.caption = _("Show examination")
            xfer.remove_component('date_end')
            img.set_value("/static/diacamma.event/images/degree.png")
