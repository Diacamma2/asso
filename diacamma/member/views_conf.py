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

from diacamma.member.models import Activity, Age, Team

from lucterios.framework.xferadvance import XferAddEditor, XferListEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import ActionsManage, MenuManage,\
    FORMTYPE_NOMODAL
from lucterios.CORE.parameters import Params
from lucterios.framework.xfercomponents import XferCompButton
from lucterios.CORE.views import ParamEdit


@MenuManage.describ('CORE.change_parameter', FORMTYPE_NOMODAL, 'member.conf', _('Management of member categories'))
class CategoryConf(XferListEditor):
    icon = "config.png"
    caption = _("Categories")

    def fillresponse_header(self):
        self.new_tab(_('Parameters'))
        param_lists = ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable",
                       "member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-connection"]
        Params.fill(self, param_lists, 1, 1, nb_col=2)
        btn = XferCompButton('editparam')
        btn.set_location(1, self.get_max_row() + 1, 2, 1)
        btn.set_action(self.request, ParamEdit.get_action(
            _('Modify'), 'images/edit.png'), {'close': 0, 'params': {'params': param_lists, 'nb_col': 2}})
        self.add_component(btn)

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


@ActionsManage.affect('Age', 'edit', 'add')
@MenuManage.describ('CORE.add_parameter')
class AgeAddModify(XferAddEditor):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption_add = _("Add age")
    caption_modify = _("Modify age")


@ActionsManage.affect('Age', 'delete')
@MenuManage.describ('CORE.add_parameter')
class AgeDel(XferDelete):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption = _("Delete age")


@ActionsManage.affect('Team', 'edit', 'add')
@MenuManage.describ('CORE.add_parameter')
class TeamAddModify(XferAddEditor):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption_add = _("Add team")
    caption_modify = _("Modify team")


@ActionsManage.affect('Team', 'delete')
@MenuManage.describ('CORE.add_parameter')
class TeamDel(XferDelete):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption = _("Delete team")


@ActionsManage.affect('Activity', 'edit', 'add')
@MenuManage.describ('CORE.add_parameter')
class ActivityAddModify(XferAddEditor):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption_add = _("Add activity")
    caption_modify = _("Modify activity")


@ActionsManage.affect('Activity', 'delete')
@MenuManage.describ('CORE.add_parameter')
class ActivityDel(XferDelete):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption = _("Delete activity")
