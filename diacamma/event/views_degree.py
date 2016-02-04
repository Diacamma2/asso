# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from lucterios.framework.xferadvance import XferAddEditor
from lucterios.framework.xferadvance import XferDelete
from lucterios.framework.tools import ActionsManage, MenuManage, WrapAction
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
            grid.add_actions(xfer, model=Degree)
            grid.set_location(0, xfer.get_max_row() + 1, 2)
            grid.set_size(200, 500)
            xfer.add_component(grid)


@ActionsManage.affect('Degree', 'edit', 'add')
@MenuManage.describ('event.add_degree')
class DegreeAddModify(XferAddEditor):
    icon = "formation.png"
    model = Degree
    field_id = 'degrees'
    caption_add = _("Add degree")
    caption_modify = _("Modify degree")


@ActionsManage.affect('Degree', 'delete')
@MenuManage.describ('event.delete_degree')
class DegreeDel(XferDelete):
    icon = "formation.png"
    model = Degree
    field_id = 'degrees'
    caption = _("Delete degree")
