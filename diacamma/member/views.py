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
from importlib import import_module

from django.utils.translation import ugettext_lazy as _
from django.utils import formats
from django.db.models.functions import Concat, Trim
from django.db.models import Q, Value
from django.conf import settings

from lucterios.framework.xferadvance import XferListEditor, TITLE_OK, TITLE_ADD,\
    TITLE_MODIFY, TITLE_EDIT, TITLE_CANCEL, TITLE_LABEL, TITLE_LISTING,\
    TITLE_DELETE, TITLE_CLOSE, TITLE_PRINT, XferTransition, TITLE_CREATE
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage, \
    FORMTYPE_REFRESH, CLOSE_NO, SELECT_SINGLE, WrapAction, FORMTYPE_MODAL, \
    SELECT_MULTI, CLOSE_YES, SELECT_NONE
from lucterios.framework.xfercomponents import XferCompLabelForm, \
    XferCompCheckList, XferCompButton, XferCompSelect, XferCompDate, \
    XferCompImage, XferCompEdit, XferCompGrid, XferCompFloat, XferCompCheck
from lucterios.framework.xfergraphic import XferContainerAcknowledge, XferContainerCustom
from lucterios.framework.tools import convert_date, same_day_months_after
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework import signal_and_lock

from lucterios.CORE.xferprint import XferPrintAction
from lucterios.CORE.xferprint import XferPrintLabel
from lucterios.CORE.xferprint import XferPrintListing
from lucterios.CORE.editors import XferSavedCriteriaSearchEditor
from lucterios.CORE.parameters import Params, notfree_mode_connect

from lucterios.contacts.models import Individual, LegalEntity, Responsability,\
    AbstractContact
from lucterios.contacts.views_contacts import LegalEntityAddModify

from diacamma.accounting.models import Third
from diacamma.accounting.tools import format_with_devise
from diacamma.invoice.models import get_or_create_customer, Bill
from diacamma.member.models import Adherent, Subscription, Season, Age, Team, Activity, License, DocAdherent, SubscriptionType, CommandManager, Prestation, ContactAdherent
from lucterios.CORE.models import Preference


MenuManage.add_sub("association", None, "diacamma.member/images/association.png", _("Association"), _("Association tools"), 30)

MenuManage.add_sub("member.actions", "association", "diacamma.member/images/member.png",
                   _("Adherents"), _("Management of adherents and subscriptions."), 50)


class AdherentFilter(object):

    def get_filter(self):
        team = self.getparam("team", Preference.get_value('adherent-team', self.request.user))
        activity = self.getparam("activity", Preference.get_value('adherent-activity', self.request.user))
        genre = self.getparam("genre", Preference.get_value('adherent-genre', self.request.user))
        age = self.getparam("age", Preference.get_value('adherent-age', self.request.user))
        status = self.getparam("status", Preference.get_value('adherent-status', self.request.user))
        dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)
        if self.getparam('is_renew', False):
            date_one_year = same_day_months_after(dateref, -12)
            date_six_month = same_day_months_after(dateref, -6)
            date_three_month = same_day_months_after(dateref, -3)
            current_filter = Q(subscription__subscriptiontype__duration=0) & Q(subscription__end_date__gte=date_one_year)
            current_filter |= Q(subscription__subscriptiontype__duration=1) & Q(subscription__end_date__gte=date_six_month)
            current_filter |= Q(subscription__subscriptiontype__duration=2) & Q(subscription__end_date__gte=date_three_month)
            current_filter |= Q(subscription__subscriptiontype__duration=3) & Q(subscription__end_date__gte=date_one_year)
            exclude_filter = Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref)
        else:
            current_filter = Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref)
            exclude_filter = Q()
        if Params.getvalue("member-team-enable"):
            if len(team) > 0:
                current_filter &= Q(subscription__license__team__in=team) | Q(subscription__prestations__team__in=team)
        if Params.getvalue("member-activite-enable"):
            if len(activity) > 0:
                current_filter &= Q(subscription__license__activity__in=activity) | Q(subscription__prestations__activity__in=activity)
        if Params.getvalue("member-age-enable"):
            if len(age) > 0:
                age_filter = Q()
                for age_item in Age.objects.filter(id__in=age):
                    age_filter |= Q(birthday__gte="%d-01-01" % (dateref.year - age_item.maximum)) & Q(birthday__lte="%d-12-31" % (dateref.year - age_item.minimum))
                current_filter &= age_filter
        if Params.getvalue("member-filter-genre"):
            if genre != Adherent.GENRE_ALL:
                current_filter &= Q(genre=genre)
        if status == Subscription.STATUS_WAITING_BUILDING:
            current_filter &= Q(subscription__status__in=(Subscription.STATUS_BUILDING, Subscription.STATUS_VALID))
        else:
            current_filter &= Q(subscription__status=status)
        return (current_filter, exclude_filter)


