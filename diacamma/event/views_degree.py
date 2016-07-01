# -*- coding: utf-8 -*-
'''
diacamma.event.views_degree modules

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

from lucterios.framework.xferadvance import XferAddEditor, TITLE_DELETE,\
    TITLE_MODIFY, TITLE_ADD
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import ActionsManage, MenuManage, WrapAction,\
    SELECT_SINGLE, SELECT_MULTI
from lucterios.framework import signal_and_lock
from lucterios.framework.xfercomponents import XferCompGrid

from diacamma.event.models import Degree
from diacamma.member.models import Adherent


@signal_and_lock.Signal.decorate('show_contact')
def show_contact_degree(contact, xfer):
    if WrapAction.is_permission(xfer.request, 'event.change_degree'):
        up_contact = contact.get_final_child()
        if isinstance(up_contact, Adherent):
            degrees = Degree.objects.filter(adherent=up_contact)
            xfer.new_tab(_("Degree"))
            grid = XferCompGrid('degrees')
            grid.set_model(degrees, None, xfer)
            grid.add_action_notified(xfer, Degree)
            grid.set_location(0, xfer.get_max_row() + 1, 2)
            grid.set_size(200, 500)
            xfer.add_component(grid)


@ActionsManage.affect_grid(TITLE_ADD, "images/add.png")
@ActionsManage.affect_grid(TITLE_MODIFY, "images/edit.png", unique=SELECT_SINGLE)
@MenuManage.describ('event.add_degree')
class DegreeAddModify(XferAddEditor):
    icon = "degree.png"
    model = Degree
    field_id = 'degrees'
    caption_add = _("Add degree")
    caption_modify = _("Modify degree")


@ActionsManage.affect_grid(TITLE_DELETE, "images/delete.png", unique=SELECT_MULTI)
@MenuManage.describ('event.delete_degree')
class DegreeDel(XferDelete):
    icon = "degree.png"
    model = Degree
    field_id = 'degrees'
    caption = _("Delete degree")
