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
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor, TITLE_DELETE, TITLE_MODIFY, TITLE_ADD, TITLE_EDIT, TITLE_CREATE
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage, SELECT_SINGLE, FORMTYPE_REFRESH, CLOSE_NO, SELECT_MULTI, CLOSE_YES, FORMTYPE_MODAL
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.xfercomponents import XferCompSelect, XferCompButton
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.CORE.parameters import Params

from diacamma.member.models import Season, Period, SubscriptionType, Document
from diacamma.member.views_conf import CategoryParamEdit

MenuManage.add_sub("member.conf", "core.extensions", short_icon='mdi:mdi-human-queue', caption=_("Member"), pos=5)


@MenuManage.describ('member.change_season', FORMTYPE_NOMODAL, 'member.conf', _('Management of seasons and subscriptions'))
class SeasonSubscription(XferListEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Season
    field_id = 'season'
    caption = _("Seasons and subscriptions")

    def fillresponse_header(self):
        self.new_tab(_('Season'))
        show_filter = self.getparam('show_filter', 0)
        edt = XferCompSelect("show_filter")
        edt.set_select([(0, _('Near active')), (1, _('All'))])
        edt.set_value(show_filter)
        edt.set_location(0, 3)
        edt.description = _('Show season')
        edt.set_action(self.request, self.return_action(),
                       modal=FORMTYPE_REFRESH, close=CLOSE_NO)
        self.add_component(edt)
        self.filter = Q()
        if show_filter == 0:
            try:
                year_ref = Season.current_season().reference_year
                designation_begin = "%d/%d" % (year_ref - 2, year_ref - 1)
                designation_end = "%d/%d" % (year_ref + 2, year_ref + 3)
                self.filter = Q(designation__gte=designation_begin) & Q(
                    designation__lte=designation_end)
            except Exception:
                pass

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.new_tab(_('Subscriptions'))
        row_max = self.get_max_row()
        self.fill_grid(row_max, SubscriptionType, "subscriptiontype", SubscriptionType.objects.all())
        self.get_components('subscriptiontype').colspan = 3
        btn = XferCompButton('reloadBill')
        btn.set_location(0, row_max + 5)
        btn.set_action(self.request, SubscriptionReloadBill.get_action(_('Regenerate'), short_icon='mdi:mdi-invoice-edit-outline'), modal=FORMTYPE_MODAL, close=CLOSE_NO)
        self.add_component(btn)
        if SubscriptionType.objects.filter(duration=SubscriptionType.DURATION_CALENDAR).count() > 0:
            param_lists = ['member-subscription-delaytorenew']
            Params.fill(self, param_lists, 1, self.get_max_row() + 1, nb_col=1)
            btn = XferCompButton('editparam')
            btn.set_is_mini(True)
            btn.set_location(2, self.get_max_row())
            btn.set_action(self.request, CategoryParamEdit.get_action(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline'),
                           close=CLOSE_NO, params={'params': param_lists, 'nb_col': 1})
            self.add_component(btn)


@ActionsManage.affect_grid(_("Active"), short_icon='mdi:mdi-check', unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class SeasonActive(XferContainerAcknowledge):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Season
    field_id = 'season'
    caption = _("Activate")

    def fillresponse(self):
        self.item.set_has_actif()


@ActionsManage.affect_grid(TITLE_CREATE, short_icon='mdi:mdi-pencil-plus')
@MenuManage.describ('member.add_season')
class SeasonAddModify(XferAddEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Season
    field_id = 'season'
    caption_add = _("Add season")
    caption_modify = _("Modify season")


@ActionsManage.affect_grid(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.change_season')
class SeasonShow(XferShowEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Season
    field_id = 'season'
    caption = _("Show season")


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class DocummentAddModify(XferAddEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Document
    field_id = 'document'
    caption_add = _("Add document")
    caption_modify = _("Modify document")


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('member.add_season')
class DocummentDel(XferDelete):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Document
    field_id = 'document'
    caption = _("Delete document")


@ActionsManage.affect_grid(_('Import doc.'), short_icon='mdi:mdi-content-copy', unique=SELECT_SINGLE, close=CLOSE_NO)
@MenuManage.describ('member.add_season')
class SeasonDocummentClone(XferContainerAcknowledge):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Season
    field_id = 'season'
    caption = _("Clone document")

    def fillresponse(self):
        self.item.clone_doc_need()


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class PeriodAddModify(XferAddEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Period
    field_id = 'period'
    caption_add = _("Add period")
    caption_modify = _("Modify period")


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('member.add_season')
class PeriodDel(XferDelete):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = Period
    field_id = 'period'
    caption = _("Delete period")


@ActionsManage.affect_grid(TITLE_ADD, short_icon='mdi:mdi-pencil-plus-outline')
@ActionsManage.affect_grid(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', unique=SELECT_SINGLE)
@ActionsManage.affect_show(TITLE_MODIFY, short_icon='mdi:mdi-pencil-outline', close=CLOSE_YES)
@MenuManage.describ('member.add_subscription')
class SubscriptionTypeAddModify(XferAddEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption_add = _("Add subscription")
    caption_modify = _("Modify subscription")


@ActionsManage.affect_grid(TITLE_EDIT, short_icon='mdi:mdi-text-box-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.change_subscription')
class SubscriptionTypeShow(XferShowEditor):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Show subscription")


@ActionsManage.affect_grid(TITLE_DELETE, short_icon='mdi:mdi-delete-outline', unique=SELECT_MULTI)
@MenuManage.describ('member.delete_subscription')
class SubscriptionTypeDel(XferDelete):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Delete subscription")


@ActionsManage.affect_grid(_('Up'), short_icon='mdi:mdi-arrow-up-bold-outline', unique=SELECT_SINGLE)
@MenuManage.describ('member.add_subscription')
class SubscriptionTypeUp(XferContainerAcknowledge):
    short_icon = "mdi:mdi-calendar-month-outline"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Up subscription")

    def fillresponse(self):
        self.item.up_order()


@MenuManage.describ('member.add_subscription')
class SubscriptionReloadBill(XferContainerAcknowledge):
    short_icon = 'mdi:mdi-invoice-edit-outline'
    caption = _("Quotation regeneration")

    def run_regenerate(self):
        from diacamma.member.models import Subscription
        nb_subscriptions = 0
        for sub in Subscription.objects.filter(season=self.season, status=Subscription.STATUS_BUILDING):
            sub.change_bill()
            nb_subscriptions += 1
        return nb_subscriptions

    def fillresponse(self, nb_quotations=None):
        from diacamma.accounting.models import FiscalYear
        self.season = Season.current_season()
        if FiscalYear.get_current() != FiscalYear.get_current(self.season.date_ref):
            raise LucteriosException(IMPORTANT, _('Active fiscal year different of current season !'))
        if self.confirme(_('Do you want regenerate quotations of building subscriptions ?')):
            if self.traitment(self.icon, _('Please, waiting a minutes ...'), ''):
                self.traitment_data[2] = _('%s subscriptions were regenerated.') % self.run_regenerate()
