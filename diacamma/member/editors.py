# -*- coding: utf-8 -*-
'''
Describe database model for Django

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
from datetime import timedelta

from django.db.models.aggregates import Max
from django.utils.translation import ugettext_lazy as _
from django.utils import formats, six

from lucterios.framework.editors import LucteriosEditor
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompDate, XferCompFloat,\
    XferCompSelect, XferCompCheck, XferCompButton
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import CLOSE_NO, FORMTYPE_REFRESH, ActionsManage, get_icon_path

from lucterios.contacts.editors import IndividualEditor

from diacamma.member.models import Period, Season, SubscriptionType, License, convert_date, same_day_months_after, Activity,\
    Adherent
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual


class SeasonEditor(LucteriosEditor):

    def before_save(self, xfer):
        date = xfer.getparam('begin_date')
        if date is None:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        date = convert_date(date)
        new_season = "%d/%d" % (date.year, date.year + 1)
        if len(Season.objects.filter(designation=new_season)) > 0:
            raise LucteriosException(IMPORTANT, _("Season exists yet!"))
        self.item.designation = new_season
        self.item.iscurrent = False

    def saving(self, xfer):
        if not xfer.has_changed:
            self.before_save(xfer)
            self.item.save()
        date = convert_date(xfer.getparam('begin_date'))
        for period_idx in range(4):
            Period.objects.create(season=xfer.item, begin_date=same_day_months_after(date, period_idx * 3),
                                  end_date=same_day_months_after(date, (period_idx + 1) * 3) - timedelta(days=1))
        if len(Season.objects.all()) == 1:
            xfer.item.set_has_actif()

    def edit(self, xfer):
        lbl = XferCompLabelForm('lbl_begin_date')
        lbl.set_value_as_name(_('begin date'))
        lbl.set_location(1, 0)
        xfer.add_component(lbl)
        date = XferCompDate('begin_date')
        date.set_location(2, 0)
        date.set_needed(True)
        val = Period.objects.all().aggregate(Max('end_date'))
        if ('end_date__max' in val.keys()) and (val['end_date__max'] is not None):
            date.set_value(val['end_date__max'] + timedelta(days=1))
        xfer.add_component(date)


class PeriodEditor(LucteriosEditor):

    def edit(self, xfer):
        xfer.change_to_readonly('num')


class SubscriptionTypeEditor(LucteriosEditor):

    def edit(self, xfer):
        from diacamma.invoice.views import ArticleList
        row_init = xfer.get_max_row() + 3
        btn = XferCompButton("btn_article")
        btn.set_location(3, row_init, 2)
        btn.set_action(xfer.request, ArticleList.get_action(_('Articles'), 'diacamma.invoice/images/article.png'), close=CLOSE_NO)
        xfer.add_component(btn)


class AgeEditor(LucteriosEditor):

    def before_save(self, xfer):
        self.item.set_dates(
            xfer.getparam('date_min', 0), xfer.getparam('date_max', 0))

    def edit(self, xfer):
        lbl = XferCompLabelForm('lbl_date_min')
        lbl.set_value_as_name(_("date min."))
        lbl.set_location(1, 5)
        xfer.add_component(lbl)
        date = XferCompFloat('date_min', 1900, 2100, 0)
        date.set_location(2, 5)
        date.set_needed(True)
        date.set_value(self.item.date_min)
        xfer.add_component(date)
        lbl = XferCompLabelForm('lbl_date_max')
        lbl.set_value_as_name(_("date max."))
        lbl.set_location(1, 6)
        xfer.add_component(lbl)
        date = XferCompFloat('date_max', 1900, 2100, 0)
        date.set_location(2, 6)
        date.set_needed(True)
        date.set_value(self.item.date_max)
        xfer.add_component(date)


class AdherentEditor(IndividualEditor):

    def edit(self, xfer):
        IndividualEditor.edit(self, xfer)
        birthday = xfer.get_components('birthday')
        if birthday is not None:
            birthday.needed = True

    def show(self, xfer):
        IndividualEditor.show(self, xfer)
        if xfer.getparam('adherent') is None:
            xfer.params['adherent'] = xfer.getparam('individual', 0)
        if xfer.getparam('individual') is None:
            xfer.params['individual'] = xfer.getparam('adherent', 0)
        img = xfer.get_components('img')
        img.set_value(get_icon_path("diacamma.member/images/adherent.png"))

        if xfer.item.current_subscription is not None:
            xfer.tab = 1
            row_init = xfer.get_max_row() + 1
            row = row_init + 1
            for doc in xfer.item.current_subscription.docadherent_set.all():
                lbl = XferCompLabelForm("lbl_doc_%d" % doc.id)
                lbl.set_value(six.text_type(doc.document))
                lbl.set_location(2, row)
                xfer.add_component(lbl)
                ckc = XferCompCheck("doc_%d" % doc.id)
                ckc.set_value(doc.value)
                ckc.set_location(3, row)
                xfer.add_component(ckc)
                row += 1
            if row != row_init + 1:
                lbl = XferCompLabelForm("lbl_doc_sep")
                lbl.set_value("{[hr/]}")
                lbl.set_location(1, row_init, 4)
                xfer.add_component(lbl)
                lbl = XferCompLabelForm("lbl_doc")
                lbl.set_value_as_name(_('documents needs'))
                lbl.set_location(1, row_init + 1)
                xfer.add_component(lbl)
                btn = XferCompButton("btn_doc")
                btn.set_location(4, row_init + 1, 1, row - row_init)
                btn.set_action(xfer.request, ActionsManage.get_action_url("member.Adherent", "Doc", xfer), close=CLOSE_NO)
                xfer.add_component(btn)


class SubscriptionEditor(LucteriosEditor):

    def before_save(self, xfer):
        xfer.is_new = (self.item.id is None)
        if xfer.getparam('autocreate', 0) == 1:
            self.item.send_email_param = (xfer.request.META.get('HTTP_REFERER', xfer.request.build_absolute_uri()), xfer.language)
            self.item.season = Season.current_season()
            if self.item.adherent_id is None:
                current_contact = Individual.objects.get(user=xfer.request.user)
                current_contact = current_contact.get_final_child()
                self.item.adherent = Adherent(id=current_contact.pk)
                self.item.adherent.save(new_num=True)
                self.item.adherent.__dict__.update(current_contact.__dict__)
                self.item.adherent.save()
                self.item.adherent_id = self.item.adherent.id
        if self.item.subscriptiontype.duration == 0:  # periodic
            season = self.item.season
            self.item.begin_date = season.begin_date
            self.item.end_date = season.end_date
        elif self.item.subscriptiontype.duration == 1:  # periodic
            periodid = xfer.getparam('period', 0)
            period = Period.objects.get(id=periodid)
            self.item.begin_date = period.begin_date
            self.item.end_date = period.end_date
        elif self.item.subscriptiontype.duration == 2:  # monthly
            month_num = xfer.getparam('month', '')
            self.item.begin_date = convert_date(month_num + '-01')
            self.item.end_date = same_day_months_after(
                self.item.begin_date, 1) - timedelta(days=1)
        elif self.item.subscriptiontype.duration == 3:  # calendar
            self.item.begin_date = convert_date(
                xfer.getparam('begin_date', ''))
            self.item.end_date = same_day_months_after(
                self.item.begin_date, 12) - timedelta(days=1)

    def saving(self, xfer):
        if xfer.is_new:
            activity_id = xfer.getparam('activity')
            team_id = xfer.getparam('team')
            value = xfer.getparam('value')
            if activity_id is None:
                activity_id = Activity.objects.all()[0].id
            License.objects.create(
                subscription=self.item, value=value, activity_id=activity_id, team_id=team_id)

    def edit(self, xfer):
        autocreate = xfer.getparam('autocreate', 0) == 1
        xfer.change_to_readonly("adherent")
        cmp_status = xfer.get_components('status')
        if autocreate:
            if Params.getvalue("member-subscription-mode") == 2:
                status = 1
            else:
                status = 0
            cmp_status.set_value(status)
            xfer.change_to_readonly("status")
            xfer.params['status'] = status
        elif self.item.id is None:
            del cmp_status.select_list[0]
            del cmp_status.select_list[-2]
            del cmp_status.select_list[-1]
        else:
            xfer.change_to_readonly("status")
        last_subscription = self.item.adherent.last_subscription
        cmp_subscriptiontype = xfer.get_components('subscriptiontype')
        if (self.item.id is not None) or autocreate:
            xfer.change_to_readonly('season')
        else:
            cmp_season = xfer.get_components('season')
            if self.item.season_id is None:
                self.item.season = Season.current_season()
                cmp_season.set_value(self.item.season.id)
            cmp_season.set_action(xfer.request, xfer.get_action(),
                                  close=CLOSE_NO, modal=FORMTYPE_REFRESH)
            if (last_subscription is not None) and (xfer.getparam('subscriptiontype') is None):
                cmp_subscriptiontype.set_value(
                    last_subscription.subscriptiontype.id)
        if self.item.subscriptiontype_id is None:
            if len(cmp_subscriptiontype.select_list) == 0:
                raise LucteriosException(IMPORTANT, _("No subscription type defined!"))
            cmp_subscriptiontype.get_reponse_xml()
            self.item.subscriptiontype = SubscriptionType.objects.get(
                id=cmp_subscriptiontype.value)
        cmp_subscriptiontype.set_action(xfer.request, xfer.get_action(), close=CLOSE_NO, modal=FORMTYPE_REFRESH)
        row = xfer.get_max_row() + 1
        season = self.item.season
        if self.item.subscriptiontype.duration == 0:  # annually
            lbl = XferCompLabelForm("lbl_seasondates")
            lbl.set_location(1, row)
            lbl.set_value_as_name(_('annually'))
            xfer.add_component(lbl)
            lbl = XferCompLabelForm("seasondates")
            lbl.set_location(2, row)
            lbl.set_value("%s => %s" % (formats.date_format(
                season.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(season.end_date, "SHORT_DATE_FORMAT")))
            xfer.add_component(lbl)
        elif self.item.subscriptiontype.duration == 1:  # periodic
            lbl = XferCompLabelForm("lbl_period")
            lbl.set_location(1, row)
            lbl.set_value_as_name(_('period'))
            xfer.add_component(lbl)
            sel = XferCompSelect('period')
            sel.set_needed(True)
            sel.set_select_query(season.period_set.all())
            sel.set_location(2, row)
            xfer.add_component(sel)
        elif self.item.subscriptiontype.duration == 2:  # monthly
            lbl = XferCompLabelForm("lbl_month")
            lbl.set_location(1, row)
            lbl.set_value_as_name(_('month'))
            xfer.add_component(lbl)
            sel = XferCompSelect('month')
            sel.set_needed(True)
            sel.set_select(season.get_months())
            sel.set_location(2, row)
            xfer.add_component(sel)
        elif self.item.subscriptiontype.duration == 3:  # calendar
            lbl = XferCompLabelForm("lbl_begin_date")
            lbl.set_location(1, row)
            lbl.set_value_as_name(_('begin date'))
            xfer.add_component(lbl)
            begindate = XferCompDate('begin_date')
            begindate.set_needed(True)
            begindate.set_value(season.date_ref)
            begindate.set_location(2, row)
            xfer.add_component(begindate)
        if self.item.id is None:
            xfer.item = License()
            if last_subscription is not None:
                licenses = last_subscription.license_set.all()
                if len(licenses) > 0:
                    xfer.item = licenses[0]
            xfer.fill_from_model(1, row + 1, False)
            xfer.item = self.item
            team = xfer.get_components('team')
            if team is not None:
                team.set_needed(True)
            activity = xfer.get_components('activity')
            if activity is not None:
                activity.set_needed(True)


class LicenseEditor(LucteriosEditor):

    def edit(self, xfer):
        team = xfer.get_components('team')
        if team is not None:
            team.set_needed(True)
        activity = xfer.get_components('activity')
        if activity is not None:
            activity.set_needed(True)
        else:
            default_act = Activity.objects.all()[0]
            xfer.params['activity'] = default_act.id
