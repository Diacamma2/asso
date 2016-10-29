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
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.utils import six
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor, TITLE_OK, TITLE_ADD,\
    TITLE_MODIFY, TITLE_EDIT, TITLE_CANCEL, TITLE_LABEL, TITLE_LISTING,\
    TITLE_DELETE, TITLE_CLOSE, TITLE_PRINT, XferTransition
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.CORE.xferprint import XferPrintAction
from lucterios.CORE.xferprint import XferPrintLabel
from lucterios.CORE.xferprint import XferPrintListing
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage, \
    FORMTYPE_REFRESH, CLOSE_NO, SELECT_SINGLE, WrapAction, FORMTYPE_MODAL, \
    SELECT_MULTI, CLOSE_YES
from lucterios.framework.xfercomponents import XferCompLabelForm, \
    XferCompCheckList, XferCompButton, XferCompSelect, XferCompDate, \
    XferCompImage, XferCompEdit, XferCompGrid, XferCompFloat, XferCompCheck
from lucterios.framework.xfergraphic import XferContainerAcknowledge, XferContainerCustom
from lucterios.framework.tools import convert_date, same_day_months_after
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework import signal_and_lock

from lucterios.CORE.parameters import Params

from diacamma.member.models import Adherent, Subscription, Season, Age, Team, Activity, License, DocAdherent, SubscriptionType, CommandManager
from lucterios.contacts.models import Individual


MenuManage.add_sub("association", None, "diacamma.member/images/association.png", _("Association"), _("Association tools"), 30)

MenuManage.add_sub("member.actions", "association", "diacamma.member/images/member.png",
                   _("Adherents"), _("Management of adherents and subscriptions."), 50)


class AdherentFilter(object):

    def get_filter(self):
        team = self.getparam("team", ())
        activity = self.getparam("activity", ())
        genre = self.getparam("genre", 0)
        age = self.getparam("age", ())
        status = self.getparam("status", -1)
        dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)
        if self.getparam('is_renew', False):
            date_one_year = same_day_months_after(dateref, -12)
            date_six_month = same_day_months_after(dateref, -6)
            date_three_month = same_day_months_after(dateref, -3)
            current_filter = Q(subscription__subscriptiontype__duration=0) & Q(
                subscription__end_date__gte=date_one_year)
            current_filter |= Q(subscription__subscriptiontype__duration=1) & Q(
                subscription__end_date__gte=date_six_month)
            current_filter |= Q(subscription__subscriptiontype__duration=2) & Q(
                subscription__end_date__gte=date_three_month)
            current_filter |= Q(subscription__subscriptiontype__duration=3) & Q(
                subscription__end_date__gte=date_one_year)
            exclude_filter = Q(subscription__begin_date__lte=dateref) & Q(
                subscription__end_date__gte=dateref)
        else:
            current_filter = Q(subscription__begin_date__lte=dateref) & Q(
                subscription__end_date__gte=dateref)
            exclude_filter = Q()
        if len(team) > 0:
            current_filter &= Q(subscription__license__team__in=team)
        if len(activity) > 0:
            current_filter &= Q(subscription__license__activity__in=activity)
        if len(age) > 0:
            age_filter = Q()
            for age_item in Age.objects.filter(id__in=age):
                age_filter |= Q(birthday__gte="%d-01-01" % (dateref.year - age_item.maximum)) & Q(
                    birthday__lte="%d-12-31" % (dateref.year - age_item.minimum))
            current_filter &= age_filter
        if genre != 0:
            current_filter &= Q(genre=genre)
        if status == -1:
            current_filter &= Q(subscription__status__in=(1, 2))
        else:
            current_filter &= Q(subscription__status=status)
        return (current_filter, exclude_filter)