class AdherentAbstractList(XferListEditor, AdherentFilter):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'

    def __init__(self, **kwargs):
        XferListEditor.__init__(self, **kwargs)
        self.size_by_page = Params.getvalue("member-size-page")

    def get_items_from_filter(self):
        current_filter, exclude_filter = self.get_filter()
        return self.model.objects.filter(current_filter).exclude(exclude_filter).distinct()

    def fillresponse_body(self):
        lineorder = self.getparam('GRID_ORDER%adherent', ())
        self.params['GRID_ORDER%adherent'] = ','.join([item.replace('family', 'responsability__legal_entity__name') for item in lineorder])
        XferListEditor.fillresponse_body(self)
        grid = self.get_components('adherent')
        family_header = grid.get_header('family')
        if family_header is not None:
            family_header.orderable = 1
        grid.order_list = lineorder
        self.params['GRID_ORDER%adherent'] = ','.join(lineorder)

    def fillresponse_header(self):
        row = self.get_max_row() + 1
        team = self.getparam("team", Preference.get_value('adherent-team', self.request.user))
        activity = self.getparam("activity", Preference.get_value('adherent-activity', self.request.user))
        genre = self.getparam("genre", Preference.get_value('adherent-genre', self.request.user))
        age = self.getparam("age", Preference.get_value('adherent-age', self.request.user))
        status = self.getparam("status", Preference.get_value('adherent-status', self.request.user))
        dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)

        col1 = 0
        if Params.getvalue("member-age-enable"):
            sel = XferCompCheckList('age')
            sel.set_select_query(Age.objects.all())
            sel.set_value(age)
            sel.set_location(col1, row)
            sel.description = _("Age")
            self.add_component(sel)
            col1 += 1

        if Params.getvalue("member-team-enable"):
            sel = XferCompCheckList('team')
            sel.set_select_query(Team.objects.filter(unactive=False))
            sel.set_value(team)
            sel.set_location(col1, row)
            sel.description = Params.getvalue("member-team-text")
            self.add_component(sel)
            col1 += 1

        if Params.getvalue("member-activite-enable"):
            sel = XferCompCheckList('activity')
            sel.set_select_query(Activity.get_all())
            sel.set_value(activity)
            sel.set_location(col1, row)
            sel.description = Params.getvalue("member-activite-text")
            self.add_component(sel)
            col1 += 1

        sel = XferCompSelect('status')
        sel.set_select(Subscription.SELECT_STATUS)
        sel.set_location(0, row + 1)
        sel.set_value(status)
        sel.description = _("status")
        self.add_component(sel)
        col2 = 1

        if Params.getvalue("member-filter-genre"):
            sel = XferCompSelect('genre')
            sel.set_select(Adherent.SELECT_GENRE)
            sel.set_location(col2, row + 1)
            sel.set_value(genre)
            sel.description = _("genre")
            self.add_component(sel)
            col2 += 1

        dtref = XferCompDate('dateref')
        dtref.set_value(dateref)
        dtref.set_needed(True)
        dtref.set_location(max(col1, col2), row)
        dtref.description = _("reference date")
        self.add_component(dtref)

        btn = XferCompButton('btndateref')
        btn.is_default = True
        btn.set_location(max(col1, col2), row + 1)
        btn.set_action(self.request, self.return_action(_('Refresh'), ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(btn)

        info_list = []
        self.params['TITLE'] = "%s - %s : %s" % (self.caption, _("reference date"), formats.date_format(dateref, "DATE_FORMAT"))
        info_list.append("{[b]}{[u]}%s{[/u]}{[/b]} : %s" % (_("status"), dict(Subscription.SELECT_STATUS)[status]))
        info_list.append("")
        if Params.getvalue("member-activite-enable") and (len(activity) > 0):
            info_list.append("{[b]}{[u]}%s{[/u]}{[/b]} : %s" % (Params.getvalue("member-activite-text"),
                                                                ", ".join([str(activity_item) for activity_item in Activity.objects.filter(id__in=activity)])))
            info_list.append("")
        if Params.getvalue("member-team-enable"):
            if len(team) == 1:
                first_team = Team.objects.get(id=team[0])
                self.params['TITLE'] = "%s - %s - %s : %s" % (self.caption, first_team, _("reference date"), formats.date_format(dateref, "DATE_FORMAT"))
                info_list.append("{[b]}{[u]}%s{[/u]}{[/b]}" % Params.getvalue("member-team-text"))
                info_list.append(first_team.description.replace("{[br/]}", "{[br]}"))
                info_list.append("")
            elif len(team) > 1:
                info_list.append("{[b]}{[u]}%s{[/u]}{[/b]} : %s" % (Params.getvalue("member-team-text"),
                                                                    ", ".join([str(team_item) for team_item in Team.objects.filter(id__in=team)])))
                info_list.append("")

        if Params.getvalue("member-age-enable") and (len(age) > 0):
            info_list.append("{[b]}{[u]}%s{[/u]}{[/b]} : %s" % (_("Age"),
                                                                ", ".join([str(age_item) for age_item in Age.objects.filter(id__in=age)])))
            info_list.append("")

        if Params.getvalue("member-filter-genre") and (genre != Adherent.GENRE_ALL):
            info_list.append("{[b]}{[u]}%s{[/u]}{[/b]} : %s" % (_("genre"), dict(Adherent.SELECT_GENRE)[genre]))
            info_list.append("")
        self.params['INFO'] = '{[br]}'.join(info_list)


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
        self.get_components(self.field_id).add_action(self.request, AdherentSubscription.get_action(_("Subscription"), ""),
                                                      unique=SELECT_SINGLE, close=CLOSE_NO)
        if Params.getvalue("member-licence-enabled"):
            self.get_components(self.field_id).add_action(self.request, AdherentLicense.get_action(_("License"), ""),
                                                          unique=SELECT_SINGLE, close=CLOSE_NO)
        if Params.getvalue("member-subscription-mode") == Subscription.MODE_WITHMODERATE:
            self.add_action(SubscriptionModerate.get_action(_("Moderation"), "images/up.png"), pos_act=0, close=CLOSE_NO)


def show_thirdlist(request):
    if AdherentActiveList.get_action().check_permission(request):
        return Params.getobject("member-family-type") is not None
    else:
        return False


@MenuManage.describ(show_thirdlist, FORMTYPE_NOMODAL, 'member.actions', _('List of  families of members up to date with their subscription'))
class AdherentContactList(XferListEditor):
    icon = "adherent.png"
    model = ContactAdherent
    field_id = 'abstractcontact'
    caption = _("Season adherents")

    def __init__(self, **kwargs):
        XferListEditor.__init__(self, **kwargs)
        self.size_by_page = Params.getvalue("member-size-page")
        self.caption = _("Address of season adherents")

    def get_items_from_filter(self):
        items = self.model.objects.annotate(completename=Trim(Concat('legalentity__name', Value(' '), 'individual__lastname', Value(' '), 'individual__firstname')))
        return items.filter(self.filter).order_by('completename').distinct()

    def fillresponse_header(self):
        family_type = Params.getobject("member-family-type")
        if family_type is None:
            raise LucteriosException(IMPORTANT, _('No family type!'))

        contact_filter = self.getparam('filter', '')
        comp = XferCompEdit('filter')
        comp.set_value(contact_filter)
        comp.set_action(self.request, self.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        comp.set_location(0, 1, 2)
        comp.description = _('Filtrer by contact')
        comp.is_default = True
        self.add_component(comp)

        dateref = convert_date(self.getparam("dateref", ""), Season.current_season().date_ref)
        dtref = XferCompDate('dateref')
        dtref.set_value(dateref)
        dtref.set_needed(True)
        dtref.set_location(2, 1)
        dtref.description = _("reference date")
        dtref.set_action(self.request, self.return_action(), modal=FORMTYPE_REFRESH)
        self.add_component(dtref)

        season = Season.get_from_date(dateref)
        self.params['season_id'] = season.id
        self.fieldnames = ["ident", "address", "city", "tel1", "tel2", "emails", "adherents"]
        indiv_filter = Q(individual__adherent__subscription__season=season) & Q(individual__adherent__subscription__status__in=(Subscription.STATUS_BUILDING, Subscription.STATUS_VALID)) & Q(individual__responsability__isnull=True)
        legal_filter = Q(legalentity__responsability__individual__adherent__subscription__season=season) & Q(legalentity__responsability__individual__adherent__subscription__status__in=(Subscription.STATUS_BUILDING, Subscription.STATUS_VALID)) & Q(legalentity__structure_type=family_type)
        self.filter = Q()
        if contact_filter != "":
            q_legalentity = Q(legalentity__name__icontains=contact_filter)
            q_individual = Q(completename__icontains=contact_filter)
            self.filter &= (q_legalentity | q_individual)
        self.filter &= (legal_filter | indiv_filter)

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        grid = self.get_components(self.field_id)
        grid.colspan = 3
        grid.add_action(self.request, ActionsManage.get_action_url(AbstractContact.get_long_name(), "Show", self), modal=FORMTYPE_MODAL, unique=SELECT_SINGLE, close=CLOSE_NO, params={'SubscriptionBefore': 'YES'})


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('To find an adherent following a set of criteria.'))
class AdherentSearch(XferSavedCriteriaSearchEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Search adherent")

    def __init__(self, **kwargs):
        XferSavedCriteriaSearchEditor.__init__(self, **kwargs)
        self.size_by_page = Params.getvalue("member-size-page")


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with old subscribtion not renew yet'))
class AdherentRenewList(AdherentAbstractList):
    caption = _("Adherents to renew")

    def fillresponse_header(self):
        self.params['is_renew'] = True
        AdherentAbstractList.fillresponse_header(self)
        self.fieldnames = Adherent.get_renew_fields()

    def fillresponse(self):
        AdherentAbstractList.fillresponse(self)
        self.item.editor.add_email_selector(self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        if Params.getvalue("member-subscription-mode") == Subscription.MODE_WITHMODERATE:
            self.add_action(SubscriptionModerate.get_action(_("Moderation"), "images/up.png"), pos_act=0, close=CLOSE_NO)


@ActionsManage.affect_grid(TITLE_CREATE, "images/new.png")
@ActionsManage.affect_show(TITLE_MODIFY, "images/edit.png", close=CLOSE_YES)
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentAddModify(XferAddEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption_add = _("Add adherent")
    caption_modify = _("Modify adherent")


@ActionsManage.affect_list(TITLE_PRINT, "images/print.png", condition=lambda xfer: Params.getobject("member-family-type") is not None)
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentContactPrint(XferPrintAction):
    icon = "adherent.png"
    model = ContactAdherent
    field_id = 'abstractcontact'
    caption = _("Print adherent")
    action_class = AdherentContactList
    with_text_export = True


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
        self.fill_from_model(1, 0, True, ['adherent', 'season', 'subscriptiontype'])
        row = self.get_max_row() + 1
        for lic in self.item.license_set.all():
            lbl = XferCompLabelForm('lbl_sep_%d' % lic.id)
            lbl.set_location(1, row, 2)
            lbl.set_value("{[hr/]}")
            self.add_component(lbl)
            row += 1
            if Params.getvalue("member-team-enable"):
                lbl = XferCompLabelForm('team_%d' % lic.id)
                lbl.set_value(str(lic.team))
                lbl.set_location(1, row)
                lbl.description = Params.getvalue("member-team-text")
                self.add_component(lbl)
                row += 1
            if Params.getvalue("member-activite-enable"):
                lbl = XferCompLabelForm('activity_%d' % lic.id)
                lbl.set_value(str(lic.activity))
                lbl.set_location(1, row)
                lbl.description = Params.getvalue("member-activite-text")
                self.add_component(lbl)
                row += 1
            lbl = XferCompEdit('value_%d' % lic.id)
            lbl.set_value(lic.value)
            lbl.set_location(1, row)
            lbl.description = _('value')
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
        text = _("{[b]}Do you want that those %d old selected adherent(s) has been renew?{[/b]}{[br/]}Same subscription(s) will be applicated.{[br/]}No validated bill will be created for each subscritpion.") % len(self.items)
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

    def fillresponse(self, send_email=False):
        cmd_manager = CommandManager(self.request.user, self.getparam('CMD_FILE', ''), self.items)
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
                grid.add_header(fname, ftitle, htype=format_with_devise(7) if fname == "reduce" else None)
            for cmd_id, cmd_item in cmd_manager.get_content_txt():
                for head_name, value in cmd_item.items():
                    grid.set_value(cmd_id, head_name, value)
            grid.set_location(1, 2, 2)
            grid.add_action(self.request, AdherentCommandModify.get_action(TITLE_MODIFY, "images/edit.png"), close=CLOSE_NO, unique=SELECT_SINGLE)
            grid.add_action(self.request, AdherentCommandDelete.get_action(TITLE_DELETE, "images/delete.png"), close=CLOSE_NO, unique=SELECT_SINGLE)
            dlg.params['CMD_FILE'] = cmd_manager.file_name
            dlg.add_component(grid)
            if len(grid.records) > 0:
                fct_mailing_mod = import_module('lucterios.mailing.email_functions')
                if (fct_mailing_mod is not None) and fct_mailing_mod.will_mail_send():
                    chk = XferCompCheck('send_email')
                    chk.set_value(send_email)
                    chk.set_location(1, 3)
                    chk.description = _('Send quotition by email for each adherent.')
                    dlg.add_component(chk)
                else:
                    dlg.params['send_email'] = False
                dlg.add_action(AdherentCommand.get_action(TITLE_OK, "images/ok.png"), close=CLOSE_YES, params={'SAVE': 'YES'})
                dlg.add_action(WrapAction(TITLE_CANCEL, 'images/cancel.png'))
            else:
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
        cmd_manager = CommandManager(self.request.user, self.getparam('CMD_FILE', ''), self.items)
        cmd_manager.delete(AdhCmd)


@MenuManage.describ('member.add_subscription')
class AdherentCommandModify(XferContainerAcknowledge):
    icon = "adherent.png"
    caption = _("Modify subscription command")

    def fillresponse(self, AdhCmd=0):
        cmd_manager = CommandManager(self.request.user, self.getparam('CMD_FILE', ''), self.items)
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
                if fname == "type":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(SubscriptionType.objects.filter(unactive=False))
                    sel.set_value(cmd_item[fname])
                    sel.set_needed(True)
                    sel.set_location(1, row)
                    sel.description = ftitle
                    dlg.add_component(sel)
                elif fname == "team":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(Team.objects.filter(unactive=False))
                    sel.set_value(cmd_item[fname][0])
                    sel.set_needed(True)
                    sel.set_location(1, row)
                    sel.description = ftitle
                    dlg.add_component(sel)
                elif fname == "activity":
                    sel = XferCompSelect(fname)
                    sel.set_select_query(Activity.get_all())
                    sel.set_value(cmd_item[fname][0])
                    sel.set_needed(True)
                    sel.set_location(1, row)
                    sel.description = ftitle
                    dlg.add_component(sel)
                elif fname == "reduce":
                    sel = XferCompFloat(fname)
                    sel.set_value(cmd_item[fname])
                    sel.set_location(1, row)
                    sel.description = ftitle
                    dlg.add_component(sel)
                elif fname == "prestations":
                    sel = XferCompCheckList(fname)
                    sel.simple = 2
                    sel.set_select_query(Prestation.objects.filter(team__unactive=False))
                    sel.set_value(cmd_item[fname])
                    sel.set_location(1, row)
                    sel.description = ftitle
                    dlg.add_component(sel)
                else:
                    lbl = XferCompLabelForm(fname)
                    lbl.set_value(cmd_item_txt[fname])
                    lbl.set_location(1, row)
                    lbl.description = ftitle
                    dlg.add_component(lbl)
                row += 1
            dlg.add_action(self.return_action(TITLE_OK, "images/ok.png"), close=CLOSE_YES, params={'SAVE': 'YES'})
            dlg.add_action(WrapAction(TITLE_CLOSE, 'images/close.png'))
        else:
            cmd_item = cmd_manager.get(AdhCmd)
            cmd_item['type'] = self.getparam("type", cmd_item['type'])
            cmd_item['team'] = self.getparam("team", cmd_item['team'])
            cmd_item['activity'] = self.getparam("activity", cmd_item['activity'])
            cmd_item['reduce'] = self.getparam("reduce", cmd_item['reduce'])
            cmd_item['prestations'] = self.getparam("prestations", cmd_item['prestations'])
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
            return items.filter(current_filter).exclude(exclude_filter).distinct()
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
            return items.filter(current_filter).exclude(exclude_filter).distinct()
        else:
            return items


def right_adherentconnection(request):
    if AdherentLicense.get_action().check_permission(request) and (signal_and_lock.Signal.call_signal("send_connection", None, None, None) != 0):
        return Params.getvalue("member-connection") == Adherent.CONNECTION_BYADHERENT
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
                nb_del, nb_add, nb_update, error_sending = Season.current_season().check_connection()
                ending_msg = _("{[center]}{[b]}Result{[/b]}{[/center]}{[br/]}%(nb_del)s removed connection(s).{[br/]}%(nb_add)s added connection(s).{[br/]}%(nb_update)s updated connection(s).") % {'nb_del': nb_del, 'nb_add': nb_add, 'nb_update': nb_update}
                if len(error_sending) > 0:
                    ending_msg += _("{[br/]}{[br/]}%d email(s) failed:") % len(error_sending)
                    ending_msg += "{[ul]}"
                    for error_item in error_sending:
                        ending_msg += "{[li]}%s : %s{[/li]}" % error_item
                    ending_msg += "{[/ul]}"
                self.traitment_data[2] = ending_msg


class BaseAdherentFamilyList(XferContainerCustom):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Family")

    def __init__(self):
        XferContainerCustom.__init__(self)
        self.family_type = None

    def fillresponse(self):
        self.family_type = Params.getobject("member-family-type")
        if self.family_type is None:
            raise LucteriosException(IMPORTANT, _('No family type!'))
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0)
        self.add_component(img)
        lbl = XferCompLabelForm('title')
        lbl.set_value_as_title(_('Add a family for "%s"') % self.item)
        lbl.set_location(1, 0)
        self.add_component(lbl)

        name_filter = self.getparam('namefilter', self.item.lastname)
        comp = XferCompEdit('namefilter')
        comp.set_value(name_filter)
        comp.is_default = True
        comp.set_action(self.request, self.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        comp.set_location(0, 1)
        comp.description = _('Filtrer by name')
        self.add_component(comp)

        grid = XferCompGrid('legal_entity')
        grid.set_model(self.family_type.legalentity_set.filter(name__icontains=name_filter), None, self)
        grid.set_location(0, 2, 2)
        grid.set_size(200, 500)
        self.add_component(grid)
        self.add_action(WrapAction(TITLE_CLOSE, 'images/close.png'))


@ActionsManage.affect_other(_('Family'), "images/add.png")
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentFamilyAdd(BaseAdherentFamilyList):

    def fillresponse(self):
        BaseAdherentFamilyList.fillresponse(self)
        grid = self.get_components('legal_entity')
        grid.add_action(self.request, AdherentFamilySelect.get_action(_("Select"), "images/ok.png"), close=CLOSE_YES, unique=SELECT_SINGLE)
        grid.add_action(self.request, AdherentFamilyCreate.get_action(TITLE_CREATE, "images/new.png"), close=CLOSE_YES, unique=SELECT_NONE, params=self.item.get_default_family_value())
        grid.add_action(self.request, ActionsManage.get_action_url('contacts.LegalEntity', 'Show', self), close=CLOSE_NO, unique=SELECT_SINGLE)


@ActionsManage.affect_other(_("Family"), "")
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentFamilySelect(XferContainerAcknowledge):
    icon = "adherent.png"
    model = LegalEntity
    field_id = 'legal_entity'

    def fillresponse(self, adherent=0):
        Responsability.objects.create(individual_id=adherent, legal_entity=self.item)


@MenuManage.describ('contacts.add_abstractcontact')
class AdherentFamilyCreate(LegalEntityAddModify):
    icon = "/static/lucterios.contacts/images/legalEntity.png"
    redirect_to_show = 'FamilySelect'

    def fillresponse(self):
        LegalEntityAddModify.fillresponse(self)
        self.change_to_readonly('structure_type')


@ActionsManage.affect_other(_("Family"), "images/add.png")
@MenuManage.describ('contacts.add_abstractcontact')
class FamilyAdherentAdd(BaseAdherentFamilyList):

    def fillresponse(self):
        BaseAdherentFamilyList.fillresponse(self)
        grid = self.get_components('legal_entity')
        grid.add_action(self.request, FamilyAdherentCreate.get_action(_("Select"), "images/ok.png"), close=CLOSE_YES, unique=SELECT_SINGLE)
        grid.add_action(self.request, ActionsManage.get_action_url('contacts.LegalEntity', 'AddModify', self), close=CLOSE_YES, unique=SELECT_NONE, params={'name': self.getparam('namefilter', '')})
        grid.add_action(self.request, ActionsManage.get_action_url('contacts.LegalEntity', 'Show', self), close=CLOSE_NO, unique=SELECT_SINGLE)


@MenuManage.describ('contacts.add_abstractcontact')
class FamilyAdherentCreate(AdherentAddModify):
    redirect_to_show = 'AdherentAdded'

    def fillresponse(self):
        if self.getparam('CHANGED') is None:
            self.params['CHANGED'] = 'YES'
            current_family = LegalEntity.objects.get(id=self.getparam('legal_entity', 0))
            self.item.lastname = current_family.name
            for field_name in ['address', 'postal_code', 'city', 'country', 'tel1', 'tel2', 'email']:
                setattr(self.item, field_name, getattr(current_family, field_name))
        AdherentAddModify.fillresponse(self)


@ActionsManage.affect_other(_("Family"), "")
@MenuManage.describ('contacts.add_abstractcontact')
class FamilyAdherentAdded(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'

    def fillresponse(self, legal_entity=0):
        Responsability.objects.create(individual=self.item, legal_entity_id=legal_entity)
        self.redirect_action(AdherentShow.get_action(), params={self.field_id: self.item.id})


@MenuManage.describ('member.change_subscription')
class SubscriptionModerate(XferListEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Subscriptions to moderate")

    def fillresponse_header(self):
        self.fieldnames = ["adherent", "season", "subscriptiontype", "begin_date", "end_date"]
        self.filter = Q(status=Subscription.STATUS_WAITING)
        self.params['status_filter'] = Subscription.STATUS_WAITING


@ActionsManage.affect_grid(_("Show adherent"), "images/open.png", intop=True, unique=SELECT_SINGLE, condition=lambda xfer, gridname='': (xfer.getparam('adherent') is None) and (xfer.getparam('individual') is None))
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


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png", condition=lambda xfer, gridname='': (xfer.getparam('adherent') is not None) or (xfer.getparam('individual') is not None))
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
        if self.item.status == Subscription.STATUS_WAITING:
            self.item.send_email_param = (self.request.META.get('HTTP_REFERER', self.request.build_absolute_uri()), self.language)
        XferTransition.fillresponse(self)


@ActionsManage.affect_grid(_('Bill'), 'images/ok.png', unique=SELECT_SINGLE, close=CLOSE_NO, condition=lambda xfer, gridname='': (xfer.getparam('status_filter') is None) or (xfer.getparam('status_filter', -1) not in (-1, Subscription.STATUS_WAITING, Subscription.STATUS_BUILDING)))
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
    caption_add = _("Add involvement")
    caption_modify = _("Modify involvement")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.add_subscription')
class LicenseDel(XferDelete):
    icon = "adherent.png"
    model = License
    field_id = 'license'
    caption = _("Delete involvement")


@MenuManage.describ('member.change_adherent', FORMTYPE_MODAL, 'member.actions', _('Statistic of adherents and subscriptions'))
class AdherentStatistic(XferContainerCustom):
    icon = "statistic.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Statistic")
    readonly = True
    methods_allowed = ('GET', )

    def add_static_grid(self, grid_title, grid_name, stat_city, main_id, main_name):
        row = self.get_max_row()
        lab = XferCompLabelForm("lbl%s" % grid_name)
        lab.set_underlined()
        lab.set_value(grid_title)
        lab.set_location(0, row + 1)
        self.add_component(lab)
        grid = XferCompGrid(grid_name)
        grid.add_header(main_id, main_name)
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
        grid.set_location(0, row + 2)
        self.add_component(grid)

    def fillresponse(self, season, only_valid=True):
        if season is None:
            working_season = Season.current_season()
        else:
            working_season = Season.objects.get(id=season)
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0)
        self.add_component(img)
        sel = XferCompSelect('season')
        sel.set_needed(True)
        sel.set_select_query(Season.objects.all())
        sel.set_value(working_season.id)
        sel.set_location(1, 0)
        sel.description = _('season')
        sel.set_action(self.request, self.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(sel)

        check = XferCompCheck('only_valid')
        check.set_value(only_valid)
        check.set_location(1, 1)
        check.description = _('only validated subscription')
        check.set_action(self.request, self.return_action('', ''), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(check)

        stat_result = working_season.get_statistic(only_valid)
        if len(stat_result) == 0:
            lab = XferCompLabelForm('lbl_season')
            lab.set_color('red')
            lab.set_value_as_infocenter(_('no subscription!'))
            lab.set_location(1, 2, 2)
            self.add_component(lab)
        else:
            tab_iden = 0
            for stat_title, stat_city, stat_type, stat_older, stat_team, stat_activity in stat_result:
                tab_iden += 1
                if (len(stat_city) > 0) and (len(stat_type) > 0):
                    self.new_tab(stat_title)
                    self.add_static_grid(_("Result by city"), 'town_%d' % tab_iden, stat_city, "city", _("city"))
                    self.add_static_grid(_("Result by type"), 'type_%d' % tab_iden, stat_type, "type", _("type"))

                    if stat_older is not None:
                        self.add_static_grid(_("Result by seniority"), 'seniority_%d' % tab_iden, stat_older, "seniority", _("count of subscription"))

                    if stat_team is not None:
                        self.add_static_grid(_("Result by %s") % Params.getvalue("member-team-text").lower(), 'team_%d' % tab_iden,
                                             stat_team, "team", Params.getvalue("member-team-text"))

                    if stat_activity is not None:
                        self.add_static_grid(_("Result by %s") % Params.getvalue("member-activite-text").lower(), 'activity_%d' % tab_iden,
                                             stat_activity, "activity", Params.getvalue("member-activite-text"))

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


def right_adherentaccess(request):
    if not notfree_mode_connect():
        return False
    if (len(settings.AUTHENTICATION_BACKENDS) != 1) or (settings.AUTHENTICATION_BACKENDS[0] != 'django.contrib.auth.backends.ModelBackend'):
        return False
    if (signal_and_lock.Signal.call_signal("send_connection", None, None, None) == 0):
        return False
    if Params.getvalue("member-connection") in (Adherent.CONNECTION_NO, Adherent.CONNECTION_BYADHERENT):
        return False
    return not request.user.is_authenticated


@MenuManage.describ(right_adherentaccess, FORMTYPE_MODAL, 'core.general', _("Ask adherent access"))
class AskAdherentAccess(XferContainerAcknowledge):
    caption = _("Ask adherent access")
    icon = "images/passwd.png"

    def _fill_dialog(self):
        dlg = self.create_custom()
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0, 1, 3)
        dlg.add_component(img)
        lbl = XferCompLabelForm('lbl_title')
        lbl.set_location(1, 0, 2)
        lbl.set_value_as_header(_("To receive by email a login and a password to connect in this site."))
        dlg.add_component(lbl)
        email = XferCompEdit('email')
        email.set_location(1, 1)
        email.mask = r"[^@]+@[^@]+\.[^@]+"
        email.description = _("email")
        dlg.add_component(email)
        dlg.add_action(self.return_action(TITLE_OK, 'images/ok.png'), params={"CONFIRME": "YES"})
        dlg.add_action(WrapAction(TITLE_CANCEL, 'images/cancel.png'))

    def fillresponse(self):
        try:
            if self.getparam("CONFIRME", "") != "YES":
                self._fill_dialog()
            elif Season.current_season().ask_member_connection(self.getparam("email", "")):
                self.message(_("Connection parametrer send."))
            else:
                self.message(_("This email don't match with an active adherent !"), 3)
        except Exception as error:
            self.message(str(error), 4)


@signal_and_lock.Signal.decorate('auth_action')
def auth_action_member(actions_basic):
    actions_basic.append(AskAdherentAccess.get_action(_("Ask adherent access")))


@ActionsManage.affect_list(_('Disable access'), "images/passwd.png")
@MenuManage.describ(lambda request: Params.getvalue("member-connection") == Adherent.CONNECTION_BYASKING)
class AdherentDisableConnection(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Disable access right")

    def fillresponse(self):
        if self.confirme(_("Do you want to disable access right for old adherents ?")):
            if self.traitment("static/lucterios.CORE/images/info.png", _("Please, waiting..."), ""):
                nb_del = Season.current_season().disabled_old_connection()
                ending_msg = _("{[center]}{[b]}Result{[/b]}{[/center]}{[br/]}%(nb_del)s removed connection(s).") % {'nb_del': nb_del}
                self.traitment_data[2] = ending_msg


@signal_and_lock.Signal.decorate('post_merge')
def post_merge_member(item):
    if isinstance(item, Individual):
        item = item.get_final_child()
        if isinstance(item, Adherent) and (item.family is not None):
            adh_third = Third.objects.filter(contact_id=item.id).first()
            if adh_third is not None:
                family_third = get_or_create_customer(item.family.id)
                for bill in Bill.objects.filter(third=adh_third, status=Bill.STATUS_BUILDING):
                    bill.third = family_third
                    bill.save()
                    subscription = bill.subscription_set.first()
                    if (subscription is not None) and (subscription.status in (Subscription.STATUS_WAITING, Subscription.STATUS_BUILDING)):
                        subscription.change_bill()


@signal_and_lock.Signal.decorate('situation')
def situation_member(xfer):
    if not hasattr(xfer, 'add_component'):
        try:
            Adherent.objects.get(user=xfer.user)
            return True
        except Exception:
            return False
    else:
        try:
            current_adherent = Adherent.objects.get(user=xfer.request.user)
            row = xfer.get_max_row() + 1
            lab = XferCompLabelForm('membertitle')
            lab.set_value_as_infocenter(_("Adherents"))
            lab.set_location(0, row, 4)
            xfer.add_component(lab)
            ident = []
            if Params.getvalue("member-numero"):
                ident.append("%s %s" % (_('numeros'), current_adherent.num))
            if Params.getvalue("member-licence-enabled"):
                current_license = current_adherent.license
                if current_license is not None:
                    ident.extend(current_license)
            lab = XferCompLabelForm('membercurrent')
            lab.set_value_as_header("{[br/]}".join(ident))
            lab.set_location(0, row + 1, 4)
            xfer.add_component(lab)
            lab = XferCompLabelForm('member')
            lab.set_value_as_infocenter("{[hr/]}")
            lab.set_location(0, row + 2, 4)
            xfer.add_component(lab)
            return True
        except Exception:
            pass
        return False


@signal_and_lock.Signal.decorate('summary')
def summary_member(xfer):
    if not hasattr(xfer, 'add_component'):
        return WrapAction.is_permission(xfer, 'member.change_adherent')
    else:
        if WrapAction.is_permission(xfer.request, 'member.change_adherent'):
            row = xfer.get_max_row() + 1
            lab = XferCompLabelForm('membertitle')
            lab.set_value_as_infocenter(_("Adherents"))
            lab.set_location(0, row, 4)
            xfer.add_component(lab)
            try:
                current_season = Season.current_season()
                dateref = current_season.date_ref
                lab = XferCompLabelForm('memberseason')
                lab.set_value_as_headername(str(current_season))
                lab.set_location(0, row + 1, 4)
                xfer.add_component(lab)
                nb_adh = Adherent.objects.filter(Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref) & Q(subscription__status=Subscription.STATUS_VALID)).distinct().count()
                lab = XferCompLabelForm('membernb')
                lab.set_value_as_header(_("Active adherents: %d") % nb_adh)
                lab.set_location(0, row + 2, 4)
                xfer.add_component(lab)
                if show_thirdlist(xfer.request):
                    family_type = Params.getobject("member-family-type")
                    legal_filter = Q(legalentity__responsability__individual__adherent__subscription__season=current_season) & Q(legalentity__responsability__individual__adherent__subscription__status__in=(Subscription.STATUS_BUILDING, Subscription.STATUS_VALID)) & Q(legalentity__structure_type=family_type)
                    indiv_filter = Q(individual__adherent__subscription__season=current_season) & Q(individual__adherent__subscription__status__in=(Subscription.STATUS_BUILDING, Subscription.STATUS_VALID)) & Q(individual__responsability__isnull=True)
                    nb_family = ContactAdherent.objects.filter(legal_filter | indiv_filter).distinct().count()
                    lab = XferCompLabelForm('familynb')
                    lab.set_value_as_header(_("Active families: %d") % nb_family)
                    lab.set_location(0, row + 3, 4)
                    xfer.add_component(lab)
                nb_adhcreat = Adherent.objects.filter(Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref) & Q(subscription__status=Subscription.STATUS_BUILDING)).distinct().count()
                if nb_adhcreat > 0:
                    lab = XferCompLabelForm('memberadhcreat')
                    lab.set_value_as_header(_("No validated adherents: %d") % nb_adhcreat)
                    lab.set_location(0, row + 4, 4)
                    xfer.add_component(lab)
                nb_adhwait = Adherent.objects.filter(Q(subscription__begin_date__lte=dateref) & Q(subscription__end_date__gte=dateref) & Q(subscription__status=Subscription.STATUS_WAITING)).distinct().count()
                if nb_adhwait > 0:
                    lab = XferCompLabelForm('memberadhwait')
                    lab.set_value_as_header(_("Adherents waiting moderation: %d") % nb_adhwait)
                    lab.set_location(0, row + 5, 4)
                    xfer.add_component(lab)
            except LucteriosException as lerr:
                lbl = XferCompLabelForm("member_error")
                lbl.set_value_center(str(lerr))
                lbl.set_location(0, row + 1, 4)
                xfer.add_component(lbl)
            if hasattr(settings, "DIACAMMA_MAXACTIVITY"):
                lbl = XferCompLabelForm("limit_activity")
                lbl.set_value(_('limitation: %d activities allowed') % getattr(settings, "DIACAMMA_MAXACTIVITY"))
                lbl.set_italic()
                lbl.set_location(0, row + 6, 4)
                xfer.add_component(lbl)
            lab = XferCompLabelForm('member')
            lab.set_value_as_infocenter("{[hr/]}")
            lab.set_location(0, row + 7, 4)
            xfer.add_component(lab)
            return True
        else:
            return False


@signal_and_lock.Signal.decorate('change_bill')
def change_bill_member(action, old_bill, new_bill):
    if action == 'convert':
        for sub in Subscription.objects.filter(bill=old_bill):
            sub.bill = new_bill
            if sub.status == Subscription.STATUS_BUILDING:
                sub.status = Subscription.STATUS_VALID
            sub.save(with_bill=False)


@MenuManage.describ('')
class SubscriptionEditAdherent(AdherentAddModify):

    def fillresponse(self):
        self.item = Adherent.objects.filter(subscription__id=self.getparam('subscription', 0)).first()
        AdherentAddModify.fillresponse(self)


@signal_and_lock.Signal.decorate('add_account')
def add_account_subscription(current_contact, xfer):
    adherent = Adherent.objects.filter(id=current_contact.id).first()
    family = adherent.family if adherent is not None else None
    if family is not None:
        from lucterios.contacts.views import Account
        for comp_id in [key for (key, comp) in xfer.components.items() if comp.tab == 1]:
            del xfer.components[comp_id]
        structure_type = xfer.get_components('legalentity_structure_type')
        if structure_type is not None:
            xfer.remove_component("__tab_%d" % structure_type.tab)
        Account.add_legalentity(xfer, family, _('family'), 1)
        old_subcomp = xfer.get_components('subscription')
        xfer.tab = old_subcomp.tab
        current_subscriptions = Subscription.objects.filter(Q(adherent__responsability__legal_entity=family) & Q(season=Season.current_season()))
        grid = XferCompGrid('subscription')
        grid.no_pager = True
        grid.set_model(current_subscriptions, Subscription.get_other_fields(), xfer)
        grid.set_location(old_subcomp.col, old_subcomp.row, old_subcomp.colspan)
        grid.add_action(xfer.request, SubscriptionEditAdherent.get_action(TITLE_EDIT, "images/edit.png"), modal=FORMTYPE_MODAL, close=CLOSE_NO, unique=SELECT_SINGLE)
        xfer.add_component(grid)
        xfer.actions = []
    if (Params.getvalue("member-subscription-mode") in (Subscription.MODE_WITHMODERATE, Subscription.MODE_AUTOMATIQUE)) and (Subscription.objects.filter(Q(adherent_id=current_contact.id) & Q(season=Season.current_season())).count() == 0):
        xfer.new_tab(_('002@Subscription'))
        row = xfer.get_max_row() + 1
        btn = XferCompButton('btnnewsubscript')
        btn.set_location(1, row)
        btn.set_action(xfer.request, SubscriptionAddForCurrent.get_action(_('Subscription'), 'diacamma.member/images/adherent.png'), close=CLOSE_NO)
        xfer.add_component(btn)


def _add_subscription(xfer, contact_filter, before):
    season = Season.current_season()
    if xfer.getparam("dateref") is None:
        season = Season.get_from_date(convert_date(xfer.getparam("dateref", ""), season.date_ref))
    subscriptions = Subscription.objects.filter(Q(season=season) & contact_filter)
    if len(subscriptions) > 0:
        if before:
            xfer.new_tab(_('002@Subscription'), num=1)
        else:
            xfer.new_tab(_('002@Subscription'))
        row = xfer.get_max_row() + 1
        grid = XferCompGrid('subscription')
        grid.set_model(subscriptions, Subscription.get_other_fields(), xfer)
        grid.set_location(0, row + 1, 2)
        grid.add_action_notified(xfer, model=Subscription)
        grid.set_size(350, 500)
        xfer.add_component(grid)


@signal_and_lock.Signal.decorate('show_contact')
def shoxcontact_member(item, xfer):
    if isinstance(item, LegalEntity):
        contact_filter = Q(adherent__responsability__legal_entity=item)
        _add_subscription(xfer, contact_filter, xfer.getparam('SubscriptionBefore') == 'YES')


@signal_and_lock.Signal.decorate('third_addon')
def thirdaddon_member(item, xfer):
    if WrapAction.is_permission(xfer.request, 'member.change_subscription'):
        contact = item.contact.get_final_child()
        contact_filter = None
        if isinstance(contact, LegalEntity):
            contact_filter = Q(adherent__responsability__legal_entity=contact)
        if isinstance(contact, Adherent):
            contact_filter = Q(adherent=contact)
        if contact_filter is None:
            return
        _add_subscription(xfer, contact_filter, False)
