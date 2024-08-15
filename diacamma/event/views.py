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

from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor, TITLE_PRINT, \
    TITLE_CLOSE, TITLE_DELETE, TITLE_MODIFY, TITLE_ADD, TITLE_EDIT, TITLE_OK, TITLE_CANCEL, \
    XferTransition, TITLE_CREATE
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.framework.xfergraphic import XferContainerAcknowledge, XferContainerCustom
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage, \
    SELECT_MULTI, CLOSE_NO, FORMTYPE_MODAL, WrapAction, CLOSE_YES, FORMTYPE_REFRESH, SELECT_SINGLE
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompImage, XferCompSelect, XferCompMemo
from lucterios.CORE.xferprint import XferPrintAction
from lucterios.CORE.parameters import Params
from lucterios.contacts.tools import ContactSelection
from lucterios.contacts.models import Individual

from diacamma.member.views import AdherentSelection
from diacamma.member.models import Season
from diacamma.event.models import Event, Organizer, Participant, Degree

MenuManage.add_sub("event.actions", "association", short_icon='mdi:mdi-calendar', caption=_("Events"), desc=_("Management of events."), pos=80)


class GenericEventList(XferListEditor):
    model = Event
    field_id = 'event'
    short_icon = "mdi:mdi-calendar-range"
    event_type = None

    def fillresponse_header(self):
        self.filter = Q(event_type=self.event_type)
        self.params['event_type'] = self.event_type

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        grid = self.get_components(self.field_id)
        grid.delete_header('event_type')


def rigth_examination(request):
    if EventListOuting.get_action().check_permission(request):
        return (Params.getvalue("event-degree-enable") == 1)
    else:
        return False


@MenuManage.describ(rigth_examination, FORMTYPE_NOMODAL, 'event.actions', _('Event manage'))
class EventListExamination(GenericEventList):
    short_icon = "mdi:mdi-trophy-outline"
    caption = _("Examination")
    event_type = Event.EVENTTYPE_EXAMINATION


@MenuManage.describ('event.change_event', FORMTYPE_NOMODAL, 'event.actions', _('Event manage'))
class EventListOuting(GenericEventList):
    short_icon = "mdi:mdi-calendar-multiselect"
    caption = _("Training or outing")
    event_type = Event.EVENTTYPE_TRAINING


@MenuManage.describ('event.change_event', FORMTYPE_NOMODAL, 'event.actions', _('To find an event'))
class EventSearch(XferSearchEditor):
    short_icon = "mdi:mdi-calendar-range"
    model = Event
    field_id = 'event'
    caption = _("Search event")


