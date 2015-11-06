# -*- coding: utf-8 -*-
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


@MenuManage.describ('invoice.change_vat', FORMTYPE_NOMODAL, 'member.conf', _('Management of member categories'))
class CategoryConf(XferListEditor):
    icon = "config.png"
    caption = _("Categories")

    def fillresponse_header(self):
        self.new_tab(_('Parameters'))
        param_lists = ["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable",
                       "member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-account-third", "member-connection"]
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
@MenuManage.describ('member.add_age')
class AgeAddModify(XferAddEditor):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption_add = _("Add age")
    caption_modify = _("Modify age")


@ActionsManage.affect('Age', 'delete')
@MenuManage.describ('member.delete_age')
class AgeDel(XferDelete):
    icon = "config.png"
    model = Age
    field_id = 'age'
    caption = _("Delete age")


@ActionsManage.affect('Team', 'edit', 'add')
@MenuManage.describ('member.add_team')
class TeamAddModify(XferAddEditor):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption_add = _("Add team")
    caption_modify = _("Modify team")


@ActionsManage.affect('Team', 'delete')
@MenuManage.describ('member.delete_team')
class TeamDel(XferDelete):
    icon = "config.png"
    model = Team
    field_id = 'team'
    caption = _("Delete team")


@ActionsManage.affect('Activity', 'edit', 'add')
@MenuManage.describ('member.add_activity')
class ActivityAddModify(XferAddEditor):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption_add = _("Add activity")
    caption_modify = _("Modify activity")


@ActionsManage.affect('Activity', 'delete')
@MenuManage.describ('member.delete_activity')
class ActivityDel(XferDelete):
    icon = "config.png"
    model = Activity
    field_id = 'activity'
    caption = _("Delete activity")
