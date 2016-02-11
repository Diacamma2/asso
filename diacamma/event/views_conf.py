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

from diacamma.event.models import DegreeType, SubDegreeType

from lucterios.framework.xferadvance import XferListEditor
from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import FORMTYPE_NOMODAL, ActionsManage, MenuManage


@MenuManage.describ('event.change_degreetype', FORMTYPE_NOMODAL, 'member.conf', _('Management of degrees'))
class EventConf(XferListEditor):
    icon = "formation.png"
    caption = _("Configuration of degrees")

    def fillresponse(self):
        self.new_tab(_('Degree'))
        self.fill_grid(0, DegreeType, "degreetype", DegreeType.objects.all())
        self.new_tab(_('Sub-degree'))
        self.fill_grid(
            0, SubDegreeType, "subdegreetype", SubDegreeType.objects.all())


@ActionsManage.affect('DegreeType', 'edit', 'add')
@MenuManage.describ('event.add_degreetype')
class DegreeTypeAddModify(XferAddEditor):
    icon = "formation.png"
    model = DegreeType
    field_id = 'degreetype'
    caption_add = _("Add degree type")
    caption_modify = _("Modify degree type")


@ActionsManage.affect('DegreeType', 'delete')
@MenuManage.describ('event.delete_degreetype')
class DegreeTypeDel(XferDelete):
    icon = "formation.png"
    model = DegreeType
    field_id = 'degreetype'
    caption = _("Delete degree type")


@ActionsManage.affect('SubDegreeType', 'edit', 'add')
@MenuManage.describ('event.add_degreetype')
class SubDegreeTypeAddModify(XferAddEditor):
    icon = "formation.png"
    model = SubDegreeType
    field_id = 'subdegreetype'
    caption_add = _("Add sub degree type")
    caption_modify = _("Modify sub degree type")


@ActionsManage.affect('SubDegreeType', 'delete')
@MenuManage.describ('event.delete_degreetype')
class SubDegreeTypeDel(XferDelete):
    icon = "formation.png"
    model = SubDegreeType
    field_id = 'subdegreetype'
    caption = _("Delete sub degree type")
