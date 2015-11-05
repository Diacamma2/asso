# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage,\
    SELECT_SINGLE, FORMTYPE_REFRESH, CLOSE_NO, WrapAction, SELECT_NONE
from lucterios.framework.xfergraphic import XferContainerAcknowledge,\
    XferContainerCustom
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompSelect,\
    XferCompImage, XferCompGrid, XferCompEdit

from diacamma.member.models import Season, Period, Subscription


@MenuManage.describ('member.change_season', FORMTYPE_NOMODAL, 'contact.conf', _('Management of seasons and subscriptions'))
class MemberConf(XferListEditor):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Seasons and subscriptions")

    def fillresponse_header(self):
        self.action_grid.append(
            ('active', _("Active"), "images/ok.png", SELECT_SINGLE))
        self.new_tab(_('Season'))
        show_filter = self.getparam('show_filter', 0)
        lbl = XferCompLabelForm('lbl_showing')
        lbl.set_value_as_name(_('Show season'))
        lbl.set_location(0, 3)
        self.add_component(lbl)
        edt = XferCompSelect("show_filter")
        edt.set_select([(0, _('Near active')), (1, _('All'))])
        edt.set_value(show_filter)
        edt.set_location(1, 3)
        edt.set_action(self.request, self.get_action(),
                       {'modal': FORMTYPE_REFRESH, 'close': CLOSE_NO})
        self.add_component(edt)
        self.filter = Q()
        if show_filter == 0:
            try:
                active_season = Season.objects.get(iscurrent=True)
                year_init = int(active_season.designation[:4])
                designation_begin = "%d/%d" % (year_init - 2, year_init - 1)
                designation_end = "%d/%d" % (year_init + 2, year_init + 3)
                self.filter = Q(designation__gte=designation_begin) & Q(
                    designation__lte=designation_end)
            except:
                pass

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.new_tab(_('Subscriptions'))
        self.fill_grid(
            self.get_max_row(), Subscription, "subscription", Subscription.objects.all())


@ActionsManage.affect('Season', 'active')
@MenuManage.describ('member.change_season')
class SeasonActive(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Activate")

    def fillresponse(self):
        self.item.set_has_actif()


@ActionsManage.affect('Season', 'add')
@MenuManage.describ('member.add_season')
class SeasonAddModify(XferAddEditor):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption_add = _("Add season")
    caption_modify = _("Modify season")


@ActionsManage.affect('Season', 'show')
@MenuManage.describ('member.change_season')
class SeasonShow(XferShowEditor):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Show season")

    def fillresponse(self):
        XferShowEditor.fillresponse(self)
        self.add_action(SeasonDocummentClone.get_action(
            _('Import doc.'), 'images/ok.png'), {'close': CLOSE_NO}, 0)


@ActionsManage.affect('Season', 'documentaddmodify')
@MenuManage.describ('member.change_season')
class SeasonDocummentAddModify(XferContainerCustom):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Edit document")
    readonly = True

    def fillresponse(self, doc_need_id=0):
        img = XferCompImage('img')
        img.set_value(self.icon_path())
        img.set_location(0, 0, 1, 6)
        self.add_component(img)
        lbl = XferCompLabelForm('lbl_name')
        lbl.set_value_as_name(_('name'))
        lbl.set_location(1, 0)
        self.add_component(lbl)
        edt = XferCompEdit("name")
        if doc_need_id > 0:
            edt.set_value(self.item.get_doc_need(doc_need_id))
        edt.set_location(1, 1)
        self.add_component(edt)
        self.add_action(
            SeasonDocummentSave.get_action(_('Ok'), 'images/ok.png'), {})
        self.add_action(WrapAction(_('Close'), 'images/close.png'), {})


@MenuManage.describ('member.change_season')
class SeasonDocummentSave(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Edit document")
    readonly = True

    def fillresponse(self, doc_need_id=0, name=""):
        self.item.set_doc_need(doc_need_id, name)


@ActionsManage.affect('Season', 'documentdel')
@MenuManage.describ('member.change_season')
class SeasonDocummentDel(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Delete document")
    readonly = True

    def fillresponse(self, doc_need_id=0):
        if self.confirme(_("Do you want to delete this document?")):
            self.item.del_doc_need(doc_need_id)


@ActionsManage.affect('Season', 'documentclone')
@MenuManage.describ('member.change_season')
class SeasonDocummentClone(XferContainerAcknowledge):
    icon = "season.png"
    model = Season
    field_id = 'season'
    caption = _("Clone document")

    def fillresponse(self, doc_need_id=0):
        self.item.clone_doc_need()


@ActionsManage.affect('Period', 'edit', 'modify', 'add')
@MenuManage.describ('member.add_season')
class PeriodAddModify(XferAddEditor):
    icon = "season.png"
    model = Period
    field_id = 'period'
    caption_add = _("Add period")
    caption_modify = _("Modify period")


@ActionsManage.affect('Period', 'delete')
@MenuManage.describ('member.add_season')
class PeriodDel(XferDelete):
    icon = "season.png"
    model = Period
    field_id = 'period'
    caption = _("Delete period")


@ActionsManage.affect('Subscription', 'edit', 'modify', 'add')
@MenuManage.describ('member.add_subscription')
class SubscriptionAddModify(XferAddEditor):
    icon = "season.png"
    model = Subscription
    field_id = 'subscription'
    caption_add = _("Add subscription")
    caption_modify = _("Modify subscription")


@ActionsManage.affect('Subscription', 'show')
@MenuManage.describ('member.change_subscription')
class SubscriptionShow(XferShowEditor):
    icon = "season.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show subscription")


@ActionsManage.affect('Subscription', 'delete')
@MenuManage.describ('member.delete_subscription')
class SubscriptionDel(XferDelete):
    icon = "season.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Delete subscription")
