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
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Concat
from django.db.models import Q, Value
from django.conf import settings
from django.utils import timezone

from lucterios.framework.xferadvance import XferAddEditor, XferListEditor, TITLE_MODIFY, TITLE_DELETE, TITLE_ADD, TITLE_EDIT, XferShowEditor, TITLE_CLONE
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import ActionsManage, MenuManage, FORMTYPE_NOMODAL, CLOSE_NO, SELECT_MULTI, SELECT_SINGLE, WrapAction, FORMTYPE_REFRESH, FORMTYPE_MODAL
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.models import LucteriosQuerySet
from lucterios.framework.xfercomponents import XferCompButton, XferCompLabelForm, XferCompCheckList, XferCompFloat, XferCompSelect
from lucterios.framework import signal_and_lock
from lucterios.framework.xfergraphic import XferContainerAcknowledge, XFER_DBOX_WARNING
from lucterios.CORE.parameters import Params
from lucterios.CORE.views import ParamEdit, ObjectMerge

from diacamma.member.models import Activity, Age, Team, Season, SubscriptionType, Adherent, TaxReceipt, \
    Subscription
from diacamma.payoff.views import SupportingPrint, can_send_email


@signal_and_lock.Signal.decorate('config')
def config_member(setting_list):
    setting_list['20@%s' % _("Adherents")] = ["member-family-type", "member-connection", "member-subscription-mode",
                                              "member-size-page", "member-default-categorybill",
                                              "member-tax-receipt", "member-tax-receipt-payoff",
                                              "member-tax-exclude-payoff", "member-tax-reason-payoff",
                                              "member-activegroup", "member-renew-filter"]
    return True


