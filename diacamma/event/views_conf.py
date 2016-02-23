# -*- coding: utf-8 -*-
'''
diacamma.event.views_conf modules

@author: Laurent GAY
@organization: sd-libre.fr
@contact: info@sd-libre.fr
@copyright: 2016 sd-libre.fr
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

from lucterios.framework.xferadvance import XferListEditor
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.xfercomponents import XferCompButton
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage
from lucterios.CORE.parameters import Params
from lucterios.CORE.views import ParamEdit

from diacamma.event.models import DegreeType, SubDegreeType


@MenuManage.describ('event.change_degreetype', FORMTYPE_NOMODAL, 'member.conf', _('Management of degrees'))
class EventConf(XferListEditor):
    icon = "degree.png"
    caption = _("Configuration of degrees")

    def fillresponse_header(self):
        self.new_tab(_('Parameters'))
        param_lists = ["event-degree-text", "event-subdegree-enable",
                       "event-subdegree-text", "event-comment-text"]
        Params.fill(self, param_lists, 1, 1, nb_col=1)
        btn = XferCompButton('editparam')
        btn.set_location(1, self.get_max_row() + 1, 2, 1)
        btn.set_action(self.request, ParamEdit.get_action(
            _('Modify'), 'images/edit.png'), {'close': 0, 'params': {'params': param_lists, 'nb_col': 1}})
        self.add_component(btn)

    def fillresponse_body(self):
        self.new_tab(Params.getvalue("event-degree-text"))
        self.fill_grid(0, DegreeType, "degreetype", DegreeType.objects.all())
        if Params.getvalue("event-subdegree-enable") == 1:
            self.new_tab(Params.getvalue("event-subdegree-text"))
            self.fill_grid(
                0, SubDegreeType, "subdegreetype", SubDegreeType.objects.all())


@ActionsManage.affect('DegreeType', 'edit', 'add')
@MenuManage.describ('event.add_degreetype')
class DegreeTypeAddModify(XferAddEditor):
    icon = "degree.png"
    model = DegreeType
    field_id = 'degreetype'
    caption_add = _("Add degree type")
    caption_modify = _("Modify degree type")


@ActionsManage.affect('DegreeType', 'delete')
@MenuManage.describ('event.delete_degreetype')
class DegreeTypeDel(XferDelete):
    icon = "degree.png"
    model = DegreeType
    field_id = 'degreetype'
    caption = _("Delete degree type")


@ActionsManage.affect('SubDegreeType', 'edit', 'add')
@MenuManage.describ('event.add_degreetype')
class SubDegreeTypeAddModify(XferAddEditor):
    icon = "degree.png"
    model = SubDegreeType
    field_id = 'subdegreetype'
    caption_add = _("Add sub degree type")
    caption_modify = _("Modify sub degree type")


@ActionsManage.affect('SubDegreeType', 'delete')
@MenuManage.describ('event.delete_degreetype')
class SubDegreeTypeDel(XferDelete):
    icon = "degree.png"
    model = SubDegreeType
    field_id = 'subdegreetype'
    caption = _("Delete sub degree type")
