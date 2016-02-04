# -*- coding: utf-8 -*-
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