def fill_params(xfer, param_lists=None, smallbtn=False):
    if param_lists is None:
        param_lists = ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable",
                       "member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-age-statistic",
                       "member-subscription-message", "member-fields"]
    if len(param_lists) >= 3:
        nb_col = 2
    else:
        nb_col = 1
    Params.fill(xfer, param_lists, 1, xfer.get_max_row() + 1, nb_col=nb_col)

    comp_fields = xfer.get_components("member-fields")
    if comp_fields is not None:
        comp_fields.value = "{[br/]}".join([str(fields_title[1]) for fields_title in Adherent.get_default_fields_title()])

    btn = XferCompButton('editparam')
    btn.set_is_mini(smallbtn)
    btn.set_location(3, xfer.get_max_row() + 1)
    btn.set_action(xfer.request, CategoryParamEdit.get_action(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline'),
                   close=CLOSE_NO, params={'params': param_lists, 'nb_col': nb_col})
    xfer.add_component(btn)


@MenuManage.describ('CORE.add_parameter')
class CategoryParamEdit(ParamEdit):

    def fillresponse(self, params=(), nb_col=1):
        ParamEdit.fillresponse(self, params=params, nb_col=nb_col)
        comp_fields = self.get_components("member-fields")
        if comp_fields is not None:
            self.remove_component("member-fields")
            new_comp_fields = XferCompCheckList("member-fields")
            new_comp_fields.description = comp_fields.description
            new_comp_fields.simple = 2
            new_comp_fields.set_location(comp_fields.col, comp_fields.row, comp_fields.colspan, comp_fields.rowspan)
            new_comp_fields.set_select(Adherent.get_allowed_fields_title())
            new_comp_fields.set_value([field[1] if isinstance(field, tuple) else field for field in Adherent.get_default_fields()])
            self.add_component(new_comp_fields)


@MenuManage.describ('CORE.change_parameter', FORMTYPE_MODAL, 'member.conf', _('Management of member categories'))
class CategoryConf(XferListEditor):
    short_icon = "mdi:mdi-account-settings"
    caption = _("Categories")

    def fillresponse_header(self):
        self.new_tab(_('Parameters'))
        fill_params(self)

    def fillresponse_body(self):
        if Params.getvalue("member-age-enable") == 1:
            self.new_tab(_('Age'))
            self.fill_grid(0, Age, "age", Age.objects.all())
        if Params.getvalue("member-team-enable") != 0:
            team_filter = self.getparam('team_filter', 0)
            self.new_tab(Params.getvalue("member-team-text"))
            check = XferCompSelect('team_filter')
            check.set_location(0, 1)
            check.set_select([(0, _('show only enabled team')), (1, _('show all teams')), (2, _('show only disabled team'))])
            check.set_value(team_filter)
            check.description = _('team filter')
            check.set_action(self.request, self.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
            self.add_component(check)
            if team_filter == 1:
                team_list = Team.objects.all()
            else:
                team_list = Team.objects.filter(unactive=(team_filter == 2))
            self.fill_grid(2, Team, "team", team_list)
            if team_filter != 1:
                grid = self.get_components('team')
                grid.delete_header('unactive')
        if Params.getvalue("member-activite-enable") == 1:
            self.new_tab(Params.getvalue("member-activite-text"))
            self.fill_grid(0, Activity, "activity", Activity.get_all(nofilter=True))
            grid = self.get_components("activity")
            if WrapAction.is_permission(self.request, 'CORE.add_parameter'):
                grid.add_action(self.request, ObjectMerge.get_action(_("Merge"), short_icon='mdi:mdi-content-copy'), close=CLOSE_NO, unique=SELECT_MULTI,
                                params={'modelname': 'member.Activity', 'field_id': 'activity'})
            if hasattr(settings, "DIACAMMA_MAXACTIVITY") and (getattr(settings, "DIACAMMA_MAXACTIVITY") <= grid.nb_lines):
                lbl = XferCompLabelForm("limit_activity")
                lbl.set_color('red')
                lbl.set_value_as_headername(_('You have the maximum of activities!'))
                lbl.set_location(grid.col, self.get_max_row() + 1)
                self.add_component(lbl)
                grid.delete_action("diacamma.member/activityAddModify", True)


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class AgeAddModify(XferAddEditor):
    short_icon = "mdi:mdi-account-settings"
    model = Age
    field_id = 'age'
    caption_add = _("Add age")
    caption_modify = _("Modify age")


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class AgeDel(XferDelete):
    short_icon = "mdi:mdi-account-settings"
    model = Age
    field_id = 'age'
    caption = _("Delete age")


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class TeamAddModify(XferAddEditor):
    short_icon = "mdi:mdi-account-settings"
    model = Team
    field_id = 'team'
    caption_add = _("Add team")
    caption_modify = _("Modify team")


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class TeamDel(XferDelete):
    short_icon = "mdi:mdi-account-settings"
    model = Team
    field_id = 'team'
    caption = _("Delete team")


@ActionsManage.affect_grid(TITLE_CLONE, short_icon='mdi:mdi-content-copy', unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class TeamClone(XferContainerAcknowledge):
    short_icon = "mdi:mdi-account-settings"
    model = Team
    field_id = 'team'
    caption_add = _("Add team")

    def fillresponse(self):
        self.item.clone()
        self.redirect_action(TeamAddModify.get_action(), params={self.field_id: self.item.id})


@ActionsManage.affect_grid(_("dis-en-abled"), short_icon="mdi:mdi-check", unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class TeamEnabled(XferContainerAcknowledge):
    short_icon = "mdi:mdi-account-settings"
    model = Team
    field_id = 'team'
    caption_add = _("Enabled team")

    def fillresponse(self):
        for item in self.items:
            item.unactive = not item.unactive
            item.save()


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class ActivityAddModify(XferAddEditor):
    short_icon = "mdi:mdi-account-settings"
    model = Activity
    redirect_to_show = None
    field_id = 'activity'
    caption_add = _("Add activity")
    caption_modify = _("Modify activity")

    def fillresponse(self):
        if (self.item.id is None) and hasattr(settings, "DIACAMMA_MAXACTIVITY"):
            nb_act = len(Activity.objects.all())
            if getattr(settings, "DIACAMMA_MAXACTIVITY") <= nb_act:
                raise LucteriosException(IMPORTANT, _('You have the maximum of activities!'))
        XferAddEditor.fillresponse(self)


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class ActivityDel(XferDelete):
    short_icon = "mdi:mdi-account-settings"
    model = Activity
    field_id = 'activity'
    caption = _("Delete activity")


@ActionsManage.affect_other(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline')
@MenuManage.describ('CORE.change_parameter')
class ActivityShow(XferShowEditor):
    short_icon = "mdi:mdi-account-settings"
    model = Activity
    field_id = 'activity'
    caption = _("Show activity")


@ActionsManage.affect_grid(_("dis-en-abled"), short_icon="mdi:mdi-check", unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class ActivityEnabled(XferContainerAcknowledge):
    short_icon = "mdi:mdi-account-settings"
    model = Activity
    field_id = 'activity'
    caption_add = _("Enabled activity")

    def fillresponse(self):
        cant_unactive_msg = self.item.can_delete()
        if cant_unactive_msg != '':
            raise LucteriosException(IMPORTANT, cant_unactive_msg)
        self.item.unactive = not self.item.unactive
        self.item.save()


def show_taxreceipt(request):
    if TaxReceiptShow.get_action().check_permission(request):
        return Params.getvalue("member-tax-receipt") != ""
    else:
        return False


@MenuManage.describ(show_taxreceipt, FORMTYPE_NOMODAL, 'financial', _('Management of tax receipts'))
class TaxReceiptList(XferListEditor):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Tax receipts")

    def get_items_from_filter(self):
        items = self.model.objects.select_related('third', 'third__contact', 'third__contact__individual', 'third__contact__legalentity').annotate(completename=Concat('third__contact__individual__lastname', Value(' '), 'third__contact__individual__firstname')).filter(self.filter).distinct()
        sort_third = self.getparam('GRID_ORDER%taxreceipt', '')
        sort_thirdbis = self.getparam('GRID_ORDER%taxreceipt+', '')
        self.params['GRID_ORDER%taxreceipt'] = ""
        if sort_third != '':
            if sort_thirdbis.startswith('-'):
                sort_thirdbis = "+"
            else:
                sort_thirdbis = "-"
            self.params['GRID_ORDER%taxreceipt+'] = sort_thirdbis
        items = sorted(items, key=lambda t: str(t.third).lower(), reverse=sort_thirdbis.startswith('-'))
        return LucteriosQuerySet(model=TaxReceipt, initial=items)

    def fillresponse_header(self):
        select_year = self.getparam('year', timezone.now().year)
        comp_year = XferCompFloat('year', minval=1900, maxval=2100, precval=0)
        comp_year.set_value(select_year)
        comp_year.set_location(1, 1)
        comp_year.set_action(self.request, self.return_action(), close=CLOSE_NO, modal=FORMTYPE_REFRESH)
        comp_year.description = _('year')
        self.add_component(comp_year)
        self.filter = Q(year=select_year)


@ActionsManage.affect_list(_('Valid'), short_icon="mdi:mdi-check")
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptValid(XferContainerAcknowledge):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Valid tax receipt")

    def fillresponse(self, year=0):
        if self.confirme(_('Do you want to validate tax receiptes for year "%s" ?{[br/]}{[u]}Warning:{[/u]} Tax receipts are not removable.') % year):
            TaxReceipt.valid_all(year)


@ActionsManage.affect_list(_('Check'), short_icon="mdi:mdi-refresh")
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptCheck(XferContainerAcknowledge):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Check tax receipt")

    def fillresponse(self, year=0):
        if self.confirme(_('Do you want to generate tax receiptes for year "%s" ?') % year):
            TaxReceipt.create_all(year)


@ActionsManage.affect_show(_('Check'), short_icon="mdi:mdi-refresh", condition=lambda xfer: xfer.item.num is None)
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptCheckOnlyOn(XferContainerAcknowledge):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Check tax receipt")

    def fillresponse(self):
        if self.confirme(_('Do you want to re-generate this tax receipte for year "%s" ?') % self.item.year):
            self.item.regenerate()


@ActionsManage.affect_grid(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptShow(XferShowEditor):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Show tax receipt")


@ActionsManage.affect_grid(_("Send"), short_icon="mdi:mdi-email-outline", close=CLOSE_NO, unique=SELECT_MULTI, condition=lambda xfer, gridname='': can_send_email(xfer))
@ActionsManage.affect_show(_("Send"), short_icon="mdi:mdi-email-outline", close=CLOSE_NO, condition=lambda xfer: (xfer.item.num is not None) and can_send_email(xfer))
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptEmail(XferContainerAcknowledge):
    caption = _("Send by email")
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'

    def fillresponse(self):
        if (hasattr(self.items, 'filter') and self.items.filter(num__isnull=True).count() > 0) or (isinstance(self.items, list) and (self.item.num is None)):
            self.message(_('Some tax receipts are not validated !'), XFER_DBOX_WARNING)
        else:
            self.redirect_action(ActionsManage.get_action_url('payoff.Supporting', 'Email', self),
                                 close=CLOSE_NO, params={'item_name': self.field_id, "modelname": ""})


@ActionsManage.affect_grid(_("Print"), short_icon="mdi:mdi-printer-outline", close=CLOSE_NO, unique=SELECT_MULTI)
@ActionsManage.affect_show(_("Print"), short_icon="mdi:mdi-printer-outline", close=CLOSE_NO)
@MenuManage.describ('member.change_taxreceipt')
class TaxReceiptPrint(SupportingPrint):
    short_icon = "mdi:mdi-receipt-text-outline"
    model = TaxReceipt
    field_id = 'taxreceipt'
    caption = _("Print tax receipt")

    def get_print_name(self):
        if len(self.items) == 1:
            current_taxreceipt = self.items[0]
            return current_taxreceipt.get_document_filename()
        else:
            return str(self.caption)

    def items_callback(self):
        return self.items

    def get_report_generator(self):
        report = SupportingPrint.get_report_generator(self)
        if (report is not None) and ((hasattr(self.items, 'filter') and self.items.filter(num__isnull=True).count() > 0) or (isinstance(self.items, list) and (self.item.num is None))):
            report.watermark = _('simulation')
        return report


@signal_and_lock.Signal.decorate('conf_wizard')
def conf_wizard_member(wizard_ident, xfer):
    if isinstance(wizard_ident, list) and (xfer is None):
        wizard_ident.append(("member_season", 11))
        wizard_ident.append(("member_subscriptiontype", 12))
        wizard_ident.append(("member_category", 13))
        wizard_ident.append(("member_params", 14))
    elif (xfer is not None) and (wizard_ident == "member_season"):
        xfer.add_title(_("Diacamma member"), _('Season'), _('Configuration of season'))
        xfer.fill_grid(5, Season, "season", Season.objects.all())
    elif (xfer is not None) and (wizard_ident == "member_subscriptiontype"):
        xfer.add_title(_("Diacamma member"), _('Subscriptions'), _('Configuration of subscription'))
        xfer.fill_grid(15, SubscriptionType, "subscriptiontype", SubscriptionType.objects.all())
        xfer.get_components("subscriptiontype").colspan = 6
        fill_params(xfer, ["member-subscription-mode", "member-connection",
                           "member-family-type", "member-tax-receipt",
                           "member-subscription-message"], True)
    elif (xfer is not None) and (wizard_ident == "member_category"):
        xfer.add_title(_("Diacamma member"), _("Categories"), _('Configuration of categories'))
        xfer.new_tab(_('Parameters'))
        fill_params(xfer, ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable"], True)
        if Params.getvalue("member-age-enable") == 1:
            xfer.new_tab(_('Age'))
            xfer.fill_grid(1, Age, "age", Age.objects.all())
        if Params.getvalue("member-team-enable") != 0:
            xfer.new_tab(Params.getvalue("member-team-text"))
            xfer.fill_grid(1, Team, "team", Team.objects.all())
        if Params.getvalue("member-activite-enable") == 1:
            xfer.new_tab(Params.getvalue("member-activite-text"))
            xfer.fill_grid(1, Activity, "activity", Activity.get_all())
            grid = xfer.get_components("activity")
            if hasattr(settings, "DIACAMMA_MAXACTIVITY") and (getattr(settings, "DIACAMMA_MAXACTIVITY") <= grid.nb_lines):
                lbl = XferCompLabelForm("limit_activity")
                lbl.set_color('red')
                lbl.set_value_as_headername(_('You have the maximum of activities!'))
                lbl.set_location(grid.col, xfer.get_max_row() + 1)
                xfer.add_component(lbl)
                grid.delete_action("diacamma.member/activityAddModify", True)
    elif (xfer is not None) and (wizard_ident == "member_params"):
        xfer.add_title(_("Diacamma member"), _('Parameters'), _('Configuration of main parameters'))
        fill_params(xfer, ["member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-fields"], True)


@signal_and_lock.Signal.decorate('auth_login')
def member_auth_login(user):
    activegroup = Params.getobject("member-activegroup")
    if not user.is_anonymous and (activegroup is not None):
        obj_adh = Adherent.objects.filter(user=user).first()
        if obj_adh is not None:
            if (obj_adh.current_subscription is None) or not (obj_adh.current_subscription.status in (Subscription.STATUS_BUILDING, Subscription.STATUS_VALID)):
                user.groups.remove(activegroup)
            else:
                user.groups.add(activegroup)
