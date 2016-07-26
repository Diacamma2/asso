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

from lucterios.framework.xferadvance import XferAddEditor, XferListEditor, TITLE_MODIFY, TITLE_DELETE, TITLE_ADD
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import ActionsManage, MenuManage, FORMTYPE_NOMODAL, CLOSE_NO, SELECT_MULTI, SELECT_SINGLE
from lucterios.framework.xfercomponents import XferCompButton
from lucterios.framework import signal_and_lock
from lucterios.CORE.parameters import Params
from lucterios.CORE.views import ParamEdit

from diacamma.member.models import Activity, Age, Team, Season, SubscriptionType


def fill_params(xfer, param_lists=None, smallbtn=False):
    if param_lists is None:
        param_lists = ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable",
                       "member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-connection", "member-subscription-mode", "member-subscription-message"]
    if len(param_lists) >= 3:
        nb_col = 2
    else:
        nb_col = 1
    Params.fill(xfer, param_lists, 1, xfer.get_max_row() + 1, nb_col=nb_col)
    btn = XferCompButton('editparam')
    btn.set_is_mini(smallbtn)
    btn.set_location(3, xfer.get_max_row() + 1)
    btn.set_action(xfer.request, ParamEdit.get_action(TITLE_MODIFY, 'images/edit.png'),
                   close=CLOSE_NO, params={'params': param_lists, 'nb_col': nb_col})
    xfer.add_component(btn)


@MenuManage.describ('CORE.change_parameter', FORMTYPE_NOMODAL, 'member.conf', _('Management of member categories'))
class CategoryConf(XferListEditor):
    icon = "config.png"
    caption = _("Categories")

    def fillresponse_header(self):
        self.new_tab(_('Parameters'))
        fill_params(self)

    def fillresponse_body(self):
        if Params.getvalue("member-age-enable") == 1:
            self.new_tab(_('Age'))
            self.fill_grid(0, Age, "age", Age.objects.all())
        if Params.getvalue("member-team-enable") == 1:
            self.new_tab(Params.getvalue("member-team-text"))
            self.fill_grid(0, Team, "team", Team.objects.all())
        if Params.getvalue("member-activite-enable") == 1:
            self.new_tab(Params.getvalue("member-activite-text"))
            self.fill_grid(0, Activity, "activity", Activity.objects.all())


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class AgeAddModify(XferAddEditor):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption_add = _("Add age")
    caption_modify = _("Modify age")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class AgeDel(XferDelete):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption = _("Delete age")


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class TeamAddModify(XferAddEditor):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption_add = _("Add team")
    caption_modify = _("Modify team")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class TeamDel(XferDelete):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption = _("Delete team")


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('CORE.add_parameter')
class ActivityAddModify(XferAddEditor):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption_add = _("Add activity")
    caption_modify = _("Modify activity")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('CORE.add_parameter')
class ActivityDel(XferDelete):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption = _("Delete activity")


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
        fill_params(xfer, ["member-subscription-mode", "member-subscription-message"], True)
    elif (xfer is not None) and (wizard_ident == "member_category"):
        xfer.add_title(_("Diacamma member"), _("Categories"), _('Configuration of categories'))
        xfer.new_tab(_('Parameters'))
        fill_params(xfer, ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable"], True)
        if Params.getvalue("member-age-enable") == 1:
            xfer.new_tab(_('Age'))
            xfer.fill_grid(1, Age, "age", Age.objects.all())
        if Params.getvalue("member-team-enable") == 1:
            xfer.new_tab(Params.getvalue("member-team-text"))
            xfer.fill_grid(1, Team, "team", Team.objects.all())
        if Params.getvalue("member-activite-enable") == 1:
            xfer.new_tab(Params.getvalue("member-activite-text"))
            xfer.fill_grid(1, Activity, "activity", Activity.objects.all())
    elif (xfer is not None) and (wizard_ident == "member_params"):
        xfer.add_title(_("Diacamma member"), _('Parameters'), _('Configuration of main parameters'))
        fill_params(xfer, ["member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-connection"], True)
