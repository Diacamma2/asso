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
from django.db.models import Q

from lucterios.framework.xferadvance import XferListEditor
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferShowEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.xfersearch import XferSearchEditor
from lucterios.CORE.xferprint import XferPrintAction
from lucterios.CORE.xferprint import XferPrintLabel
from lucterios.CORE.xferprint import XferPrintListing
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage,\
    FORMTYPE_REFRESH, CLOSE_NO
from lucterios.framework.xfercomponents import XferCompLabelForm,\
    XferCompCheckList, XferCompButton, XferCompSelect, XferCompDate

from diacamma.member.models import Adherent, Subscription, Season, Age, Team,\
    Activity, License, DocAdherent
from datetime import datetime
from builtins import ValueError
from lucterios.framework.xfergraphic import XferContainerAcknowledge
from lucterios.CORE.parameters import Params

MenuManage.add_sub(
    "association", None, "diacamma.member/images/association.png", _("Association"), _("Association tools"), 30)

MenuManage.add_sub("member.actions", "association", "diacamma.member/images/member.png",
                   _("Adherents"), _("Management of adherents and subscriptions."), 50)


def _add_adherent_filter(xfer):
    row = xfer.get_max_row() + 1
    team = xfer.getparam("team", ())
    activity = xfer.getparam("activity", ())
    genre = xfer.getparam("genre", 0)
    age = xfer.getparam("age", ())
    dateref = xfer.getparam("dateref", "")

    try:
        dateref = datetime.strptime(dateref, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        current_season = Season.current_season()
        dateref = current_season.date_ref

    lbl = XferCompLabelForm('lblage')
    lbl.set_value_as_name(_("Age"))
    lbl.set_location(0, row)
    xfer.add_component(lbl)
    sel = XferCompCheckList('age')
    sel.set_select_query(Age.objects.all())
    sel.set_value(age)
    sel.set_location(1, row, 1, 2)
    xfer.add_component(sel)

    lbl = XferCompLabelForm('lblteam')
    lbl.set_value_as_name(Params.getvalue("member-team-text"))
    lbl.set_location(2, row)
    xfer.add_component(lbl)
    sel = XferCompCheckList('team')
    sel.set_select_query(Team.objects.all())
    sel.set_value(team)
    sel.set_location(3, row, 1, 2)
    xfer.add_component(sel)

    lbl = XferCompLabelForm('lblactivity')
    lbl.set_value_as_name(Params.getvalue("member-activite-text"))
    lbl.set_location(4, row)
    xfer.add_component(lbl)
    sel = XferCompCheckList('activity')
    sel.set_select_query(Activity.objects.all())
    sel.set_value(activity)
    sel.set_location(5, row, 1, 2)
    xfer.add_component(sel)

    lbl = XferCompLabelForm('lbldateref')
    lbl.set_value_as_name(_("reference date"))
    lbl.set_location(6, row)
    xfer.add_component(lbl)

    dtref = XferCompDate('dateref')
    dtref.set_value(dateref)
    dtref.set_needed(True)
    dtref.set_location(7, row, 2)
    xfer.add_component(dtref)

    lbl = XferCompLabelForm('lblgenre')
    lbl.set_value_as_name(_("genre"))
    lbl.set_location(6, row + 1)
    xfer.add_component(lbl)

    sel = XferCompSelect('genre')
    list_genre = list(xfer.item.get_field_by_name('genre').choices)
    list_genre.insert(0, (0, '---'))
    sel.set_select(list_genre)
    sel.set_location(7, row + 1)
    sel.set_value(genre)
    xfer.add_component(sel)

    btn = XferCompButton('btndateref')
    btn.set_location(8, row + 1)
    btn.set_action(xfer.request, xfer.get_action(_('refresh'), ''),
                   {'modal': FORMTYPE_REFRESH, 'close': CLOSE_NO})
    xfer.add_component(btn)

    current_filter = Q(subscription__begin_date__lte=dateref) & Q(
        subscription__end_date__gte=dateref)
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
    return current_filter


@ActionsManage.affect('Adherent', 'list')
@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('List of adherents with subscribtion'))
class AdherentList(XferListEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Subscribe adherents")

    def fillresponse_header(self):
        self.filter = _add_adherent_filter(self)

    def fillresponse(self):
        XferListEditor.fillresponse(self)
        self.item.editor.add_email_selector(
            self, 0, self.get_max_row() + 1, 10)
        self.get_components('title').colspan = 10
        self.get_components(self.field_id).colspan = 10
        self.get_components('nb_adherent').colspan = 10


@ActionsManage.affect('Adherent', 'search')
@MenuManage.describ('member.change_adherent', FORMTYPE_NOMODAL, 'member.actions', _('To find an adherent following a set of criteria.'))
class AdherentSearch(XferSearchEditor):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Search adherent")


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


@ActionsManage.affect('Adherent', 'label')
@MenuManage.describ('contacts.change_abstractcontact')
class AdherentLabel(XferPrintLabel):
    icon = "adherent.png"
    model = Adherent
    field_id = 'adherent'
    caption = _("Label adherent")


@ActionsManage.affect('Adherent', 'listing')
@MenuManage.describ('member.change_adherent')
@MenuManage.describ('contacts.add_abstractcontact')
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


@ActionsManage.affect('Subscription', 'show')
@MenuManage.describ('member.change_subscription')
class SubscriptionShow(XferShowEditor):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Show subscription")


@ActionsManage.affect('Subscription', 'delete')
@MenuManage.describ('member.delete_subscription')
class SubscriptionDel(XferDelete):
    icon = "adherent.png"
    model = Subscription
    field_id = 'subscription'
    caption = _("Delete subscription")


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
