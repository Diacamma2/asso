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

from lucterios.framework.xferadvance import XferListEditor
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
    XferCompImage, XferCompEdit, XferCompGrid, DEFAULT_ACTION_LIST
from lucterios.framework.xfergraphic import XferContainerAcknowledge, \
    XferContainerCustom
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework import signal_and_lock

from lucterios.CORE.parameters import Params
from lucterios.framework.tools import convert_date, same_day_months_after

from diacamma.member.models import Adherent, Subscription, Season, Age, Team, Activity, License, DocAdherent, \
    SubscriptionType


MenuManage.add_sub(
    "association", None, "diacamma.member/images/association.png", _("Association"), _("Association tools"), 30)

MenuManage.add_sub("member.actions", "association", "diacamma.member/images/member.png",
                   _("Adherents"), _("Management of adherents and subscriptions."), 50)


class AdherentAbstractList(XferListEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    is_renew = False

    def fillresponse_header(self):
        row = self.get_max_row() + 1
        team = self.getparam("team", ())
        activity = self.getparam("activity", ())
        genre = self.getparam("genre", 0)
        age = self.getparam("age", ())
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

        btn = XferCompButton('btndateref')
        btn.set_location(8, row + 1)
        btn.set_action(self.request, self.get_action(_('Refresh'), ''),
                       {'modal': FORMTYPE_REFRESH, 'close': CLOSE_NO})
        self.add_component(btn)

    def get_items_from_filter(self):
        team = self.getparam("team", ())
        activity = self.getparam("activity", ())
        genre = self.getparam("genre", 0)
        age = self.getparam("age", ())
        dateref = convert_date(
            self.getparam("dateref", ""), Season.current_season().date_ref)
        if self.is_renew:
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
        items = self.model.objects.filter(
            current_filter).exclude(exclude_filter)
        return items


class AdherentSelection(AdherentAbstractList):
    caption = _("Select adherent")
    mode_select = SELECT_SINGLE
    select_class = None
    final_class = None

    def fillresponse(self):
        self.action_list = []
        if self.final_class is not None:
            self.add_action(
                self.final_class.get_action(_('ok'), "images/ok.png"), {})
        AdherentAbstractList.fillresponse(self)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10
        if self.select_class is not None:
            grid = self.get_components(self.field_id)
            grid.add_action(self.request, self.select_class.get_action(_("Select"), "images/ok.png"), {
                            'close': CLOSE_YES, 'unique': self.mode_select}, 0)


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with subscribtion'))
class AdherentActiveList(AdherentAbstractList):
    caption = _("Subscribe adherents")
    is_renew = False

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.item.editor.add_email_selector(
            self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10
        if Params.getvalue("member-licence-enabled"):
            self.get_components(self.field_id).add_action(self.request, AdherentLicense.get_action(
                _("License"), ""), {"unique": SELECT_SINGLE, "close": CLOSE_NO})


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('To find an adherent following a set of criteria.'))
class AdherentSearch(XferSearchEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Search adherent")


@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with old subscribtion not renew yet'))
class AdherentRenewList(AdherentAbstractList):
    caption = _("Adherents to renew")
    is_renew = True

    def fillresponse_header(self):
        AdherentAbstractList.fillresponse_header(self)
        self.action_grid = [DEFAULT_ACTION_LIST[0]]
        self.action_grid.append(
            ('renew', _("re-new"), "images/add.png", SELECT_MULTI))
        self.fieldnames = Adherent.get_renew_fields()

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.item.editor.add_email_selector(
            self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10


@ActionsManage.affect('Adherent', 'modify', 'add')
@MenuManage.describ('contacts.add_abstractcontact')
class AdherentAddModify(XferAddEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption_add = _("Add adherent")
    caption_modify = _("Modify adherent")


@ActionsManage.affect('Adherent', 'show')
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
        self.item = self.item.current_subscription()
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
        self.add_action(
            AdherentLicenseSave.get_action(_('Ok'), 'images/ok.png'), {})
        self.add_action(WrapAction(_('Cancel'), 'images/cancel.png'), {})


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


@ActionsManage.affect('Adherent', 'renew')
@MenuManage.describ('member.add_subscription')
class AdherentRenew(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("License")

    def fillresponse(self):
        text = _(
            "{[b]}Do you want that those %d old selected adherent(s) has been renew?{[/b]}{[br/]}Same subscription(s) will be applicated.{[br/]}No validated bill will be created for each subscritpion.") % len(self.items)
        if self.confirme(text):
            dateref = convert_date(
                self.getparam("dateref", ""), Season.current_season().date_ref)
            for item in self.items:
                item.renew(dateref)


@ActionsManage.affect('Adherent', 'delete')
@MenuManage.describ('contacts.delete_abstractcontact')
class AdherentDel(XferDelete):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Delete adherent")


@ActionsManage.affect('Adherent', 'doc')
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


@ActionsManage.affect('Adherent', 'print')
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentPrint(XferPrintAction):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Print adherent")
    action_class = AdherentShow


@ActionsManage.affect('Adherent', 'label')
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentLabel(XferPrintLabel):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Label adherent")


@ActionsManage.affect('Adherent', 'listing')
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentListing(XferPrintListing):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Listing adherent")


@ActionsManage.affect('Subscription', 'modify', 'add')
@MenuManage.describ('member.add_subscription')
class SubscriptionAddModify(XferAddEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption_add = _("Add subscription")
    caption_modify = _("Modify subscription")
    redirect_to_show = 'bill'


@ActionsManage.affect('Subscription', 'show')
@MenuManage.describ('member.change_subscription')
class SubscriptionShow(XferShowEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show subscription")

    def fillresponse(self):
        XferShowEditor.fillresponse(self)
        self.add_action(ActionsManage.get_act_changed(
            'Subscription', 'bill', _('Bill'), 'images/ok.png'), {'close': CLOSE_NO}, 0)


@ActionsManage.affect('Subscription', 'delete')
@MenuManage.describ('member.delete_subscription')
class SubscriptionDel(XferDelete):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Delete subscription")


@ActionsManage.affect('Subscription', 'bill')
@MenuManage.describ('invoice.change_bill')
class SubscriptionShowBill(XferContainerAcknowledge):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show bill of subscription")

    def fillresponse(self):
        if self.item.bill_id is not None:
            self.redirect_action(ActionsManage.get_act_changed(
                'Bill', 'show', '', ''), {'close': CLOSE_NO, 'params': {'bill': self.item.bill_id}})


@ActionsManage.affect('License', 'edit', 'add')
@MenuManage.describ('member.add_subscription')
class LicenseAddModify(XferAddEditor):
    icon = "adherent.png"
    model = License
    field_id = 'license'
    caption_add = _("Add license")
    caption_modify = _("Modify license")


@ActionsManage.affect('License', 'delete')
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
        sel.set_action(
            self.request, self.get_action('', ''), {'modal': FORMTYPE_REFRESH, 'close': CLOSE_NO})
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
        self.add_action(AdherentStatisticPrint.get_action(
            _("Print"), "images/print.png"), {'close': CLOSE_NO, 'params': {'classname': self.__class__.__name__}})
        self.add_action(WrapAction(_('Close'), 'images/close.png'), {})


@MenuManage.describ('member.change_adherent')
class AdherentStatisticPrint(XferPrintAction):
    icon = "statistic.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Statistic")
    action_class = AdherentStatistic
    with_text_export = True


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
                subscription__end_date__gte=dateref)))
            lab = XferCompLabelForm('membernb')
            lab.set_value_as_header(_("Active adherents: %d") % nb_adh)
            lab.set_location(0, row + 2, 4)
            xfer.add_component(lab)
        except LucteriosException as lerr:
            lbl = XferCompLabelForm("member_error")
            lbl.set_value_center(six.text_type(lerr))
            lbl.set_location(0, row + 1, 4)
            xfer.add_component(lbl)
    if is_right or (current_adherent is not None):
        lab = XferCompLabelForm('member')
        lab.set_value_as_infocenter("{[hr/]}")
        lab.set_location(0, row + 3, 4)
        xfer.add_component(lab)
        return True
    else:
        return False
