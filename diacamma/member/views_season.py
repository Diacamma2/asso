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

from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor, TITLE_DELETE, TITLE_MODIFY, TITLE_ADD, TITLE_EDIT, TITLE_CREATE
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage, SELECT_SINGLE, FORMTYPE_REFRESH, CLOSE_NO, SELECT_MULTI, CLOSE_YES, FORMTYPE_MODAL
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.framework.xfercomponents import XferCompSelect, XferCompButton
from lucterios.framework.error import LucteriosException, IMPORTANT

from diacamma.member.models import Season, Period, SubscriptionType, Document

MenuManage.add_sub("member.conf", "core.extensions", "", _("Member"), "", 5)


@MenuManage.describ('member.change_season', FORMTYPE_NOMODAL, 'member.conf', _('Management of seasons and subscriptions'))
class SeasonSubscription(XferListEditor):
    icon = "season.png"
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
        btn = XferCompButton('reloadBill')
        btn.set_location(0, row_max + 5, 2)
        btn.set_action(self.request, SubscriptionReloadBill.get_action(_('Regenerate'), "/static/diacamma.invoice/images/bill.png"), modal=FORMTYPE_MODAL, close=CLOSE_NO)
        self.add_component(btn)


@ActionsManage.affect_grid(_("Active"), "images/ok.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class SeasonActive(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Activate")

    def fillresponse(self):
        self.item.set_has_actif()


@ActionsManage.affect_grid(TITLE_CREATE, "images/new.png")
@MenuManage.describ('member.add_season')
class SeasonAddModify(XferAddEditor):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption_add = _("Add season")
    caption_modify = _("Modify season")


@ActionsManage.affect_grid(TITLE_EDIT, "images/show.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.change_season')
class SeasonShow(XferShowEditor):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Show season")


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class DocummentAddModify(XferAddEditor):
    icon = "season.png"
    model = Document
    field_id = 'document'
    caption_add = _("Add document")
    caption_modify = _("Modify document")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.add_season')
class DocummentDel(XferDelete):
    icon = "season.png"
    model = Document
    field_id = 'document'
    caption = _("Delete document")


@ActionsManage.affect_grid(_('Import doc.'), "images/clone.png", unique=SELECT_SINGLE, close=CLOSE_NO)
@MenuManage.describ('member.add_season')
class SeasonDocummentClone(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Clone document")

    def fillresponse(self):
        self.item.clone_doc_need()


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.add_season')
class PeriodAddModify(XferAddEditor):
    icon = "season.png"
    model = Period
    field_id = 'period'
    caption_add = _("Add period")
    caption_modify = _("Modify period")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.add_season')
class PeriodDel(XferDelete):
    icon = "season.png"
    model = Period
    field_id = 'period'
    caption = _("Delete period")


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@ActionsManage.affect_show(TITLE_MODIFY, "images/edit.png", close=CLOSE_YES)
@MenuManage.describ('member.add_subscription')
class SubscriptionTypeAddModify(XferAddEditor):
    icon = "season.png"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption_add = _("Add subscription")
    caption_modify = _("Modify subscription")


@ActionsManage.affect_grid(TITLE_EDIT, "images/show.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.change_subscription')
class SubscriptionTypeShow(XferShowEditor):
    icon = "season.png"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Show subscription")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('member.delete_subscription')
class SubscriptionTypeDel(XferDelete):
    icon = "season.png"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Delete subscription")


@ActionsManage.affect_grid(_('Up'), "images/up.png", unique=SELECT_SINGLE)
@MenuManage.describ('member.add_subscription')
class SubscriptionTypeUp(XferContainerAcknowledge):
    icon = "season.png"
    model = SubscriptionType
    field_id = 'subscriptiontype'
    caption = _("Up subscription")

    def fillresponse(self):
        self.item.up_order()


@MenuManage.describ('member.add_subscription')
class SubscriptionReloadBill(XferContainerAcknowledge):
    icon = "/static/diacamma.invoice/images/bill.png"
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