class AdherentAbstractList(XferListEditor, AdherentFilter):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'

    def get_items_from_filter(self):
        current_filter, exclude_filter = self.get_filter()
        return self.model.objects.filter(current_filter).exclude(exclude_filter)

    def fillresponse_header(self):
        row = self.get_max_row() + 1
        team = self.getparam("team", ())
        activity = self.getparam("activity", ())
        genre = self.getparam("genre", 0)
        age = self.getparam("age", ())
        status = self.getparam("status", -1)
        dateref = convert_date(
            self.getparam("dateref", ""), Season.current_season().date_ref)

        if Params.getvalue("member-age-enable"):
            lbl = XferCompLabelForm('lblage')
            lbl.set_value_as_name(_("Age"))
            lbl.set_location(0, row)
            self.add_component(lbl)
            sel = XferCompCheckList('age')
            sel.set_select_query(Age.objects.all())
            sel.set_value(age)
            sel.set_location(1, row, 1, 2)
            self.add_component(sel)

        if Params.getvalue("member-team-enable"):
            lbl = XferCompLabelForm('lblteam')
            lbl.set_value_as_name(Params.getvalue("member-team-text"))
            lbl.set_location(2, row)
            self.add_component(lbl)
            sel = XferCompCheckList('team')
            sel.set_select_query(Team.objects.all())
            sel.set_value(team)
            sel.set_location(3, row, 1, 2)
            self.add_component(sel)

        if Params.getvalue("member-activite-enable"):
            lbl = XferCompLabelForm('lblactivity')
            lbl.set_value_as_name(Params.getvalue("member-activite-text"))
            lbl.set_location(4, row)
            self.add_component(lbl)
            sel = XferCompCheckList('activity')
            sel.set_select_query(Activity.objects.all())
            sel.set_value(activity)
            sel.set_location(5, row, 1, 2)
            self.add_component(sel)

        lbl = XferCompLabelForm('lbldateref')
        lbl.set_value_as_name(_("reference date"))
        lbl.set_location(6, row)
        self.add_component(lbl)

        dtref = XferCompDate('dateref')
        dtref.set_value(dateref)
        dtref.set_needed(True)
        dtref.set_location(7, row, 2)
        self.add_component(dtref)

        if Params.getvalue("member-filter-genre"):
            lbl = XferCompLabelForm('lblgenre')
            lbl.set_value_as_name(_("genre"))
            lbl.set_location(6, row + 1)
            self.add_component(lbl)
            sel = XferCompSelect('genre')
            list_genre = list(self.item.get_field_by_name('genre').choices)
            list_genre.insert(0, (0, '---'))
            sel.set_select(list_genre)
            sel.set_location(7, row + 1)
            sel.set_value(genre)
            self.add_component(sel)

        lbl = XferCompLabelForm('lblstatus')
        lbl.set_value_as_name(_("status"))
        lbl.set_location(6, row + 2)
        self.add_component(lbl)
        sel = XferCompSelect('status')
        list_status = list(Subscription.get_field_by_name('status').choices)
        del list_status[0]
        del list_status[-2]
        del list_status[-1]
        list_status.insert(0, (-1, '%s & %s' % (_('building'), _('valid'))))
        sel.set_select(list_status)
        sel.set_location(7, row + 2)
        sel.set_value(status)
        self.add_component(sel)

        btn = XferCompButton('btndateref')
        btn.set_location(8, row + 1, 1, 2)
        btn.set_action(self.request, self.get_action(_('Refresh'), ''),
                       modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(btn)


class AdherentSelection(AdherentAbstractList):
    caption = _("Select adherent")
    mode_select = SELECT_SINGLE
    select_class = None
    final_class = None

    def fillresponse(self):
        self.model = Adherent
        self.item = Adherent()
        self.action_list = []
        if self.final_class is not None:
            self.add_action(self.final_class.get_action(TITLE_OK, "images/ok.png"))
        AdherentAbstractList.fillresponse(self)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10
        if self.select_class is not None:
            grid = self.get_components(self.field_id)
            grid.add_action(self.request, self.select_class.get_action(_("Select"), "images/ok.png"),
                            close=CLOSE_YES, unique=self.mode_select, pos_act=0)


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with subscribtion'))
class AdherentActiveList(AdherentAbstractList):
    caption = _("Subscribe adherents")

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.item.editor.add_email_selector(
            self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10
        self.get_components(self.field_id).add_action(self.request, AdherentSubscription.get_action(_("Subscription"), ""),
                                                      unique=SELECT_SINGLE, close=CLOSE_NO)
        if Params.getvalue("member-licence-enabled"):
            self.get_components(self.field_id).add_action(self.request, AdherentLicense.get_action(_("License"), ""),
                                                          unique=SELECT_SINGLE, close=CLOSE_NO)
        if Params.getvalue("member-subscription-mode") == 1:
            self.add_action(SubscriptionModerate.get_action(_("Moderation"), "images/up.png"), pos_act=0, close=CLOSE_NO)


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('To find an adherent following a set of criteria.'))
class AdherentSearch(XferSearchEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Search adherent")


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with old subscribtion not renew yet'))
class AdherentRenewList(AdherentAbstractList):
    caption = _("Adherents to renew")

    def fillresponse_header(self):
        self.params['is_renew'] = True
        AdherentAbstractList.fillresponse_header(self)
        self.fieldnames = Adherent.get_renew_fields()

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.item.editor.add_email_selector(
            self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10
        if Params.getvalue("member-subscription-mode") == 1:
            self.add_action(SubscriptionModerate.get_action(_("Moderation"), "images/up.png"), pos_act=0, close=CLOSE_NO)


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_show(TITLE_MODIFY, "images/edit.png", close=CLOSE_YES)
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentAddModify(XferAddEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption_add = _("Add adherent")
    caption_modify = _("Modify adherent")


@ActionsManage.affect_grid(TITLE_EDIT, "images/show.png", unique=SELECT_SINGLE)
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentShow(XferShowEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Show adherent")


@MenuManage.describ('member.add_subscription')
class AdherentLicense(XferContainerCustom):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("License")

    def fillresponse(self):
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0, 1, 3)
        self.add_component(img)
        self.item = self.item.current_subscription
        if self.item is None:
            raise LucteriosException(IMPORTANT, _("no subscription!"))
        self.fill_from_model(
            1, 0, True, ['adherent', 'season', 'subscriptiontype'])
        row = self.get_max_row() + 1
        for lic in self.item.license_set.all():
            lbl = XferCompLabelForm('lbl_sep_%d' % lic.id)
            lbl.set_location(1, row, 2)
            lbl.set_value("{[hr/]}")
            self.add_component(lbl)
            row += 1
            if Params.getvalue("member-team-enable"):
                lbl = XferCompLabelForm('lblteam_%d' % lic.id)
                lbl.set_value_as_name(Params.getvalue("member-team-text"))
                lbl.set_location(1, row)
                self.add_component(lbl)
                lbl = XferCompLabelForm('team_%d' % lic.id)
                lbl.set_value(six.text_type(lic.team))
                lbl.set_location(2, row)
                self.add_component(lbl)
                row += 1
            if Params.getvalue("member-activite-enable"):
                lbl = XferCompLabelForm('lblactivity_%d' % lic.id)
                lbl.set_value_as_name(Params.getvalue("member-activite-text"))
                lbl.set_location(1, row)
                self.add_component(lbl)
                lbl = XferCompLabelForm('activity_%d' % lic.id)
                lbl.set_value(six.text_type(lic.activity))
                lbl.set_location(2, row)
                self.add_component(lbl)
                row += 1
            lbl = XferCompLabelForm('lblvalue_%d' % lic.id)
            lbl.set_value_as_name(_('value'))
            lbl.set_location(1, row)
            self.add_component(lbl)
            lbl = XferCompEdit('value_%d' % lic.id)
            lbl.set_value(lic.value)
            lbl.set_location(2, row)
            self.add_component(lbl)
            row += 1
        self.add_action(AdherentLicenseSave.get_action(TITLE_OK, 'images/ok.png'))
        self.add_action(WrapAction(TITLE_CANCEL, 'images/cancel.png'))


@MenuManage.describ('member.add_subscription')
class AdherentLicenseSave(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("License")

    def fillresponse(self):
        for param_id in self.params.keys():
            if param_id[:6] == 'value_':
                doc = License.objects.get(id=int(param_id[6:]))
                doc.value = self.getparam(param_id, '')
                doc.save()


@MenuManage.describ('member.add_subscription')
class AdherentSubscription(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Subscription")

    def fillresponse(self):
        if self.item.current_subscription is not None:
            self.redirect_action(SubscriptionShow.get_action(), modal=FORMTYPE_MODAL, close=CLOSE_YES, params={'subscription': self.item.current_subscription.id})


@ActionsManage.affect_grid(_("re-new"), "images/add.png", unique=SELECT_MULTI, condition=lambda xfer, gridname='': xfer.getparam('is_renew', False))
@MenuManage.describ('member.add_subscription')
class AdherentRenew(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("re-new")

    def fillresponse(self):
        text = _(
            "{[b]}Do you want that those %d old selected adherent(s) has been renew?{[/b]}{[br/]}Same subscription(s) will be applicated.{[br/]}No validated bill will be created for each subscritpion.") % len(self.items)
        if self.confirme(text):
            dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)
            for item in self.items:
                item.renew(dateref)


@ActionsManage.affect_grid(_("command"), "images/add.png", unique=SELECT_MULTI, condition=lambda xfer, gridname='': xfer.getparam('is_renew', False))
@MenuManage.describ('member.add_subscription')
class AdherentCommand(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Command subscription")

    def fillresponse(self, send_email=True):
        cmd_manager = CommandManager(self.getparam('CMD_FILE', ''), self.items)
        if self.getparam('SAVE') is None:
            dlg = self.create_custom(self.model)
            img = XferCompImage('img')
            img.set_value(self.icon_path())
            img.set_location(0, 0, 1, 4)
            dlg.add_component(img)
            lab = XferCompLabelForm('lbl_title')
            lab.set_value_as_title(self.caption)
            lab.set_location(1, 0, 2)
            dlg.add_component(lab)
            grid = XferCompGrid('AdhCmd')
            for fname, ftitle in cmd_manager.get_fields():
                grid.add_header(fname, ftitle)
            for cmd_id, cmd_item in cmd_manager.get_content_txt():
                for head_name, value in cmd_item.items():
                    grid.set_value(cmd_id, head_name, value)
            grid.set_location(1, 2, 2)
            grid.add_action(self.request, AdherentCommandModify.get_action(TITLE_MODIFY, "images/edit.png"), close=CLOSE_NO, unique=SELECT_SINGLE)
            grid.add_action(self.request, AdherentCommandDelete.get_action(TITLE_DELETE, "images/delete.png"), close=CLOSE_NO, unique=SELECT_SINGLE)
            dlg.params['CMD_FILE'] = cmd_manager.file_name
            dlg.add_component(grid)
            if len(grid.records) > 0:
                lab = XferCompLabelForm('lbl_send_email')
                lab.set_value_as_name(_('Send quotition by email for each adherent.'))
                lab.set_location(1, 3)
                dlg.add_component(lab)
                chk = XferCompCheck('send_email')
                chk.set_value(send_email)
                chk.set_location(2, 3)
                dlg.add_component(chk)
                dlg.add_action(AdherentCommand.get_action(TITLE_OK, "images/ok.png"), close=CLOSE_YES, params={'SAVE': 'YES'})
            dlg.add_action(WrapAction(TITLE_CLOSE, 'images/close.png'))
        else:
            dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)
            if send_email:
                param_email = self.request.META.get('HTTP_REFERER', self.request.build_absolute_uri()), self.language
            else:
                param_email = None
            nb_sub, nb_bill = cmd_manager.create_subscription(dateref, param_email)
            if send_email:
                msg = _('%(nbsub)d new subscription and %(nbbill)d quotation have been sent.') % {'nbsub': nb_sub, 'nbbill': nb_bill}
            else:
                msg = _('%d new subscription have been prepared.') % nb_sub
            self.message(msg)


@MenuManage.describ('member.add_subscription')
class AdherentCommandDelete(XferContainerAcknowledge):
    icon = "adherent.png"
    caption = _("Delete subscription command")

    def fillresponse(self, AdhCmd=0):
        cmd_manager = CommandManager(self.getparam('CMD_FILE', ''), self.items)
        cmd_manager.delete(AdhCmd)


@MenuManage.describ('member.add_subscription')
class AdherentCommandModify(XferContainerAcknowledge):
    icon = "adherent.png"
    caption = _("Modify subscription command")

    def fillresponse(self, AdhCmd=0):
        cmd_manager = CommandManager(self.getparam('CMD_FILE', ''), self.items)
        if self.getparam('SAVE') is None:
            dlg = self.create_custom(self.model)
            img = XferCompImage('img')
            img.set_value(self.icon_path())
            img.set_location(0, 0, 1, 4)
            dlg.add_component(img)
            lab = XferCompLabelForm('lbl_title')
            lab.set_value_as_title(self.caption)
            lab.set_location(1, 0)
            dlg.add_component(lab)
            row = dlg.get_max_row() + 1
            cmd_item = cmd_manager.get(AdhCmd)
            cmd_item_txt = cmd_manager.get_txt(cmd_item)
            for fname, ftitle in cmd_manager.get_fields():
                lbl = XferCompLabelForm("lbl" + fname)
                lbl.set_value_as_name(ftitle)
                lbl.set_location(1, row)
                dlg.add_component(lbl)
                if fname == "type":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(SubscriptionType.objects.all())
                    sel.set_value(cmd_item[fname])
                    sel.set_needed(True)
                    sel.set_location(2, row)
                    dlg.add_component(sel)
                elif fname == "team":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(Team.objects.all())
                    sel.set_value(cmd_item[fname][0])
                    sel.set_needed(True)
                    sel.set_location(2, row)
                    dlg.add_component(sel)
                elif fname == "activity":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(Activity.objects.all())
                    sel.set_value(cmd_item[fname][0])
                    sel.set_needed(True)
                    sel.set_location(2, row)
                    dlg.add_component(sel)
                elif fname == "reduce":
                    sel = XferCompFloat(fname)
                    sel.set_value(cmd_item[fname])
                    sel.set_location(2, row)
                    dlg.add_component(sel)
                else:
                    lbl = XferCompLabelForm(fname)
                    lbl.set_value(cmd_item_txt[fname])
                    lbl.set_location(2, row)
                    dlg.add_component(lbl)
                row += 1
            dlg.add_action(self.get_action(TITLE_OK, "images/ok.png"), close=CLOSE_YES, params={'SAVE': 'YES'})
            dlg.add_action(WrapAction(TITLE_CLOSE, 'images/close.png'))
        else:
            cmd_item = cmd_manager.get(AdhCmd)
            cmd_item['type'] = self.getparam("type", cmd_item['type'])
            cmd_item['team'] = self.getparam("team", cmd_item['team'])
            cmd_item['activity'] = self.getparam("activity", cmd_item['activity'])
            cmd_item['reduce'] = self.getparam("reduce", cmd_item['reduce'])
            cmd_manager.set(AdhCmd, cmd_item)


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('contacts.delete_abstractcontact')
class AdherentDel(XferDelete):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Delete adherent")


@ActionsManage.affect_other(_('Modify'), '')
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentDoc(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Modify document")

    def fillresponse(self):
        for param_id in self.params.keys():
            if param_id[:4] == 'doc_':
                doc = DocAdherent.objects.get(id=int(param_id[4:]))
                doc.value = self.getparam(param_id, False)
                doc.save()


@ActionsManage.affect_show(TITLE_PRINT, "images/print.png")
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentPrint(XferPrintAction):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Print adherent")
    action_class = AdherentShow


@ActionsManage.affect_list(TITLE_LABEL, "images/print.png")
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentLabel(XferPrintLabel, AdherentFilter):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Label adherent")

    def filter_callback(self, items):
        if self.getparam('CRITERIA') is None:
            current_filter, exclude_filter = AdherentFilter.get_filter(self)
            return items.filter(current_filter).exclude(exclude_filter)
        else:
            return items


@ActionsManage.affect_list(TITLE_LISTING, "images/print.png")
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentListing(XferPrintListing, AdherentFilter):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Listing adherent")

    def filter_callback(self, items):
        if self.getparam('CRITERIA') is None:
            current_filter, exclude_filter = AdherentFilter.get_filter(self)
            return items.filter(current_filter).exclude(exclude_filter)
        else:
            return items


def right_adherentconnection(request):
    if AdherentLicense.get_action().check_permission(request) and (signal_and_lock.Signal.call_signal("send_connection", None, None, None) != 0):
        return Params.getvalue("member-connection")
    else:
        return False


@ActionsManage.affect_list(_('Connection'), "images/passwd.png")
@MenuManage.describ(right_adherentconnection)
class AdherentConnection(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Check access right")

    def fillresponse(self):
        if self.confirme(_("Do you want to check the access right for all adherents ?")):
            if self.traitment("static/lucterios.CORE/images/info.png", _("Please, waiting..."), ""):
                nb_del, nb_add, nb_update = Season.current_season().check_connection()
                self.traitment_data[2] = _("{[center]}{[b]}Result{[/b]}{[/center]}{[br/]}%(nb_del)s removed connection(s).{[br/]}%(nb_add)s added connection(s).{[br/]}%(nb_update)s updated connection(s).") % {'nb_del': nb_del, 'nb_add': nb_add, 'nb_update': nb_update}


@MenuManage.describ('member.change_subscription')
class SubscriptionModerate(XferListEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Subscriptions to moderate")

    def fillresponse_header(self):
        self.fieldnames = ["adherent", "season", "subscriptiontype", "begin_date", "end_date"]
        self.filter = Q(status=0)
        self.params['status_filter'] = 0


@ActionsManage.affect_grid(_("Show adherent"), "", intop=True, unique=SELECT_SINGLE, condition=lambda xfer, gridname='': (xfer.getparam('adherent') == None))
@MenuManage.describ('member.add_subscription')
class SubscriptionOpenAdherent(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show adherent")

    def fillresponse(self):
        if 'status_filter' in self.params:
            del self.params['status_filter']
        self.redirect_action(AdherentShow.get_action(), params={'adherent': self.item.adherent_id})


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png", condition=lambda xfer, gridname='': (xfer.getparam('adherent') != None))
@ActionsManage.affect_show(TITLE_MODIFY, "images/edit.png", close=CLOSE_YES)
@MenuManage.describ('member.add_subscription')
class SubscriptionAddModify(XferAddEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption_add = _("Add subscription")
    caption_modify = _("Modify subscription")
    redirect_to_show = 'Bill'


@ActionsManage.affect_grid(TITLE_EDIT, "images/show.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.change_subscription')
class SubscriptionShow(XferShowEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show subscription")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.delete_subscription')
class SubscriptionDel(XferDelete):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Delete subscription")


@ActionsManage.affect_transition("status")
@MenuManage.describ('member.add_subscription')
class SubscriptionTransition(XferTransition):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'

    def fillresponse(self):
        if self.item.status == 0:
            self.item.send_email_param = (self.request.META.get('HTTP_REFERER', self.request.build_absolute_uri()), self.language)
        XferTransition.fillresponse(self)


@ActionsManage.affect_grid(_('Bill'), 'images/ok.png', unique=SELECT_SINGLE, close=CLOSE_NO, condition=lambda xfer, gridname='': (xfer.getparam('status_filter') == None) or (xfer.getparam('status_filter', -1) > 1))
@ActionsManage.affect_show(_('Bill'), 'images/ok.png', close=CLOSE_NO)
@MenuManage.describ('invoice.change_bill')
class SubscriptionShowBill(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show bill of subscription")

    def fillresponse(self):
        if self.item.bill_id is not None:
            self.redirect_action(ActionsManage.get_action_url('invoice.Bill', 'Show', self), close=CLOSE_NO, params={'bill': self.item.bill_id})


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.add_subscription')
class LicenseAddModify(XferAddEditor):
    icon = "adherent.png"
    model = License
    field_id = 'license'
    caption_add = _("Add license")
    caption_modify = _("Modify license")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.add_subscription')
class LicenseDel(XferDelete):
    icon = "adherent.png"
    model = License
    field_id = 'license'
    caption = _("Delete license")


@MenuManage.describ('member.change_adherent', FORMTYPE_MODAL, 'member.actions', _('Statistic of adherents and subscriptions'))
class AdherentStatistic(XferContainerCustom):
    icon = "statistic.png"
    model = Adherent
    field_id = 'adherent'
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
        sel.set_action(self.request, self.get_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(sel)
        stat_result = working_season.get_statistic()
        if len(stat_result) == 0:
            lab = XferCompLabelForm('lbl_season')
            lab.set_color('red')
            lab.set_value_as_infocenter(_('no subscription!'))
            lab.set_location(1, 1, 2)
            self.add_component(lab)
        else:
            tab_iden = 0
            for stat_title, stat_city, stat_type in stat_result:
                tab_iden += 1
                if (len(stat_city) > 0) and (len(stat_type) > 0):
                    self.new_tab(stat_title)
                    lab = XferCompLabelForm("lbltown_%d" % tab_iden)
                    lab.set_underlined()
                    lab.set_value(_("Result by city"))
                    lab.set_location(0, 1)
                    self.add_component(lab)
                    grid = XferCompGrid("town_%d" % tab_iden)
                    grid.add_header("city", _("city"))
                    grid.add_header("MajW", _("women major"))
                    grid.add_header("MajM", _("men major"))
                    grid.add_header("MinW", _("women minor"))
                    grid.add_header("MinM", _("men minor"))
                    grid.add_header("ratio", _("total (%)"))
                    cmp = 0
                    for stat_val in stat_city:
                        for stat_key in stat_val.keys():
                            grid.set_value(cmp, stat_key, stat_val[stat_key])
                        cmp += 1
                    grid.set_location(0, 2)
                    self.add_component(grid)

                    lab = XferCompLabelForm("lbltype_%d" % tab_iden)
                    lab.set_underlined()
                    lab.set_value(_("Result by type"))
                    lab.set_location(0, 3)
                    self.add_component(lab)
                    grid = XferCompGrid("type_%d" % tab_iden)
                    grid.add_header("type", _("type"))
                    grid.add_header("MajW", _("women major"))
                    grid.add_header("MajM", _("men major"))
                    grid.add_header("MinW", _("women minor"))
                    grid.add_header("MinM", _("men minor"))
                    grid.add_header("ratio", _("total (%)"))
                    cmp = 0
                    for stat_val in stat_type:
                        for stat_key in stat_val.keys():
                            if (stat_key == 'type') and not isinstance(stat_val['type'], six.text_type):
                                grid.set_value(cmp, stat_key, six.text_type(
                                    SubscriptionType.objects.get(id=stat_val['type'])))
                            else:
                                grid.set_value(
                                    cmp, stat_key, stat_val[stat_key])
                        cmp += 1
                    grid.set_location(0, 4)
                    self.add_component(grid)
        self.add_action(AdherentStatisticPrint.get_action(TITLE_PRINT, "images/print.png"),
                        close=CLOSE_NO, params={'classname': self.__class__.__name__})
        self.add_action(WrapAction(TITLE_CLOSE, 'images/close.png'))


@MenuManage.describ('member.change_adherent')
class AdherentStatisticPrint(XferPrintAction):
    icon = "statistic.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Statistic")
    action_class = AdherentStatistic
    with_text_export = True


@MenuManage.describ(None)
class SubscriptionAddForCurrent(SubscriptionAddModify):
    redirect_to_show = False

    def fillresponse(self):
        self.params['autocreate'] = 1
        current_contact = Individual.objects.get(user=self.request.user)
        current_contact = current_contact.get_final_child()
        if isinstance(current_contact, Adherent):
            self.item.adherent = current_contact
            self.params['adherent'] = current_contact.id
        else:
            self.item.adherent = Adherent()
        self.item.season = Season.current_season()
        SubscriptionAddModify.fillresponse(self)


@signal_and_lock.Signal.decorate('summary')
def summary_member(xfer):
    is_right = WrapAction.is_permission(xfer.request, 'member.change_adherent')
    try:
        current_adherent = Adherent.objects.get(user=xfer.request.user)
    except:
        current_adherent = None

    if is_right or (current_adherent is not None):
        row = xfer.get_max_row() + 1
        lab = XferCompLabelForm('membertitle')
        lab.set_value_as_infocenter(_("Adherents"))
        lab.set_location(0, row, 4)
        xfer.add_component(lab)
    if current_adherent is not None:
        ident = []
        if Params.getvalue("member-numero"):
            ident.append("%s %s" % (_('numeros'), current_adherent.num))
        if Params.getvalue("member-licence-enabled"):
            current_license = current_adherent.license
            if current_license is not None:
                ident.append(current_license)
        row = xfer.get_max_row() + 1
        lab = XferCompLabelForm('membercurrent')
        lab.set_value_as_header("{[br/]}".join(ident))
        lab.set_location(0, row, 4)
        xfer.add_component(lab)
    if is_right:
        row = xfer.get_max_row() + 1
        try:
            current_season = Season.current_season()
            dateref = current_season.date_ref
            lab = XferCompLabelForm('memberseason')
            lab.set_value_as_headername(six.text_type(current_season))
            lab.set_location(0, row + 1, 4)
            xfer.add_component(lab)
            nb_adh = len(Adherent.objects.filter(Q(subscription__begin_date__lte=dateref) & Q(
                subscription__end_date__gte=dateref) & Q(subscription__status=2)))
            lab = XferCompLabelForm('membernb')
            lab.set_value_as_header(_("Active adherents: %d") % nb_adh)
            lab.set_location(0, row + 2, 4)
            xfer.add_component(lab)
            nb_adhcreat = len(Adherent.objects.filter(
                Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref) & Q(subscription__status=1)))
            if nb_adhcreat > 0:
                lab = XferCompLabelForm('memberadhcreat')
                lab.set_value_as_header(_("No validated adherents: %d") % nb_adhcreat)
                lab.set_location(0, row + 3, 4)
                xfer.add_component(lab)
            nb_adhwait = len(Adherent.objects.filter(
                Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref) & Q(subscription__status=0)))
            if nb_adhwait > 0:
                lab = XferCompLabelForm('memberadhwait')
                lab.set_value_as_header(_("Adherents waiting moderation: %d") % nb_adhwait)
                lab.set_location(0, row + 4, 4)
                xfer.add_component(lab)
        except LucteriosException as lerr:
            lbl = XferCompLabelForm("member_error")
            lbl.set_value_center(six.text_type(lerr))
            lbl.set_location(0, row + 1, 4)
            xfer.add_component(lbl)
    if is_right or (current_adherent is not None):
        lab = XferCompLabelForm('member')
        lab.set_value_as_infocenter("{[hr/]}")
        lab.set_location(0, row + 5, 4)
        xfer.add_component(lab)
        return True
    else:
        return False


@signal_and_lock.Signal.decorate('change_bill')
def change_bill_member(action, old_bill, new_bill):
    if action == 'convert':
        for sub in Subscription.objects.filter(bill=old_bill):
            sub.bill = new_bill
            if sub.status == 1:
                sub.validate()
            sub.save()


@signal_and_lock.Signal.decorate('add_account')
def add_account_subscription(current_contact, xfer):
    if Params.getvalue("member-subscription-mode") > 0:
        current_subscription = Subscription.objects.filter(adherent_id=current_contact.id, season=Season.current_season())
        if len(current_subscription) == 0:
            xfer.new_tab(_('002@Subscription'))
            row = xfer.get_max_row() + 1
            btn = XferCompButton('btnnewsubscript')
            btn.set_location(1, row)
            btn.set_action(xfer.request, SubscriptionAddForCurrent.get_action(
                _('Subscription'), 'diacamma.member/images/adherent.png'), close=CLOSE_NO)
            xfer.add_component(btn)
