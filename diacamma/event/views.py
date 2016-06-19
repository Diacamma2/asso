# -*- coding: utf-8 -*-
'''
diacamma.event view module

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
from django.utils import six

from lucterios.framework.xferadvance import XferListEditor
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.framework.xfergraphic import XferContainerAcknowledge,\
    XferContainerCustom
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage,\
    SELECT_MULTI, CLOSE_NO, FORMTYPE_MODAL, WrapAction, CLOSE_YES,\
    FORMTYPE_REFRESH
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompImage,\
    XferCompSelect, XferCompMemo
from lucterios.CORE.xferprint import XferPrintAction
from lucterios.CORE.parameters import Params
from lucterios.contacts.tools import ContactSelection
from lucterios.contacts.models import Individual

from diacamma.member.views import AdherentSelection

from diacamma.event.models import Event, Organizer, Participant, Degree
from diacamma.member.models import Season
from lucterios.framework.models import get_value_if_choices

MenuManage.add_sub("event.actions", "association", "diacamma.event/images/event.png",
                   _("Events"), _("Management of events."), 80)


@ActionsManage.affect('Event', 'list')
@MenuManage.describ('event.change_event', FORMTYPE_NOMODAL, 'event.actions', _('Event manage'))
class EventList(XferListEditor):
    icon = "event.png"
    model = Event
    field_id = 'event'
    caption = _("Event")


@ActionsManage.affect('Event', 'search')
@MenuManage.describ('event.change_event', FORMTYPE_NOMODAL, 'event.actions', _('To find an event'))
class EventSearch(XferSearchEditor):
    icon = "event.png"
    model = Event
    field_id = 'event'
    caption = _("Search event")


@ActionsManage.affect('Event', 'edit', 'modify', 'add')
@MenuManage.describ('event.add_event')
class EventAddModify(XferAddEditor):
    icon = "event.png"
    model = Event
    field_id = 'event'
    caption_add = _("Add event")
    caption_modify = _("Modify event")


@ActionsManage.affect('Event', 'show')
@MenuManage.describ('event.change_event')
class EventShow(XferShowEditor):
    icon = "event.png"
    model = Event
    field_id = 'event'
    caption = _("Show examination")

    def fillresponse(self):
        if self.item.status == 0:
            if self.item.event_type == 0:
                params = {}
            else:
                params = {'SAVE': ''}
            self.action_list.insert(
                0, ('valid', _("Validation"), "images/ok.png", CLOSE_NO, params))
        else:
            del self.action_list[0]
        XferShowEditor.fillresponse(self)


@ActionsManage.affect('Event', 'valid')
@MenuManage.describ('event.add_event')
class EventValid(XferContainerAcknowledge):
    icon = "degree.png"
    model = Event
    field_id = 'event'
    caption = _("Validation of an examination")

    def fillresponse(self):
        self.item.can_be_valid()
        if self.getparam('SAVE') is None:
            dlg = self.create_custom()
            dlg.item = self.item
            img = XferCompImage('img')
            img.set_value(self.icon_path())
            img.set_location(0, 0, 1, 3)
            dlg.add_component(img)
            lbl = XferCompLabelForm('title')
            lbl.set_value_as_title(self.caption)
            lbl.set_location(1, 0, 6)
            dlg.add_component(lbl)
            dlg.fill_from_model(1, 1, True, ['activity', 'date'])
            lbl = XferCompLabelForm('sep')
            lbl.set_value("{[hr/]}")
            lbl.set_location(0, 4, 7)
            dlg.add_component(lbl)
            row_id = 5
            for participant in self.item.participant_set.all():
                lbl = XferCompLabelForm('name_%d' % participant.id)
                lbl.set_value_as_name(six.text_type(participant))
                lbl.set_location(0, row_id)
                dlg.add_component(lbl)

                lbl = XferCompLabelForm('current_%d' % participant.id)
                lbl.set_value(participant.current_degree)
                lbl.set_location(1, row_id)
                dlg.add_component(lbl)

                sel = XferCompSelect('degree_%d' % participant.id)
                sel.set_select_query(participant.allow_degree())
                sel.set_location(2, row_id)
                dlg.add_component(sel)

                if Params.getvalue("event-subdegree-enable") == 1:
                    sel = XferCompSelect('subdegree_%d' % participant.id)
                    sel.set_select_query(participant.allow_subdegree())
                    sel.set_location(3, row_id)
                    dlg.add_component(sel)

                edt = XferCompMemo('comment_%d' % participant.id)
                edt.set_value(participant.comment)
                edt.set_location(4, row_id)
                dlg.add_component(edt)

                row_id += 1
            dlg.add_action(self.get_action(
                _('Ok'), "images/ok.png"), {'close': CLOSE_YES, 'params': {'SAVE': 'YES'}})
            dlg.add_action(WrapAction(_('Cancel'), 'images/cancel.png'), {})
        elif (self.getparam('SAVE') != '') or self.confirme(_("Do you want to validate this %s?") % get_value_if_choices(
                self.item.event_type, self.item._meta.get_field('event_type'))):
            self.item.validate(self)


@ActionsManage.affect('Event', 'delete')
@MenuManage.describ('event.delete_event')
class EventDel(XferDelete):
    icon = "degree.png"
    model = Event
    field_id = 'event'
    caption = _("Delete examination")


@ActionsManage.affect('Event', 'print')
@MenuManage.describ('event.change_event')
class EventPrint(XferPrintAction):
    icon = "degree.png"
    model = Event
    field_id = 'event'
    caption = _("Print event")
    action_class = EventShow


@MenuManage.describ('event.add_event')
class OrganizerSave(XferContainerAcknowledge):
    icon = "degree.png"
    model = Organizer
    field_id = 'organizer'
    caption_add = _("Add organizer")

    def fillresponse(self, event, pkname=''):
        contact_ids = self.getparam(pkname)
        for contact_id in contact_ids.split(';'):
            Organizer.objects.get_or_create(
                event_id=event, contact_id=contact_id)


@ActionsManage.affect('Organizer', 'add')
@MenuManage.describ('event.add_event')
class OrganizerAddModify(ContactSelection):
    icon = "degree.png"
    caption = _("Add organizer")
    mode_select = SELECT_MULTI
    select_class = OrganizerSave
    inital_model = Individual


@ActionsManage.affect('Organizer', 'delete')
@MenuManage.describ('event.add_event')
class OrganizerDel(XferDelete):
    icon = "degree.png"
    model = Organizer
    field_id = 'organizer'
    caption = _("Delete organizer")


@ActionsManage.affect('Organizer', 'responsible')
@MenuManage.describ('event.add_event')
class OrganizerResponsible(XferContainerAcknowledge):
    icon = "degree.png"
    model = Organizer
    field_id = 'organizer'
    caption = _("Responsible")

    def fillresponse(self):
        self.item.set_has_responsible()


@MenuManage.describ('event.add_event')
class ParticipantSave(XferContainerAcknowledge):
    icon = "degree.png"
    model = Participant
    field_id = 'participant'
    caption_add = _("Add participant")

    def fillresponse(self, event, adherent=[], pkname=''):
        contact_ids = self.getparam(pkname, '').split(';')
        contact_ids.extend(adherent)
        for contact_id in contact_ids:
            if contact_id != '':
                Participant.objects.get_or_create(
                    event_id=event, contact_id=contact_id)


@ActionsManage.affect('Participant', 'show')
@MenuManage.describ('event.change_event')
class ParticipantOpen(XferContainerAcknowledge):
    icon = "degree.png"
    model = Participant
    field_id = 'participant'
    caption_add = _("Add participant")

    def fillresponse(self):
        current_contact = self.item.contact.get_final_child()
        modal_name = current_contact.__class__.__name__
        field_id = modal_name.lower()
        self.redirect_action(ActionsManage.get_act_changed(modal_name, 'show', '', ''), {
                             'modal': FORMTYPE_MODAL, 'close': CLOSE_NO, 'params': {field_id: six.text_type(current_contact.id)}})


@ActionsManage.affect('Participant', 'add')
@MenuManage.describ('event.add_event')
class ParticipantAdd(AdherentSelection):
    icon = "degree.png"
    caption = _("Add participant")
    mode_select = SELECT_MULTI
    select_class = ParticipantSave


@ActionsManage.affect('Participant', 'addct')
@MenuManage.describ('event.add_event')
class ParticipantAddContact(ContactSelection):
    icon = "degree.png"
    caption = _("Add participant")
    mode_select = SELECT_MULTI
    select_class = ParticipantSave
    inital_model = Individual


@ActionsManage.affect('Participant', 'edit')
@MenuManage.describ('event.add_event')
class ParticipantModify(XferAddEditor):
    icon = "degree.png"
    model = Participant
    field_id = 'participant'
    caption_add = _("Add participant")
    caption_modify = _("Modify participant")
    redirect_to_show = None


@ActionsManage.affect('Participant', 'delete')
@MenuManage.describ('event.add_event')
class ParticipantDel(XferDelete):
    icon = "degree.png"
    model = Participant
    field_id = 'participant'
    caption = _("Delete participant")


@MenuManage.describ('event.change_event', FORMTYPE_MODAL, 'event.actions', _('Statistic of degrees'))
class DegreeStatistic(XferContainerCustom):
    icon = "degree.png"
    model = Degree
    field_id = 'degree'
    caption = _("Statistic")

    def fillresponse(self, season):
        if season is None:
            working_season = Season.current_season()
        else:
            working_season = Season.objects.get(id=season)
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0)
        self.add_component(img)
        lab = XferCompLabelForm('lbl_season')
        lab.set_value_as_name(_('season'))
        lab.set_location(1, 0)
        self.add_component(lab)
        sel = XferCompSelect('season')
        sel.set_needed(True)
        sel.set_select_query(Season.objects.all())
        sel.set_value(working_season.id)
        sel.set_location(2, 0)
        sel.set_action(
            self.request, self.get_action('', ''), {'modal': FORMTYPE_REFRESH, 'close': CLOSE_NO})
        self.add_component(sel)
        stat_result = Degree.get_statistic(working_season)
        if len(stat_result) == 0:
            lab = XferCompLabelForm('lbl_season')
            lab.set_color('red')
            lab.set_value_as_infocenter(_('no degree!'))
            lab.set_location(1, 1, 2)
            self.add_component(lab)
        else:
            total = 0
            pos_y = 2
            for activity, sublist in stat_result:
                subtotal = 0
                if activity is not None:
                    lab = XferCompLabelForm("lblactivite_%d" % activity.id)
                    lab.set_italic()
                    lab.set_value(six.text_type(activity))
                    lab.set_location(0, pos_y, 3)
                    self.add_component(lab)
                    pos_y += 1
                for degree_name, val in sublist:
                    lab = XferCompLabelForm("title_%d" % pos_y)
                    lab.set_value(degree_name)
                    lab.set_location(1, pos_y)
                    self.add_component(lab)
                    lab = XferCompLabelForm("val_%d" % pos_y)
                    lab.set_value(six.text_type(val))
                    lab.set_location(2, pos_y)
                    self.add_component(lab)
                    subtotal += val
                    total += subtotal
                    pos_y += 1
                if (len(sublist) > 1) and (activity is not None):
                    lab = XferCompLabelForm("lblsubtotal_%d" % activity.id)
                    lab.set_value_as_header(_("Total"))
                    lab.set_location(1, pos_y)
                    self.add_component(lab)
                    lab = XferCompLabelForm("subtotal_%d" % activity.id)
                    lab.set_italic()
                    lab.set_value(six.text_type(subtotal))
                    lab.set_location(2, pos_y)
                    self.add_component(lab)
                    pos_y += 1
            lab = XferCompLabelForm("lbltotal")
            lab.set_value_as_headername(_("Total"))
            lab.set_location(1, pos_y)
            self.add_component(lab)
            lab = XferCompLabelForm("total")
            lab.set_value_as_name(six.text_type(subtotal))
            lab.set_location(2, pos_y)
            self.add_component(lab)
        self.add_action(DegreeStatisticPrint.get_action(
            _("Print"), "images/print.png"), {'close': CLOSE_NO, 'params': {'classname': self.__class__.__name__}})
        self.add_action(WrapAction(_('Close'), 'images/close.png'), {})


@MenuManage.describ('event.change_event')
class DegreeStatisticPrint(XferPrintAction):
    icon = "degree.png"
    model = Degree
    field_id = 'degree'
    caption = _("Statistic")
    action_class = DegreeStatistic
    with_text_export = True