@ActionsManage.affect_grid(TITLE_CREATE, short_icon='mdi:mdi-pencil-plus')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@ActionsManage.affect_show(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', close=CLOSE_YES, condition=lambda xfer: xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class EventAddModify(XferAddEditor):
    short_icon = "mdi:mdi-calendar-range"
    model = Event
    field_id = 'event'
    caption_add = _("Add event")
    caption_modify = _("Modify event")


@ActionsManage.affect_grid(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline', unique=SELECT_SINGLE)
@MenuManage.describ('event.change_event')
class EventShow(XferShowEditor):
    short_icon = "mdi:mdi-calendar-range"
    model = Event
    field_id = 'event'
    caption = _("Show examination")


@ActionsManage.affect_transition("status")
@MenuManage.describ('event.add_event')
class EventTransition(XferTransition):
    short_icon = "mdi:mdi-trophy-outline"
    model = Event
    field_id = 'event'

    def fill_dlg(self):
        self.item.can_be_valid()
        dlg = self.create_custom()
        dlg.item = self.item
        img = XferCompImage('img')
        img.set_value(self.short_icon, '#')
        img.set_location(0, 0, 1, 3)
        dlg.add_component(img)
        lbl = XferCompLabelForm('title')
        lbl.set_value_as_title(self.caption)
        lbl.set_location(1, 0, 6)
        dlg.add_component(lbl)
        dlg.fill_from_model(1, 1, True, ['activity', 'date'])
        dlg.get_components('activity').colspan = 3
        dlg.get_components('date').colspan = 3
        lbl = XferCompLabelForm('sep')
        lbl.set_value("{[hr/]}")
        lbl.set_location(0, 4, 7)
        dlg.add_component(lbl)
        row_id = 5
        for participant in self.item.participant_set.all():
            lbl = XferCompLabelForm('name_%d' % participant.id)
            lbl.set_value_as_name(str(participant))
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
        dlg.add_action(self.return_action(TITLE_OK, short_icon='mdi:mdi-check'), close=CLOSE_YES, params={'CONFIRME': 'YES'})
        dlg.add_action(WrapAction(TITLE_CANCEL, short_icon='mdi:mdi-cancel'))

    def fill_confirm(self, transition, trans):
        if (transition == 'validate') and (self.item.event_type == Event.EVENTTYPE_EXAMINATION) and (self.getparam('CONFIRME') is None):
            self.fill_dlg()
        else:
            XferTransition.fill_confirm(self, transition, trans)


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('event.delete_event')
class EventDel(XferDelete):
    short_icon = "mdi:mdi-trophy-outline"
    model = Event
    field_id = 'event'
    caption = _("Delete examination")


@ActionsManage.affect_show(TITLE_PRINT, short_icon='mdi:mdi-printer-outline')
@MenuManage.describ('event.change_event')
class EventPrint(XferPrintAction):
    short_icon = "mdi:mdi-trophy-outline"
    model = Event
    field_id = 'event'
    caption = _("Print event")
    action_class = EventShow


@MenuManage.describ('event.add_event')
class OrganizerSave(XferContainerAcknowledge):
    short_icon = "mdi:mdi-trophy-outline"
    model = Organizer
    field_id = 'organizer'
    caption_add = _("Add organizer")

    def fillresponse(self, event, pkname=''):
        contact_ids = self.getparam(pkname)
        for contact_id in contact_ids.split(';'):
            Organizer.objects.get_or_create(
                event_id=event, contact_id=contact_id)


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline', condition=lambda xfer, gridname='': xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class OrganizerAddModify(ContactSelection):
    short_icon = "mdi:mdi-trophy-outline"
    caption = _("Add organizer")
    mode_select = SELECT_MULTI
    select_class = OrganizerSave
    model = Organizer
    inital_model = Individual
    readonly = False
    methods_allowed = ('POST', 'PUT')


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI, condition=lambda xfer, gridname='': xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class OrganizerDel(XferDelete):
    short_icon = "mdi:mdi-trophy-outline"
    model = Organizer
    field_id = 'organizer'
    caption = _("Delete organizer")


@ActionsManage.affect_grid(_("Responsible"), short_icon='mdi:mdi-check', unique=SELECT_SINGLE, intop=True, condition=lambda xfer, gridname='': xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class OrganizerResponsible(XferContainerAcknowledge):
    short_icon = "mdi:mdi-trophy-outline"
    model = Organizer
    field_id = 'organizer'
    caption = _("Responsible")

    def fillresponse(self):
        self.item.set_has_responsible()


@MenuManage.describ('event.add_event')
class ParticipantSave(XferContainerAcknowledge):
    short_icon = "mdi:mdi-trophy-outline"
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


@ActionsManage.affect_grid(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline', unique=SELECT_SINGLE)
@MenuManage.describ('event.change_event')
class ParticipantOpen(XferContainerAcknowledge):
    short_icon = "mdi:mdi-trophy-outline"
    model = Participant
    field_id = 'participant'
    caption_add = _("Add participant")
    readonly = True
    methods_allowed = ('GET', )

    def fillresponse(self):
        current_contact = self.item.contact.get_final_child()
        modal_name = current_contact.__class__.get_long_name()
        field_id = current_contact.__class__.__name__.lower()
        self.redirect_action(ActionsManage.get_action_url(modal_name, 'Show', self), modal=FORMTYPE_MODAL,
                             close=CLOSE_NO, params={field_id: str(current_contact.id)})


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline', condition=lambda xfer, gridname='': hasattr(xfer.item, 'status') and (xfer.item.status == Event.STATUS_BUILDING))
@MenuManage.describ('event.add_event')
class ParticipantAdd(AdherentSelection):
    short_icon = "mdi:mdi-trophy-outline"
    caption = _("Add participant")
    mode_select = SELECT_MULTI
    model = Participant
    select_class = ParticipantSave
    readonly = False
    methods_allowed = ('POST', 'PUT')


@ActionsManage.affect_grid(_("Add contact"), short_icon='mdi:mdi-pencil-plus-outline', condition=lambda xfer, gridname='': xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class ParticipantAddContact(ContactSelection):
    short_icon = "mdi:mdi-trophy-outline"
    caption = _("Add participant")
    mode_select = SELECT_MULTI
    select_class = ParticipantSave
    model = Participant
    inital_model = Individual
    readonly = False
    methods_allowed = ('POST', 'PUT')


@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE, condition=lambda xfer, gridname='': (xfer.item.status == Event.STATUS_BUILDING))
@MenuManage.describ('event.add_event')
class ParticipantModify(XferAddEditor):
    short_icon = "mdi:mdi-trophy-outline"
    model = Participant
    field_id = 'participant'
    caption_add = _("Add participant")
    caption_modify = _("Modify participant")
    redirect_to_show = None


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI, condition=lambda xfer, gridname='': xfer.item.status == Event.STATUS_BUILDING)
@MenuManage.describ('event.add_event')
class ParticipantDel(XferDelete):
    short_icon = "mdi:mdi-trophy-outline"
    model = Participant
    field_id = 'participant'
    caption = _("Delete participant")


@MenuManage.describ(rigth_examination, FORMTYPE_MODAL, 'event.actions', _('Statistic of degrees'))
class DegreeStatistic(XferContainerCustom):
    short_icon = "mdi:mdi-trophy-outline"
    model = Degree
    field_id = 'degree'
    caption = _("Statistic")
    readonly = True
    methods_allowed = ('GET', )

    def _show_statistic(self, action_name, working_season):
        total = 0
        pos_y = 2
        stat_result = getattr(Degree, action_name)(working_season)
        for activity, sublist in stat_result:
            subtotal = 0
            if activity is not None:
                lab = XferCompLabelForm("lblactivite_%s__%d" % (action_name, activity.id))
                lab.set_italic()
                lab.set_value(str(activity))
                lab.set_location(0, pos_y, 3)
                self.add_component(lab)
                pos_y += 1
            for degree_name, subdegree_name, val in sublist:
                lab = XferCompLabelForm("title_%s_%d" % (action_name, pos_y))
                lab.set_value(degree_name)
                lab.set_location(1, pos_y)
                self.add_component(lab)
                lab = XferCompLabelForm("subtitle_%s_%d" % (action_name, pos_y))
                lab.set_value(subdegree_name)
                lab.set_location(2, pos_y)
                self.add_component(lab)
                lab = XferCompLabelForm("val_%s_%d" % (action_name, pos_y))
                lab.set_value(str(val))
                lab.set_location(3, pos_y)
                self.add_component(lab)
                subtotal += val
                total += val
                pos_y += 1
            if activity is not None:
                lab = XferCompLabelForm("lblsubtotal_%s_%d" % (action_name, activity.id))
                lab.set_value_as_header(_("Total"))
                lab.set_location(1, pos_y, 2)
                self.add_component(lab)
                lab = XferCompLabelForm("subtotal_%s_%d" % (action_name, activity.id))
                lab.set_italic()
                lab.set_value(str(subtotal))
                lab.set_location(2, pos_y)
                self.add_component(lab)
                pos_y += 1
        lab = XferCompLabelForm("lbltotal_%s" % action_name)
        lab.set_value_as_headername(_("Total"))
        lab.set_location(1, pos_y, 2)
        self.add_component(lab)
        lab = XferCompLabelForm("total_%s" % action_name)
        lab.set_value_as_name(str(total))
        lab.set_location(2, pos_y)
        self.add_component(lab)

    def fillresponse(self, season):
        if season is None:
            working_season = Season.current_season()
        else:
            working_season = Season.objects.get(id=season)
        img = XferCompImage('img')
        img.set_value(self.short_icon, '#')
        img.set_location(0, 0)
        self.add_component(img)
        sel = XferCompSelect('season')
        sel.set_needed(True)
        sel.set_select_query(Season.objects.all())
        sel.set_value(working_season.id)
        sel.set_location(1, 0, 2)
        sel.description = _('season')
        sel.set_action(self.request, self.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(sel)
        self.new_tab(_('allocated in this season'))
        self._show_statistic('get_statistic', working_season)
        show_member_fields = Params.getvalue("member-fields").split(";")
        if 'higher_degree' in show_member_fields:
            self.new_tab(_('higher allocated'))
            self._show_statistic('get_higher_statistic', working_season)
        if 'lastdate_degree' in show_member_fields:
            self.new_tab(_('laster allocated'))
            self._show_statistic('get_laster_statistic', working_season)
        self.add_action(DegreeStatisticPrint.get_action(TITLE_PRINT, short_icon='mdi:mdi-printer-outline'),
                        close=CLOSE_NO, params={'classname': self.__class__.__name__})
        self.add_action(WrapAction(TITLE_CLOSE, short_icon='mdi:mdi-close'))


@MenuManage.describ(rigth_examination)
class DegreeStatisticPrint(XferPrintAction):
    short_icon = "mdi:mdi-trophy-outline"
    model = Degree
    field_id = 'degree'
    caption = _("Statistic")
    action_class = DegreeStatistic
    with_text_export = True
