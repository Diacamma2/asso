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
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import formats

from lucterios.framework.editors import LucteriosEditor
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompDate, XferCompFloat, \
    XferCompSelect, XferCompCheck, XferCompButton
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import CLOSE_NO, FORMTYPE_REFRESH, ActionsManage, \
    FORMTYPE_MODAL, CLOSE_YES, SELECT_SINGLE, get_url_from_request
from lucterios.framework.xferadvance import TITLE_EDIT, TITLE_MODIFY, TITLE_ADD

from lucterios.CORE.parameters import Params
from lucterios.CORE.models import Preference
from lucterios.framework.xferbasic import NULL_VALUE
from lucterios.contacts.models import Individual
from lucterios.contacts.editors import IndividualEditor

from diacamma.member.models import Period, Season, Subscription, Team, License, convert_date, same_day_months_after, Activity, Adherent, \
    SubscriptionType, Prestation
from diacamma.invoice.models import Article
from diacamma.accounting.models import ChartsAccount, FiscalYear


class SeasonEditor(LucteriosEditor):

    def before_save(self, xfer):
        date = xfer.getparam('begin_date')
        if date is None:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        date = convert_date(date)
        if (date.month == 1) and (date.day == 1):
            new_season = "%4d" % date.year
        else:
            new_season = "%d/%d" % (date.year, date.year + 1)
        if len(Season.objects.filter(designation=new_season).exclude(id=self.item.id)) > 0:
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
        date = XferCompDate('begin_date')
        date.set_location(1, 0)
        date.set_needed(True)
        date.description = _('begin date')
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
        articles_comp = xfer.get_components('articles')
        btn = XferCompButton("btn_article")
        btn.set_location(articles_comp.col + articles_comp.colspan, articles_comp.row)
        btn.set_action(xfer.request, ArticleList.get_action(_('Articles'), short_icon="mdi:mdi-invoice-list-outline"), close=CLOSE_NO)
        btn.set_is_mini(True)
        xfer.add_component(btn)


class AgeEditor(LucteriosEditor):

    def before_save(self, xfer):
        self.item.set_dates(xfer.getparam('date_min', 0), xfer.getparam('date_max', 0))

    def edit(self, xfer):
        Season.current_season()
        date = XferCompFloat('date_min', 1900, 2100, 0)
        date.set_location(1, 5)
        date.set_needed(True)
        date.set_value(self.item.date_min)
        date.description = _("date min.")
        xfer.add_component(date)
        date = XferCompFloat('date_max', 1900, 2100, 0)
        date.set_location(1, 6)
        date.set_needed(True)
        date.set_value(self.item.date_max)
        date.description = _("date max.")
        xfer.add_component(date)


class AdherentEditor(IndividualEditor):

    def saving(self, xfer):
        IndividualEditor.saving(self, xfer)
        if (Params.getvalue("member-connection") == Adherent.CONNECTION_BYADHERENT) and (Params.getvalue("contacts-createaccount") != 0):
            self.item.activate_adherent()

    def edit(self, xfer):
        IndividualEditor.edit(self, xfer)
        birthday = xfer.get_components('birthday')
        if birthday is not None:
            birthday.needed = True
        if (self.item.id is None) and (xfer.getparam('legal_entity', 0) == 0) and (Params.getobject("member-family-type") is not None):
            genre = xfer.get_components('genre')
            genre.colspan -= 1
            btn = XferCompButton('famillybtn')
            btn.set_location(genre.col + genre.colspan, genre.row)
            btn.set_action(xfer.request, ActionsManage.get_action_url('member.Adherent', 'familyAdherentAdd', xfer), modal=FORMTYPE_MODAL, close=CLOSE_YES)
            xfer.add_component(btn)

    def show(self, xfer):
        IndividualEditor.show(self, xfer)
        if xfer.getparam('adherent') is None:
            xfer.params['adherent'] = xfer.getparam('individual', 0)
        if xfer.getparam('individual') is None:
            xfer.params['individual'] = xfer.getparam('adherent', 0)
        img = xfer.get_components('img')
        img.set_value('mdi:mdi-badge-account-horizontal-outline', '#')

        if Params.getobject("member-family-type") is not None:
            xfer.tab = 1
            row_init = xfer.get_max_row() + 1
            lbl = XferCompLabelForm("family")
            current_family = self.item.family
            if current_family is None:
                lbl.set_value(None)
            else:
                lbl.set_value(str(self.item.family))
            lbl.set_location(1, row_init, 2)
            lbl.description = _('family')
            xfer.add_component(lbl)
            btn = XferCompButton('famillybtn')
            btn.is_mini = True
            btn.set_location(3, row_init)
            if current_family is None:
                act = ActionsManage.get_action_url('member.Adherent', 'FamilyAdd', xfer)
                act.set_value(TITLE_ADD, 'mdi:mdi-pencil-plus-outline')
                btn.set_action(xfer.request, act, modal=FORMTYPE_MODAL, close=CLOSE_NO)
            else:
                act = ActionsManage.get_action_url('contacts.LegalEntity', 'Show', xfer)
                act.set_value(TITLE_MODIFY, 'mdi:mdi-pencil-outline')
                btn.set_action(xfer.request, act, modal=FORMTYPE_MODAL, close=CLOSE_NO, params={'legal_entity': str(current_family.id)})
            xfer.add_component(btn)

        if xfer.item.current_subscription is not None:
            xfer.tab = 1
            row_init = xfer.get_max_row() + 1
            row = row_init + 1
            for doc in xfer.item.current_subscription.docadherent_set.all():
                ckc = XferCompCheck("doc_%d" % doc.id)
                ckc.set_value(doc.value)
                ckc.set_location(2, row)
                ckc.description = str(doc.document)
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
            self.item.send_email_param = (get_url_from_request(xfer.request), xfer.language)
            self.item.season = Season.current_season()
            if self.item.adherent_id is None:
                current_contact = Individual.objects.get(user=xfer.request.user)
                current_contact = current_contact.get_final_child()
                self.item.adherent = Adherent(id=current_contact.pk)
                self.item.adherent.save(new_num=True)
                self.item.adherent.__dict__.update(current_contact.__dict__)
                self.item.adherent.save()
                self.item.adherent_id = self.item.adherent.id
        if self.item.subscriptiontype.duration == SubscriptionType.DURATION_ANNUALLY:
            season = self.item.season
            self.item.begin_date = season.begin_date
            self.item.end_date = season.end_date
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_PERIODIC:
            periodid = xfer.getparam('period', 0)
            period = Period.objects.get(id=periodid)
            self.item.begin_date = period.begin_date
            self.item.end_date = period.end_date
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_MONTLY:
            month_num = xfer.getparam('month', '')
            self.item.begin_date = convert_date(month_num + '-01')
            self.item.end_date = same_day_months_after(
                self.item.begin_date, 1) - timedelta(days=1)
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_CALENDAR:
            self.item.begin_date = convert_date(
                xfer.getparam('begin_date', ''))
            self.item.end_date = same_day_months_after(
                self.item.begin_date, 12) - timedelta(days=1)

    def saving(self, xfer):
        if xfer.is_new and (Params.getvalue("member-team-enable") != 2):
            activity_id = xfer.getparam('activity')
            team_id = xfer.getparam('team')
            value = xfer.getparam('value')
            if activity_id is None:
                activity_id = Activity.get_all().first().id
            License.objects.create(subscription=self.item, value=value, activity_id=activity_id, team_id=team_id)

    def _add_season_comp(self, xfer, row, last_subscription):
        season = self.item.season
        if self.item.subscriptiontype.duration == SubscriptionType.DURATION_ANNUALLY:
            lbl = XferCompLabelForm("seasondates")
            lbl.set_location(1, row)
            lbl.set_value("%s => %s" % (formats.date_format(season.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(season.end_date, "SHORT_DATE_FORMAT")))
            lbl.description = _('annually')
            xfer.add_component(lbl)
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_PERIODIC:
            sel = XferCompSelect('period')
            sel.set_needed(True)
            sel.set_select_query(season.period_set.all())
            sel.set_location(1, row)
            sel.description = _('period')
            xfer.add_component(sel)
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_MONTLY:
            sel = XferCompSelect('month')
            sel.set_needed(True)
            sel.set_select(season.get_months())
            sel.set_location(1, row)
            sel.description = _('month')
            xfer.add_component(sel)
        elif self.item.subscriptiontype.duration == SubscriptionType.DURATION_CALENDAR:
            begindate = XferCompDate('begin_date')
            begindate.set_needed(True)
            if last_subscription is None:
                begindate.set_value(season.date_ref)
            elif self.item.id is not None:
                begindate.set_value(self.item.begin_date)
            else:
                new_begin_date = last_subscription.end_date + timedelta(days=1)
                if (season.date_ref - new_begin_date).days < Params.getvalue('member-subscription-delaytorenew'):
                    begindate.set_value(new_begin_date)
                else:
                    begindate.set_value(season.date_ref)
            begindate.set_location(1, row)
            begindate.description = _('begin date')
            xfer.add_component(begindate)
            if (xfer.getparam('autocreate', 0) == 1) and (xfer.params['status'] == Subscription.STATUS_BUILDING):
                xfer.params['begin_date'] = begindate.value
                xfer.change_to_readonly('begin_date')

    def edit(self, xfer):
        autocreate = xfer.getparam('autocreate', 0) == 1
        last_subscription = self.item.adherent.last_subscription
        xfer.change_to_readonly("adherent")
        cmp_status = xfer.get_components('status')
        if autocreate:
            if Params.getvalue("member-subscription-mode") == Subscription.MODE_NOHIMSELF:
                raise LucteriosException(IMPORTANT, _("No subscription for this mode!"))
            elif (Params.getvalue("member-subscription-mode") == Subscription.MODE_WITHMODERATEFORNEW) and (last_subscription is not None):
                status = Subscription.STATUS_BUILDING
            elif Params.getvalue("member-subscription-mode") == Subscription.MODE_AUTOMATIQUE:
                status = Subscription.STATUS_BUILDING
            else:
                status = Subscription.STATUS_WAITING
            cmp_status.set_value(status)
            xfer.change_to_readonly("status")
            xfer.params['status'] = status
        elif self.item.id is None:
            del cmp_status.select_list[0]
            del cmp_status.select_list[-2]
            del cmp_status.select_list[-1]
            status_pref = Preference.get_value('adherent-status', xfer.request.user)
            if status_pref == Subscription.STATUS_VALID:
                cmp_status.set_value(Subscription.STATUS_VALID)
            else:
                cmp_status.set_value(Subscription.STATUS_BUILDING)
        else:
            xfer.change_to_readonly("status")
        cmp_subscriptiontype = xfer.get_components('subscriptiontype')
        if (self.item.id is None) and (last_subscription is not None) and (xfer.getparam('subscriptiontype') is None):
            cmp_subscriptiontype.set_value(last_subscription.subscriptiontype.id)
        if self.item.subscriptiontype_id is None:
            if len(cmp_subscriptiontype.select_list) == 0:
                raise LucteriosException(IMPORTANT, _("No subscription type defined!"))
            cmp_subscriptiontype.get_json()
            self.item.subscriptiontype = SubscriptionType.objects.get(id=cmp_subscriptiontype.value)
        cmp_subscriptiontype.set_action(xfer.request, xfer.return_action(), close=CLOSE_NO, modal=FORMTYPE_REFRESH)
        if (self.item.id is not None) or autocreate:
            xfer.change_to_readonly('season')
        else:
            cmp_season = xfer.get_components('season')
            current_season = Season.current_season()
            if self.item.subscriptiontype.duration in (SubscriptionType.DURATION_ANNUALLY, SubscriptionType.DURATION_CALENDAR):
                season_exclud = {sub.season_id for sub in xfer.item.adherent.subscription_set.all()}
                cmp_season.select_list = []
                for season in Season.objects.exclude(id__in=season_exclud):
                    if season.end_date < current_season.begin_date:
                        continue
                    cmp_season.select_list.append((season.id, str(season)))
                if len(cmp_season.select_list) > 0:
                    cmp_season.set_value(cmp_season.select_list[-1][0])
                self.item.season = Season.objects.get(id=cmp_season.value)
            if self.item.season_id is None:
                self.item.season = Season.current_season()
                cmp_season.set_value(self.item.season.id)
            cmp_season.set_action(xfer.request, xfer.return_action(),
                                  close=CLOSE_NO, modal=FORMTYPE_REFRESH)
        row = xfer.get_max_row() + 1
        self._add_season_comp(xfer, row, last_subscription)
        if (Params.getvalue("member-team-enable") == 2) and ((self.item.id is None) or (self.item.status in (Subscription.STATUS_WAITING, Subscription.STATUS_BUILDING))):
            xfer.filltab_from_model(1, row + 1, False, ['prestations'])
        elif self.item.id is None:
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

    def show(self, xfer):
        if (Params.getvalue("member-team-enable") == 2) and (self.item.status in (Subscription.STATUS_WAITING, Subscription.STATUS_BUILDING)):
            xfer.remove_component('license')
            xfer.filltab_from_model(1, xfer.get_max_row() + 1, True, ['prestations'])


class LicenseEditor(LucteriosEditor):

    def edit(self, xfer):
        team = xfer.get_components('team')
        if team is not None:
            team.set_needed(True)
        activity = xfer.get_components('activity')
        if activity is not None:
            activity.set_select_query(Activity.get_all())
            activity.set_needed(True)
        else:
            default_act = Activity.get_all().first()
            xfer.params['activity'] = default_act.id


def append_articles_button(xfer):
    article_comp = xfer.get_components('article')
    article_comp.set_action(xfer.request, xfer.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
    if xfer.getparam("article"):
        article_comp.value = xfer.getparam("article", 0)
    btn = XferCompButton("showarticle")
    btn.set_location(article_comp.col + article_comp.colspan, article_comp.row)
    btn.set_is_mini(True)
    btn.set_action(xfer.request, ActionsManage.get_action_url(Article.get_long_name(), 'Show', xfer), modal=FORMTYPE_MODAL, close=CLOSE_NO, params={'article': article_comp.value})
    xfer.add_component(btn)
    btn = XferCompButton("addarticle")
    btn.set_location(article_comp.col + article_comp.colspan + 1, article_comp.row)
    btn.set_is_mini(True)
    btn.set_action(xfer.request, ActionsManage.get_action_url(Article.get_long_name(), 'AddModify', xfer), modal=FORMTYPE_MODAL, close=CLOSE_NO, params={'article': NULL_VALUE})
    xfer.add_component(btn)
    if btn.action is None:
        article_comp.colspan = 3
    return article_comp


class PrestationEditor(LucteriosEditor):

    def edit(self, xfer):
        append_articles_button(xfer)
        name_comp = xfer.get_components('name')
        name_comp.colspan = 3


class TeamPrestationEditor(LucteriosEditor):

    def before_save(self, xfer):
        if ('team_name' in xfer.params) and ('team_description' in xfer.params):
            group_name = xfer.getparam('team_name', '')
            group_description = xfer.getparam('team_description', '')
            if self.item.id is None:
                self.item.team = Team.objects.create(name=group_name, description=group_description, unactive=False)
            else:
                self.item.team.name = group_name
                self.item.team.description = group_description
                self.item.team.save()
            if 'team' in xfer.params:
                del xfer.params['team']
        return

    def saving(self, xfer):
        articleid = xfer.getparam('article', 0)
        if articleid != 0:
            prest = self.item.prestation_set.first()
            if prest is None:
                Prestation.objects.create(team_prestation=self.item, article_id=articleid)
            else:
                prest.article_id = articleid
                prest.save()

    def edit(self, xfer):
        team_row = xfer.get_components('team').row
        team_col = xfer.get_components('team').col
        xfer.move(0, 0, 3)
        if self.item.id is None:
            new_group = xfer.getparam('new_group', 0)
            sel = XferCompSelect('new_group')
            sel.set_needed(True)
            sel.set_select([(0, _('new %s') % Params.getvalue("member-team-text").lower()),
                            (1, _('select old %s') % Params.getvalue("member-team-text").lower())])
            sel.set_location(team_col, team_row, 3)
            sel.set_value(new_group)
            sel.description = _('addon mode')
            sel.set_action(xfer.request, xfer.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
            xfer.add_component(sel)
        else:
            new_group = 0
        if new_group == 0:
            xfer.remove_component('team')
            xfer.model = Team
            xfer.item = self.item.team if self.item.id is not None else Team()
            xfer.filltab_from_model(team_col, team_row + 1, False, ['name', 'description'], prefix='team_')
            xfer.model = self.item.__class__
            xfer.item = self.item
            for field_name in ['team_name', 'team_description']:
                xfer.get_components(field_name).colspan = 3
        else:
            xfer.get_components('team').colspan = 3
            for field_to_del in ['team_name', 'team_description']:
                if field_to_del in xfer.params:
                    del xfer.params[field_to_del]

        multiprice = xfer.getparam('multiprice', False)
        if (self.item.id is not None) and ((self.item.prestation_set.count() > 1) or (multiprice is True)):
            xfer.fill_from_model(1, 10, True, desc_fields=['prestation_set'])
            grid = xfer.get_components('prestation')
            grid.no_pager = True
        else:
            xfer.model = Prestation
            xfer.item = xfer.item.prestation_set.first() if xfer.item.id is not None else Prestation()
            xfer.fill_from_model(1, 10, False, desc_fields=['article'])
            article_comp = append_articles_button(xfer)
            if Params.getvalue("member-activite-enable"):
                xfer.get_components('activity').colspan = article_comp.colspan
            if self.item.id is not None:
                check = XferCompCheck('multiprice')
                check.set_location(article_comp.col, article_comp.row + 1, 3)
                check.set_value(multiprice)
                check.description = _('Use multi-prices')
                check.set_action(xfer.request, xfer.return_action(), modal=FORMTYPE_REFRESH, close=CLOSE_NO)
                xfer.add_component(check)

    def show(self, xfer):
        nb_prestations = self.item.prestation_set.count()
        if nb_prestations > 1:
            article_comp = xfer.get_components('article')
            xfer.move_components('adherent', 0, nb_prestations + 5)
            xfer.remove_component('article')
            xfer.remove_component('price')
            row = article_comp.row + 1
            lbl_title = XferCompLabelForm('prices_title')
            lbl_title.set_location(article_comp.col, row)
            lbl_title.set_value(_('prices'))
            lbl_title.set_bold()
            xfer.add_component(lbl_title)
            row += 1
            for prestation in self.item.prestation_set.all():
                lbl_name = XferCompLabelForm('name_%d' % prestation.id)
                lbl_name.set_location(article_comp.col, row)
                lbl_name.set_value(prestation.name)
                lbl_name.description = '     '
                xfer.add_component(lbl_name)
                lbl_price = XferCompLabelForm('price_%d' % prestation.id)
                lbl_price.set_location(article_comp.col + 1, row)
                lbl_price.set_value(prestation.get_article_price())
                lbl_price.description = '     '
                xfer.add_component(lbl_price)
                row += 1


class TaxReceiptEditor(LucteriosEditor):

    def show(self, xfer):
        from diacamma.accounting.views_entries import EntryAccountOpenFromLine
        entryline = xfer.get_components('entryline')
        entryline.actions = []
        entryline.delete_header('link')
        entryline.add_action(xfer.request, EntryAccountOpenFromLine.get_action(TITLE_EDIT, short_icon="mdi:mdi-text-box-outline"), close=CLOSE_NO, unique=SELECT_SINGLE)
        if len(list(self.item.reason_list())) == 0:
            xfer.remove_component('__empty__')
            xfer.remove_component('type_gift')
