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
from datetime import date, datetime, timedelta
from os.path import isfile, join
import logging
from os import unlink
from unicodedata import normalize, category

from django.db import models
from django.db.models.aggregates import Min, Max, Count
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import formats, six
from django_fsm import FSMIntegerField, transition
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from lucterios.framework.models import LucteriosModel, LucteriosVirtualField
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import convert_date, same_day_months_after, toHtml, get_bool_textual
from lucterios.framework.signal_and_lock import Signal
from lucterios.framework.filetools import get_tmp_dir

from lucterios.CORE.models import Parameter, PrintModel, LucteriosUser
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual, LegalEntity, Responsability

from diacamma.invoice.models import Article, Bill, Detail, get_or_create_customer
from diacamma.accounting.tools import get_amount_from_format_devise,\
    format_with_devise
from diacamma.accounting.models import CostAccounting
from diacamma.payoff.views import get_html_payment
from diacamma.payoff.models import PaymentMethod
from lucterios.framework.auditlog import auditlog


class Season(LucteriosModel):
    designation = models.CharField(_('designation'), max_length=100)
    iscurrent = models.BooleanField(verbose_name=_('is current'), default=False)

    begin_date = LucteriosVirtualField(verbose_name=_('begin date'), compute_from="get_begin_date", format_string='D')
    end_date = LucteriosVirtualField(verbose_name=_('end date'), compute_from='get_end_date', format_string='D')

    def __str__(self):
        return self.designation

    @classmethod
    def get_default_fields(cls):
        return ["designation", 'period_set', 'iscurrent']

    @classmethod
    def get_edit_fields(cls):
        return []

    @classmethod
    def get_show_fields(cls):
        return ["designation", ("begin_date", 'end_date'), 'period_set', 'document_set']

    def set_has_actif(self):
        all_season = Season.objects.all()
        for season_item in all_season:
            season_item.iscurrent = False
            season_item.save()
        self.iscurrent = True
        self.save()

    @classmethod
    def current_season(cls):
        try:
            return Season.objects.get(iscurrent=True)
        except ObjectDoesNotExist:
            raise LucteriosException(
                IMPORTANT, _('No default season define!'))

    @classmethod
    def get_from_date(cls, dateref):
        seasons = Season.objects.filter(
            period__begin_date__lte=dateref, period__end_date__gte=dateref)
        if len(seasons) > 0:
            return seasons[0]
        else:
            raise LucteriosException(IMPORTANT, _('No season find!'))

    def get_period_from_date(self, dateref):
        periods = self.period_set.filter(
            begin_date__lte=dateref, end_date__gte=dateref)
        if len(periods) > 0:
            return periods[0]
        else:
            raise LucteriosException(IMPORTANT, _('No period find!'))

    def stats_by_criteria(self, duration_id, only_valid, field, name, with_total):
        val_by_criteria = {}
        query = Q(subscription__status=2) if only_valid else Q(subscription__status__in=(1, 2))
        query &= Q(subscription__begin_date__lte=self.date_ref) & Q(subscription__end_date__gte=self.date_ref)
        query &= Q(subscription__subscriptiontype__duration=duration_id)
        birthday = date(self.date_ref.year - 18, self.date_ref.month, self.date_ref.day)
        total = 0
        for age in range(2):
            if age == 0:
                new_query = query & Q(birthday__gte=birthday)
                offset = +1
            else:
                new_query = query & Q(birthday__lt=birthday)
                offset = -1
            values = Adherent.objects.filter(new_query).values(field, 'genre').annotate(genre_sum=Count('genre'))
            for value in values:
                if value[field] not in val_by_criteria.keys():
                    val_by_criteria[value[field]] = [0, 0, 0, 0]
                val_by_criteria[value[field]][value['genre'] + offset] += value['genre_sum']
                total += value['genre_sum']
        total_by_criteria = [0, 0, 0, 0]
        values_by_criteria = []
        for criteria in val_by_criteria.keys():
            criteria_sum = val_by_criteria[criteria][0] + val_by_criteria[criteria][1] + val_by_criteria[criteria][2] + val_by_criteria[criteria][3]
            criteria_name = criteria
            try:
                if (name == 'type'):
                    criteria_name = six.text_type(SubscriptionType.objects.get(id=criteria))
                elif (name == 'team'):
                    criteria_name = six.text_type(Team.objects.get(id=criteria))
                elif (name == 'activity'):
                    criteria_name = six.text_type(Activity.objects.get(id=criteria))
            except Exception:
                criteria_name = '---'
            values_by_criteria.append({name: criteria_name,
                                       "MajM": val_by_criteria[criteria][0],
                                       "MajW": val_by_criteria[criteria][1],
                                       "MinM": val_by_criteria[criteria][2],
                                       "MinW": val_by_criteria[criteria][3],
                                       "sum": criteria_sum,
                                       "ratio": "%d (%.1f%%)" % (criteria_sum, 100 * criteria_sum / total) if with_total else "%d" % criteria_sum})
            for idx in range(4):
                total_by_criteria[idx] += val_by_criteria[criteria][idx]
        values_by_criteria.sort(key=lambda val: -1 * val['sum'])
        if with_total and (len(values_by_criteria) > 0):
            values_by_criteria.append({name: "{[b]}%s{[/b]}" % _('total'),
                                       "MajM": "{[b]}%d{[/b]}" % total_by_criteria[0],
                                       "MajW": "{[b]}%d{[/b]}" % total_by_criteria[1],
                                       "MinM": "{[b]}%d{[/b]}" % total_by_criteria[2],
                                       "MinW": "{[b]}%d{[/b]}" % total_by_criteria[3],
                                       "ratio": "{[b]}%d{[/b]}" % total})
        return values_by_criteria

    def stats_by_seniority(self, only_valid):
        val_by_seniority = {}
        query = Q(subscription__status=2) if only_valid else Q(subscription__status__in=(1, 2))
        query &= Q(subscription__begin_date__lte=self.date_ref) & Q(subscription__end_date__gte=self.date_ref)
        query &= Q(subscription__subscriptiontype__duration=0)
        birthday = date(self.date_ref.year - 18, self.date_ref.month, self.date_ref.day)
        total = 0
        for adh in Adherent.objects.filter(query).distinct():
            nb_sub = adh.subscription_set.filter(Q(subscriptiontype__duration=0) & Q(begin_date__lte=self.date_ref)).count()
            if adh.birthday >= birthday:
                offset = +1
            else:
                offset = -1
            if nb_sub not in val_by_seniority.keys():
                val_by_seniority[nb_sub] = [0, 0, 0, 0]
            val_by_seniority[nb_sub][adh.genre + offset] += 1
            total += 1
        values_by_seniority = []
        for seniority in val_by_seniority.keys():
            seniority_sum = val_by_seniority[seniority][0] + val_by_seniority[seniority][1] + val_by_seniority[seniority][2] + val_by_seniority[seniority][3]
            values_by_seniority.append({'seniority': seniority,
                                        "MajM": val_by_seniority[seniority][0],
                                        "MajW": val_by_seniority[seniority][1],
                                        "MinM": val_by_seniority[seniority][2],
                                        "MinW": val_by_seniority[seniority][3],
                                        "sum": seniority_sum,
                                        "ratio": "%d (%.1f%%)" % (seniority_sum, 100 * seniority_sum / total)})
        return values_by_seniority

    def get_statistic(self, only_valid):
        stat_res = []
        for duration_id, duration_title in SubscriptionType().get_field_by_name('duration').choices:
            res_city = self.stats_by_criteria(duration_id, only_valid, 'city', 'city', True)
            res_type = self.stats_by_criteria(duration_id, only_valid, 'subscription__subscriptiontype', 'type', True)
            if duration_id == 0:
                res_older = self.stats_by_seniority(only_valid)
                if Params.getvalue("member-team-enable"):
                    res_team = self.stats_by_criteria(duration_id, only_valid, 'subscription__license__team', 'team', False)
                else:
                    res_team = None
                if Params.getvalue("member-activite-enable"):
                    res_activity = self.stats_by_criteria(duration_id, only_valid, 'subscription__license__activity', 'activity', False)
                else:
                    res_activity = None
            else:
                res_older = None
                res_team = None
                res_activity = None
            if (len(res_city) > 0) or (len(res_type) > 0):
                stat_res.append((duration_title, res_city, res_type, res_older, res_team, res_activity))
        return stat_res

    def check_connection(self):
        nb_del = 0
        nb_add = 0
        nb_update = 0
        for adh in Adherent.objects.filter(Q(user__is_active=True)):
            if len(adh.subscription_set.filter(Q(season=self) & Q(status=2))) == 0:
                adh.user.is_active = False
                adh.user.save()
                nb_del += 1
        for adh in Adherent.objects.filter(Q(subscription__status=2) & Q(subscription__season=self)).distinct():
            if adh.user_id is None:
                if adh.email != '':
                    username_temp = adh.firstname.lower() + adh.lastname.upper()[0]
                    username_temp = ''.join(letter for letter in normalize('NFD', username_temp) if category(letter) != 'Mn')
                    username = ''
                    inc = ''
                    while (username == ''):
                        username = "%s%s" % (username_temp, inc)
                        users = LucteriosUser.objects.filter(username=username)
                        if len(users) > 0:
                            username = ''
                            if (inc == ''):
                                inc = 1
                            else:
                                inc += 1
                    user = LucteriosUser.objects.create(username=username, first_name=adh.firstname, last_name=adh.lastname, email=adh.email)
                    user.generate_password()
                    adh.user = user
                    adh.save()
                    nb_add += 1
            elif not adh.user.is_active:
                adh.user.is_active = True
                adh.user.save()
                nb_update += 1
        return nb_del, nb_add, nb_update

    @property
    def reference_year(self):
        return int(self.designation[:4])

    @property
    def date_ref(self):
        value = date.today()
        if (self.begin_date > value) or (self.end_date < value):
            value = date(self.begin_date.year, value.month, value.day)
            if self.begin_date > value:
                value = date(self.end_date.year, value.month, value.day)
        return value

    def get_begin_date(self):
        val = self.period_set.all().aggregate(Min('begin_date'))
        if 'begin_date__min' in val.keys():
            return val['begin_date__min']
        else:
            return None

    def get_months(self):
        months = []
        begin = self.begin_date
        for month_num in range(12):
            year = begin.year
            month = begin.month + month_num
            if month > 12:
                month -= 12
                year += 1
            months.append(
                ('%4d-%02d' % (year, month), date(year, month, 1).strftime("%B %Y")))
        return months

    def get_end_date(self):
        val = self.period_set.all().aggregate(Max('end_date'))
        if 'end_date__max' in val.keys():
            return val['end_date__max']
        else:
            return None

    def refresh_periodnum(self):
        nb = 1
        for period in self.period_set.all().order_by("begin_date", "end_date"):
            period.num = nb
            nb += 1
            period.save(refresh_num=False)

    def clone_doc_need(self):
        old_season = Season.objects.filter(
            designation__lt=self.designation).order_by("-designation")
        if len(old_season) > 0:
            for doc_need in old_season[0].document_set.all():
                doc_need.id = None
                doc_need.season = self
                doc_need.save()

    class Meta(object):
        verbose_name = _('season')
        verbose_name_plural = _('seasons')
        ordering = ['-designation']
        default_permissions = ['add', 'change']


class Document(LucteriosModel):
    season = models.ForeignKey(Season, verbose_name=_('season'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=100)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ["name"]

    @classmethod
    def get_edit_fields(cls):
        return ["name"]

    @classmethod
    def get_show_fields(cls):
        return ["season", "name"]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        is_new = self.id is None
        LucteriosModel.save(self, force_insert=force_insert,
                            force_update=force_update, using=using, update_fields=update_fields)
        if is_new:
            for sub in self.season.subscription_set.all():
                DocAdherent.objects.create(
                    subscription=sub, document=self, value=False)

    class Meta(object):
        verbose_name = _('document needs')
        verbose_name_plural = _('documents needs')
        default_permissions = []


class Period(LucteriosModel):
    season = models.ForeignKey(
        Season, verbose_name=_('season'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    num = models.IntegerField(
        verbose_name=_('numeros'), null=True, default=None,)
    begin_date = models.DateField(verbose_name=_('begin date'), null=False)
    end_date = models.DateField(verbose_name=_('end date'), null=False)

    def __str__(self):
        return "%d: %s => %s" % (self.num, formats.date_format(self.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(self.end_date, "SHORT_DATE_FORMAT"))

    def get_auditlog_object(self):
        return self.season

    @classmethod
    def get_default_fields(cls):
        return ["num", "begin_date", 'end_date']

    @classmethod
    def get_edit_fields(cls):
        return ["num", "begin_date", 'end_date']

    @classmethod
    def get_show_fields(cls):
        return ["season", "num", "begin_date", 'end_date']

    def can_delete(self):
        if len(self.season.period_set.all()) <= 2:
            return _('Each season have to have 2 periods minimum!')
        return ''

    def delete(self, using=None, refresh_num=True):
        LucteriosModel.delete(self, using=using)
        if refresh_num:
            self.season.refresh_periodnum()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, refresh_num=True):
        if self.begin_date > self.end_date:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        LucteriosModel.save(self, force_insert=force_insert,
                            force_update=force_update, using=using, update_fields=update_fields)
        if refresh_num:
            self.season.refresh_periodnum()

    class Meta(object):
        verbose_name = _('period')
        verbose_name_plural = _('periods')
        ordering = ['num']
        default_permissions = []


class SubscriptionType(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, default="")
    duration = models.IntegerField(verbose_name=_('duration'), choices=((0, _('annually')), (1, _('periodic')), (2, _('monthly')), (3, _('calendar'))), null=False, default=0, db_index=True)
    unactive = models.BooleanField(verbose_name=_('unactive'), default=False)
    articles = models.ManyToManyField(Article, verbose_name=_('articles'), blank=True)

    price = LucteriosVirtualField(verbose_name=_('price'), compute_from='get_price', format_string=lambda: format_with_devise(5))

    def __str__(self):
        return self.name

    def get_text_value(self):
        return "%s [%s]" % (self.name, get_amount_from_format_devise(self.price, 5))

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", 'duration', "unactive", 'price']

    @classmethod
    def get_edit_fields(cls):
        return ["name", "description", 'duration', "unactive", ('articles', None)]

    @classmethod
    def get_show_fields(cls):
        return ["name", "description", 'duration', 'unactive', 'price', 'articles']

    def get_price(self):
        total_price = 0
        if self.id is not None:
            for art in self.articles.all():
                total_price += art.price
        return total_price

    class Meta(object):
        verbose_name = _('subscription type')
        verbose_name_plural = _('subscription types')
        default_permissions = []


class Activity(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, default="")

    def __str__(self):
        return self.name

    @classmethod
    def get_all(cls):
        activities = Activity.objects.all()
        if hasattr(settings, "DIACAMMA_MAXACTIVITY"):
            activities = activities[0:getattr(settings, "DIACAMMA_MAXACTIVITY")]
        return activities

    @classmethod
    def get_default_fields(cls):
        return ["name", "description"]

    @classmethod
    def get_edit_fields(cls):
        return ["name", "description"]

    @classmethod
    def get_show_fields(cls):
        return ["name", "description"]

    def can_delete(self):
        if (len(Activity.objects.all()) == 1):
            return _("1 activity is needs!")
        return ""

    class Meta(object):
        verbose_name = _('activity')
        verbose_name_plural = _('activities')
        default_permissions = []
        ordering = ['name']


class Team(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, default="")
    unactive = models.BooleanField(verbose_name=_('unactive'), default=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", "unactive"]

    @classmethod
    def get_edit_fields(cls):
        return ["name", "description", "unactive"]

    @classmethod
    def get_show_fields(cls):
        return ["name", "description", "unactive"]

    class Meta(object):
        verbose_name = _('team')
        verbose_name_plural = _('teams')
        default_permissions = []
        ordering = ['name']


class Age(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    minimum = models.IntegerField(verbose_name=_('minimum'), null=False, default=0)
    maximum = models.IntegerField(verbose_name=_('maximum'), null=False, default=0)

    date_min = LucteriosVirtualField(verbose_name=_("date min."), compute_from="get_date_min")
    date_max = LucteriosVirtualField(verbose_name=_("date max."), compute_from="get_date_max")

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ["name", "date_min", "date_max"]

    @classmethod
    def get_edit_fields(cls):
        return ["name"]

    @classmethod
    def get_show_fields(cls):
        return ["name", "date_min", "date_max"]

    def set_dates(self, datemin, datemax):
        if datemin > datemax:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        ref_year = Season.current_season().reference_year
        self.maximum = ref_year - datemin
        self.minimum = ref_year - datemax

    def get_date_min(self):
        if self.id is None:
            return None
        return Season.current_season().reference_year - self.maximum

    def get_date_max(self):
        if self.id is None:
            return None
        return Season.current_season().reference_year - self.minimum

    class Meta(object):
        verbose_name = _('age')
        verbose_name_plural = _('ages')
        ordering = ['-minimum']
        default_permissions = []


class Adherent(Individual):
    num = models.IntegerField(verbose_name=_('numeros'), null=False, default=0,)
    birthday = models.DateField(verbose_name=_('birthday'), default=date.today, null=True)
    birthplace = models.CharField(_('birthplace'), max_length=50, blank=True)

    family = LucteriosVirtualField(verbose_name=_('family'), compute_from='get_family')
    age_category = LucteriosVirtualField(verbose_name=_("age category"), compute_from="get_age_category")
    license = LucteriosVirtualField(verbose_name=_('involvement'), compute_from='get_license')
    documents = LucteriosVirtualField(verbose_name=_('documents needs'), compute_from='get_documents')

    dateref = LucteriosVirtualField(verbose_name=_("reference date"), compute_from='get_dateref', format_string='D')

    def __init__(self, *args, **kwargs):
        Individual.__init__(self, *args, **kwargs)
        self.date_ref = None

    def set_context(self, xfer):
        if xfer is not None:
            self.date_ref = convert_date(xfer.getparam("dateref"))

    @classmethod
    def get_renew_fields(cls):
        fields = cls.get_default_fields()
        for item in ['license', 'documents']:
            if item in fields:
                fields.remove(item)
        return fields

    @classmethod
    def get_allowed_fields(cls):
        allowed_fields = []
        if Params.getvalue("member-numero"):
            allowed_fields.append("num")
        allowed_fields.extend(["firstname", "lastname", 'address', 'postal_code', 'city', 'country', 'tel1', 'tel2', 'email'])
        for fields in cls.get_fields_to_show():
            allowed_fields.extend(fields)
        if Params.getobject("member-family-type") is not None:
            allowed_fields.append('family')
        if Params.getvalue("member-birth"):
            allowed_fields.extend(["birthday", "birthplace", "age_category"])
        if Params.getvalue("member-licence-enabled"):
            allowed_fields.append('license')
        allowed_fields.extend(['comment', 'user', 'documents'])
        return allowed_fields

    @classmethod
    def get_default_fields(cls):
        def fill_default():
            fields = Individual.get_default_fields()
            if Params.getvalue("member-numero"):
                fields.insert(0, "num")
            if Params.getvalue("member-licence-enabled"):
                fields.append('license')
            return fields
        wanted_fields_text = Params.getvalue("member-fields")
        fields = []
        if wanted_fields_text != '':
            wanted_fields = wanted_fields_text.split(";")
            allowed_fields = cls.get_allowed_fields()
            for allowed_field in allowed_fields:
                if isinstance(allowed_field, six.text_type) and (allowed_field in wanted_fields):
                    fields.append(allowed_field)
                elif isinstance(allowed_field, tuple) and (len(allowed_field) == 2) and (allowed_field[1] in wanted_fields):
                    fields.append(allowed_field)
        if len(fields) == 0:
            fields = fill_default()
        return fields

    @classmethod
    def get_fields_title(cls, adh_fields):
        fields = []
        for adh_field in adh_fields:
            if isinstance(adh_field, six.text_type):
                dep_field = cls.get_field_by_name(adh_field)
                fields.append((adh_field, dep_field.verbose_name))
            elif isinstance(adh_field, tuple) and (len(adh_field) == 2):
                fields.append((adh_field[1], adh_field[0]))
        return fields

    @classmethod
    def get_default_fields_title(cls):
        fields = cls.get_fields_title(cls.get_default_fields())
        return fields

    @classmethod
    def get_allowed_fields_title(cls):
        fields = cls.get_fields_title(cls.get_allowed_fields())
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = Individual.get_edit_fields()
        if Params.getvalue("member-birth"):
            fields.insert(-1, ("birthday", "birthplace"))
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = super(Adherent, cls).get_show_fields()
        keys = list(fields.keys())
        if Params.getvalue("member-numero"):
            fields[keys[0]][0] = ("num", fields[keys[0]][0])
        if Params.getvalue("member-birth"):
            fields[keys[0]].insert(-1, ("birthday", "birthplace"))
            fields[keys[0]].insert(-1, ("age_category",))
        fields[_('002@Subscription')] = ['subscription_set']
        fields[''] = [("dateref",)]
        return fields

    @classmethod
    def get_search_fields(cls):
        ident_field = []
        ident_field.extend(super(Adherent, cls).get_search_fields())
        if Params.getvalue("member-numero"):
            ident_field.append('num')
        if Params.getvalue("member-birth"):
            ident_field.extend(['birthday', 'birthplace'])
        ident_field.extend(['subscription_set.status', 'subscription_set.season', 'subscription_set.subscriptiontype',
                            'subscription_set.begin_date', 'subscription_set.end_date'])
        if Params.getvalue("member-team-enable"):
            ident_field.append('subscription_set.license_set.team')
        if Params.getvalue("member-activite-enable"):
            ident_field.append('subscription_set.license_set.activity')
        if Params.getvalue("member-licence-enabled"):
            ident_field.append('subscription_set.license_set.value')
        return ident_field

    @classmethod
    def get_import_fields(cls):
        fields = super(Adherent, cls).get_import_fields()
        if Params.getobject("member-family-type") is not None:
            fields.append(('family', _('family')))
        fields.append(('subscriptiontype', _('subscription type')))
        if Params.getvalue("member-team-enable"):
            fields.append(('team', Params.getvalue("member-team-text")))
            if len(Prestation.objects.all()) > 0:
                fields.append(('prestations', _('prestations')))
        if Params.getvalue("member-activite-enable"):
            fields.append(('activity', Params.getvalue("member-activite-text")))
        if Params.getvalue("member-licence-enabled"):
            fields.append(('value', _('license #')))
        return fields

    def _import_family(self, new_family):
        family_type = Params.getobject("member-family-type")
        if family_type is None:
            raise LucteriosException(IMPORTANT, _('No family type!'))
        try:
            family = LegalEntity.objects.get(name__iexact=new_family, structure_type=family_type)
        except LegalEntity.DoesNotExist:
            family = LegalEntity()
            for fieldname, fieldvalue in self.get_default_family_value(False).items():
                setattr(family, fieldname, fieldvalue)
            family.name = new_family
            family.structure_type = family_type
            family.save()
        if self.family != family:
            Responsability.objects.create(individual=self, legal_entity=family)

    def _import_subscription(self, type_name, dateformat, is_building):
        working_subscription = None
        current_season = Season.current_season()
        type_option = 0
        if '#' in type_name:
            type_name, type_option = type_name.split('#')
        try:
            type_obj = SubscriptionType.objects.filter(name__iexact=type_name)
            if len(type_obj) > 0:
                type_obj = type_obj[0]
                if type_obj.duration == 1:
                    type_option = int(type_option) - 1
                    period_list = current_season.period_set.all()
                    begin_date = period_list[type_option].begin_date
                    end_date = period_list[type_option].end_date
                elif type_obj.duration == 2:
                    type_option = int(type_option) - 1
                    mounths = current_season.get_months()
                    begin_date = convert_date(mounths[type_option][0] + '-01')
                    end_date = same_day_months_after(
                        begin_date, 1) - timedelta(days=1)
                elif type_obj.duration == 3:
                    try:
                        begin_date = datetime.strptime(
                            type_option, dateformat).date()
                    except (TypeError, ValueError):
                        begin_date = date.today()
                    end_date = same_day_months_after(
                        begin_date, 12) - timedelta(days=1)
                else:
                    begin_date = current_season.begin_date
                    end_date = current_season.end_date
                try:
                    working_subscription = Subscription.objects.get(adherent=self,
                                                                    season=current_season, subscriptiontype=type_obj,
                                                                    begin_date=begin_date, end_date=end_date)
                except ObjectDoesNotExist:
                    working_subscription = Subscription()
                    if is_building:
                        working_subscription.status = 1
                    working_subscription.adherent = self
                    working_subscription.season = current_season
                    working_subscription.subscriptiontype = type_obj
                    working_subscription.begin_date = begin_date
                    working_subscription.end_date = end_date
                    working_subscription.save(with_bill=False)
                if isinstance(working_subscription, tuple):
                    working_subscription = working_subscription[0]
        except Exception:
            logging.getLogger('diacamma.member').exception("import_data")
        return working_subscription

    @classmethod
    def import_data(cls, rowdata, dateformat):
        try:
            new_item = super(Adherent, cls).import_data(rowdata, dateformat)
            if new_item is not None:
                if ('family' in rowdata.keys()) and (rowdata['family'].strip() != ''):
                    new_item._import_family(rowdata['family'].strip())
                working_subscription = None
                if 'subscriptiontype' in rowdata.keys():
                    working_subscription = new_item._import_subscription(rowdata['subscriptiontype'], dateformat, is_building='prestations' in rowdata)
                if working_subscription is None:
                    working_subscription = new_item.last_subscription
                if working_subscription is not None:
                    working_subscription.import_licence(rowdata)
                    working_subscription.save(with_bill=True)
            return new_item
        except Exception:
            logging.getLogger('diacamma.member').exception("import_data")
            return None

    @classmethod
    def get_print_fields(cls):
        return ["image", 'num', "firstname", "lastname", 'address', 'postal_code', 'city', 'country', 'tel1', 'tel2',
                'email', 'birthday', 'birthplace', 'comment', 'user', 'subscription_set', 'responsability_set', 'documents', 'OUR_DETAIL']

    def get_documents(self):
        if self.id is None:
            return None
        current_subscription = self.current_subscription
        if current_subscription is None:
            return None
        value = ""
        for doc in current_subscription.docadherent_set.all():
            if doc.value:
                color = "green"
            else:
                color = "red"
            value += "%s: {[font color='%s']}%s{[/font]}{[br/]}" % (six.text_type(doc.document), color, get_bool_textual(doc.value))
        return value

    def get_age_category(self):
        if self.id is None:
            return None
        try:
            age_val = int(self.dateref.year - self.birthday.year)
            ages = Age.objects.filter(minimum__lte=age_val, maximum__gte=age_val)
            val = ages[0]
        except Exception:
            val = None
        return val

    def get_license(self):
        if self.id is None:
            return None
        sub = self.current_subscription
        if sub is not None:
            return sub.involvement
        return None

    def get_dateref(self):
        if self.date_ref is None:
            self.date_ref = Season.current_season().date_ref
        return self.date_ref

    def renew(self, dateref):
        last_subscription = self.last_subscription
        if last_subscription is not None:
            new_subscription = Subscription(adherent=self, subscriptiontype=last_subscription.subscriptiontype)
            new_subscription.set_periode(dateref)
            if Params.getvalue("member-team-enable") and (len(Prestation.objects.all()) > 0):
                prestation_list = []
                for license_item in last_subscription.license_set.all():
                    pesta = Prestation.objects.filter(team_id=license_item.team_id,
                                                      activity_id=license_item.activity_id).order_by('-article__price')
                    if pesta.count() > 0:
                        prestation_list.append(pesta[0])
                new_subscription.save(with_bill=False)
                new_subscription.prestations.set(prestation_list)
                new_subscription.save(with_bill=True)
            else:
                new_subscription.save()
                for license_item in last_subscription.license_set.all():
                    license_item.id = None
                    license_item.subscription = new_subscription
                    license_item.save()

    @property
    def last_subscription(self):
        subscriptions = self.subscription_set.all().order_by('-end_date')
        if len(subscriptions) > 0:
            return subscriptions[0]
        else:
            return None

    @property
    def current_subscription(self):
        sub = self.subscription_set.filter(
            begin_date__lte=self.dateref, end_date__gte=self.dateref)
        if len(sub) > 0:
            return sub[0]
        else:
            return None

    def get_default_family_value(self, with_type=True):
        family_value = {'name': self.lastname}
        if with_type:
            family_type = Params.getobject("member-family-type")
            if family_type is None:
                raise LucteriosException(IMPORTANT, _('No family type!'))
            family_value['structure_type'] = family_type.id
        for field_name in ['address', 'postal_code', 'city', 'country', 'tel1', 'tel2', 'email']:
            family_value[field_name] = getattr(self, field_name)
        return family_value

    def get_family(self):
        if self.id is None:
            return None
        current_family = None
        current_type = Params.getobject("member-family-type")
        if current_type is not None:
            responsabilities = self.responsability_set.filter(legal_entity__structure_type=current_type).order_by('-id')
            if len(responsabilities) > 0:
                current_family = responsabilities[0].legal_entity
        return current_family

    def get_ref_contact(self):
        current_family = self.family
        if current_family is None:
            return self
        else:
            return current_family

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, new_num=True):
        if (self.id is None) and new_num:
            val = Adherent.objects.all().aggregate(Max('num'))
            if val['num__max'] is None:
                self.num = 1
            else:
                self.num = val['num__max'] + 1
        Individual.save(self, force_insert=force_insert,
                        force_update=force_update, using=using, update_fields=update_fields)

    class Meta(object):
        verbose_name = _('adherent')
        verbose_name_plural = _('adherents')


class Prestation(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, default="")
    team = models.ForeignKey(Team, verbose_name=_('team'), null=False, on_delete=models.PROTECT)
    activity = models.ForeignKey(Activity, verbose_name=_('activity'), null=False, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, verbose_name=_('article'), null=False, on_delete=models.CASCADE)

    def __str__(self):
        if Params.getvalue("member-activite-enable"):
            return "%s [%s]" % (self.team, self.activity)
        else:
            return six.text_type(self.team)

    def get_text(self):
        return "%s %s" % (self.__str__(), get_amount_from_format_devise(self.article.price, 5))

    @property
    def article_query(self):
        return Article.objects.filter(isdisabled=False, stockable=0)

    @classmethod
    def get_default_fields(cls):
        fields = ["name", "description"]
        fields.append((Params.getvalue("member-team-text"), "team"))
        if Params.getvalue("member-activite-enable"):
            fields.append((Params.getvalue("member-activite-text"), "activity"))
        fields.append("article.price")
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = ["name", "description"]
        fields.append(((Params.getvalue("member-team-text"), "team"),))
        if Params.getvalue("member-activite-enable"):
            fields.append(((Params.getvalue("member-activite-text"), "activity"),))
        fields.append('article')
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = ["name", "description"]
        fields.append(((Params.getvalue("member-team-text"), "team"),))
        if Params.getvalue("member-activite-enable"):
            fields.append(((Params.getvalue("member-activite-text"), "activity"),))
        fields.append('article')
        fields.append("article.price")
        return fields

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if (self.id is None) and (self.activity_id is None):
            self.activity = Activity.objects.all().first()
        return LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta(object):
        verbose_name = _('prestation')
        verbose_name_plural = _('prestations')
        ordering = ['team__name', 'activity__name']
        default_permissions = []


class Subscription(LucteriosModel):
    adherent = models.ForeignKey(
        Adherent, verbose_name=_('adherent'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    season = models.ForeignKey(
        Season, verbose_name=_('season'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    subscriptiontype = models.ForeignKey(
        SubscriptionType, verbose_name=_('subscription type'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    bill = models.ForeignKey(
        Bill, verbose_name=_('bill'), null=True, default=None, db_index=True, on_delete=models.SET_NULL)
    begin_date = models.DateField(verbose_name=_('begin date'), null=False)
    end_date = models.DateField(verbose_name=_('end date'), null=False)
    status = FSMIntegerField(verbose_name=_('status'),
                             choices=((0, _('waiting')), (1, _('building')), (2, _('valid')), (3, _('cancel')), (4, _('disbarred'))), null=False, default=2, db_index=True)
    prestations = models.ManyToManyField(Prestation, verbose_name=_('prestations'), blank=True)

    involvement = LucteriosVirtualField(verbose_name=_('involvement'), compute_from='get_involvement')

    def __str__(self):
        if not isinstance(self.begin_date, six.text_type) and not isinstance(self.end_date, six.text_type):
            return "%s:%s->%s" % (self.subscriptiontype, formats.date_format(self.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(self.end_date, "SHORT_DATE_FORMAT"))
        else:
            return self.subscriptiontype

    @classmethod
    def get_default_fields(cls):
        fields = ["season", "subscriptiontype", "status", "begin_date", "end_date"]
        if Params.getvalue("member-licence-enabled") or Params.getvalue("member-team-enable") or Params.getvalue("member-activite-enable"):
            fields.append("involvement")
        return fields

    @classmethod
    def get_edit_fields(cls):
        return ["adherent", "season", "subscriptiontype", "status"]

    @classmethod
    def get_show_fields(cls):
        fields = ["adherent", "season", "subscriptiontype", "status", "begin_date", "end_date"]
        if Params.getvalue("member-licence-enabled") or Params.getvalue("member-team-enable") or Params.getvalue("member-activite-enable"):
            fields.append("license_set")
        return fields

    def get_involvement(self):
        if self.id is None:
            return None
        res = []
        if self.prestations.all().count() == 0:
            for lic in self.license_set.all():
                res.append(six.text_type(lic))
        else:
            for presta in self.prestations.all():
                res.append(six.text_type(presta))
        return res

    @property
    def subscriptiontype_query(self):
        return SubscriptionType.objects.filter(unactive=False)

    @property
    def prestations_query(self):
        select_list = []
        for item in Prestation.objects.filter(team__unactive=False):
            select_list.append((item.id, six.text_type(item)))
        return select_list

    def set_periode(self, dateref):
        self.dateref = dateref
        self.season = Season.get_from_date(dateref)
        if self.subscriptiontype.duration == 0:  # periodic
            self.begin_date = self.season.begin_date
            self.end_date = self.season.end_date
        elif self.subscriptiontype.duration == 1:  # periodic
            period = self.season.get_period_from_date(dateref)
            self.begin_date = period.begin_date
            self.end_date = period.end_date
        elif self.subscriptiontype.duration == 2:  # monthly
            self.begin_date = convert_date('%4d-%02d-01' % (dateref.year, dateref.month))
            self.end_date = same_day_months_after(self.begin_date, 1) - timedelta(days=1)
        elif self.subscriptiontype.duration == 3:  # calendar
            self.begin_date = dateref
            self.end_date = same_day_months_after(self.begin_date, 12) - timedelta(days=1)

    def _add_detail_bill(self):
        cmt = []
        if self.bill.third.contact.id != self.adherent.id:
            cmt.append(_("Subscription of '%s'") % six.text_type(self.adherent))
        for art in self.subscriptiontype.articles.all():
            new_cmt = [art.designation]
            new_cmt.extend(cmt)
            Detail.create_for_bill(self.bill, art, designation="{[br/]}".join(new_cmt))
        for presta in self.prestations.all():
            new_cmt = [presta.name]
            new_cmt.extend(cmt)
            Detail.create_for_bill(self.bill, presta.article, designation="{[br/]}".join(new_cmt))

    def _search_or_create_bill(self, bill_type):
        new_third = get_or_create_customer(self.adherent.get_ref_contact().id)
        bill_list = Bill.objects.filter(third=new_third, bill_type=bill_type, status=0).annotate(subscription_count=Count('subscription')).filter(subscription_count__gte=1).order_by('-date')
        if len(bill_list) > 0:
            self.bill = bill_list[0]
            self.bill.date = self.season.date_ref
        if self.bill is None:
            self.bill = Bill.objects.create(bill_type=bill_type, date=self.season.date_ref, third=new_third)

    def change_bill(self):
        if (len(self.subscriptiontype.articles.all()) == 0) and (len(self.prestations.all()) == 0):
            return False
        modify = False
        if self.status in (1, 2):
            if (self.status == 2) and (self.bill is not None) and (self.bill.bill_type == 0) and (self.bill.status == 1):
                self.bill = self.bill.convert_to_bill()
                modify = True
            create_bill = (self.bill is None)
            if self.status == 1:
                bill_type = 0
            else:
                bill_type = 1
            if create_bill:
                self._search_or_create_bill(bill_type)
                modify = True
            if (self.bill.status == 0):
                self.bill.bill_type = bill_type
                if hasattr(self, 'xfer'):
                    self.bill.date = convert_date(self.xfer.getparam('dateref'), self.season.date_ref)
                elif hasattr(self, 'dateref'):
                    self.bill.date = convert_date(self.dateref, self.season.date_ref)
                else:
                    self.bill.date = self.season.date_ref
                if (self.bill.date < self.season.begin_date) or (self.bill.date > self.season.end_date):
                    self.bill.date = self.season.date_ref
                cost_acc = CostAccounting.objects.filter(is_default=True)
                if len(cost_acc) > 0:
                    self.bill.cost_accounting = cost_acc[0]
                cmt = ["{[b]}%s{[/b]}" % _("subscription")]
                if self.bill.third.contact.id == self.adherent.id:
                    cmt.append(_("Subscription of '%s'") % six.text_type(self.adherent))
                self.bill.comment = "{[br/]}".join(cmt)
                self.bill.save()
                self.bill.detail_set.all().delete()
                subscription_list = list(self.bill.subscription_set.all())
                if self not in subscription_list:
                    subscription_list.append(self)
                for subscription in subscription_list:
                    subscription._add_detail_bill()
                if hasattr(self, 'send_email_param'):
                    self.sendemail(self.send_email_param)
        if (self.status == 3) and (self.bill is not None):
            if self.bill.status == 0:
                self.bill.delete()
                self.bill = None
                modify = True
            elif self.bill.status == 1:
                new_assetid = self.bill.cancel()
                if new_assetid is not None:
                    self.bill = Bill.objects.get(id=new_assetid)
                    modify = True
        return modify

    def import_licence(self, rowdata):
        if ('prestations' in rowdata) and (rowdata['prestations'].strip() != ''):
            prestation_list = []
            for prestation_name in rowdata['prestations'].replace(',', ';').split(';'):
                try:
                    new_prestation = Prestation.objects.get(name__iexact=prestation_name.strip())
                    prestation_list.append(new_prestation)
                except Prestation.DoesNotExist:
                    pass
            self.prestations.set(prestation_list)
        elif self.prestations.count() == 0:
            try:
                team = Team.objects.get(name__iexact=rowdata['team'])
            except Exception:
                team = None
            try:
                activity = Activity.objects.get(name__iexact=rowdata['activity'])
            except Exception:
                activity = Activity.objects.all()[0]
            try:
                value = rowdata['value']
            except Exception:
                value = ''
            if ('subscriptiontype' in rowdata.keys()) or (team is not None) or (value != ''):
                return License.objects.create(subscription=self, team=team, activity=activity, value=value)
        return None

    def convert_prestations(self):
        if self.prestations.all().count() > 0:
            if self.status <= 2:
                self.license_set.all().delete()
                for presta in self.prestations.all():
                    License.objects.create(subscription=self, activity_id=presta.activity_id, team_id=presta.team_id)
            if self.status >= 2:
                self.prestations.through.objects.all().delete()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, with_bill=True):
        is_new = self.id is None
        query_dates = (Q(begin_date__lte=self.end_date) & Q(end_date__gte=self.end_date)) | (Q(begin_date__lte=self.begin_date) & Q(end_date__gte=self.begin_date))
        if is_new and (len(self.adherent.subscription_set.filter((Q(subscriptiontype__duration=0) & Q(season=self.season)) | (Q(subscriptiontype__duration__gt=0) & query_dates))) > 0):
            raise LucteriosException(IMPORTANT, _("dates always used!"))
        self.status = int(self.status)
        LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        if not force_insert and with_bill and self.change_bill():
            LucteriosModel.save(self)
        if is_new:
            for doc in self.season.document_set.all():
                DocAdherent.objects.create(subscription=self, document=doc, value=False)
        self.convert_prestations()

    transitionname__moderate = _("Moderate")

    @transition(field=status, source=0, target=1)
    def moderate(self):
        pass

    transitionname__validate = _("Validate")

    @transition(field=status, source=1, target=2)
    def validate(self):
        pass

    transitionname__cancel = _("Cancel")

    @transition(field=status, source=1, target=3)
    def cancel(self):
        if self.bill is not None:
            if self.bill.status == 0:
                self.bill.delete()
            elif (self.bill.status == 1) and (self.bill.bill_type == 0):
                self.bill.status = 2
                self.bill.save()

    transitionname__disbar = _("Disbar")

    @transition(field=status, source=2, target=4)
    def disbar(self):
        pass

    transitionname__reopen3 = _("Re-open")

    @transition(field=status, source=3, target=1)
    def reopen3(self):
        pass

    transitionname__reopen4 = _("Re-open")

    @transition(field=status, source=4, target=1)
    def reopen4(self):
        pass

    def can_delete(self):
        if self.status not in (0, 1):
            return _('You cannot delete this subscription!')
        return ""

    def delete(self, using=None):
        old_bill = self.bill
        LucteriosModel.delete(self, using=using)
        if (old_bill is not None) and (old_bill.bill_type == 0):
            if old_bill.status == 0:
                old_bill.delete()
            elif old_bill.status == 1:
                old_bill.status = 2
                old_bill.save()

    def sendemail(self, sendemail):
        if sendemail is not None:
            self.bill.valid()
            if self.adherent.email != '':
                subscription_message = toHtml(Params.getvalue("member-subscription-message").replace('\n', '<br/>'))
                if self.bill.payoff_have_payment():
                    subscription_message += get_html_payment(sendemail[0], sendemail[1], self.bill)
                self.bill.send_email(_('New subscription'), "<html>%s</html>" % subscription_message, PrintModel.get_print_default(2, Bill))
                return True
        return False

    class Meta(object):
        verbose_name = _('subscription')
        verbose_name_plural = _('subscription')
        ordering = ['-begin_date']


class DocAdherent(LucteriosModel):
    subscription = models.ForeignKey(Subscription, verbose_name=_('subscription'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, verbose_name=_('document'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    value = models.BooleanField(verbose_name=_('value'), default=False)

    def __str__(self):
        return "%s %s" % (self.document, self.value)

    def get_auditlog_object(self):
        return self.subscription

    @classmethod
    def get_default_fields(cls):
        return ["document", "value"]

    @classmethod
    def get_edit_fields(cls):
        return ["document", "value"]

    @classmethod
    def get_show_fields(cls):
        return ["document", "value"]

    class Meta(object):
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        default_permissions = []


class License(LucteriosModel):
    subscription = models.ForeignKey(Subscription, verbose_name=_('subscription'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    value = models.CharField(_('license #'), max_length=50, null=True)
    team = models.ForeignKey(Team, verbose_name=_('team'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    activity = models.ForeignKey(Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)

    def __str__(self):
        val = []
        if Params.getvalue("member-team-enable") and (self.team is not None):
            val.append(six.text_type(self.team))
        if Params.getvalue("member-activite-enable") and (self.activity is not None):
            val.append("[%s]" % six.text_type(self.activity))
        if Params.getvalue("member-licence-enabled") and (self.value is not None):
            val.append(self.value)
        return " ".join(val)

    def get_auditlog_object(self):
        return self.subscription

    @classmethod
    def get_default_fields(cls):
        fields = []
        if Params.getvalue("member-team-enable"):
            fields.append((Params.getvalue("member-team-text"), "team"))
        if Params.getvalue("member-activite-enable"):
            fields.append((Params.getvalue("member-activite-text"), "activity"))
        if Params.getvalue("member-licence-enabled"):
            fields.append("value")
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = []
        if Params.getvalue("member-team-enable"):
            fields.append(((Params.getvalue("member-team-text"), "team"),))
        if Params.getvalue("member-activite-enable"):
            fields.append(((Params.getvalue("member-activite-text"), "activity"),))
        if Params.getvalue("member-licence-enabled"):
            fields.append("value")
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = []
        if Params.getvalue("member-team-enable"):
            fields.append(((Params.getvalue("member-team-text"), "team"),))
        if Params.getvalue("member-activite-enable"):
            fields.append(
                ((Params.getvalue("member-activite-text"), "activity"),))
        if Params.getvalue("member-licence-enabled"):
            fields.append("value")
        return fields

    class Meta(object):
        verbose_name = _('involvement')
        verbose_name_plural = _('involvements')
        ordering = ['team__name', 'activity__name']
        default_permissions = []


class CommandManager(object):

    def __init__(self, user, file_name, items):
        self.username = user.username if (user.username != '') else 'anonymous'
        self.file_name = file_name
        self.commands = []
        self.items = items
        self.read()

    def get_fields(self):
        fields = []
        fields.append(("adherent", _('adherent')))
        fields.append(("type", _('subscription type')))
        if Params.getvalue("member-age-enable"):
            fields.append(("age", _("age category")))
        if Params.getvalue("member-team-enable") and (len(Prestation.objects.all()) > 0):
            fields.append(("prestations", _('prestations')))
        else:
            if Params.getvalue("member-team-enable"):
                fields.append(("team", Params.getvalue("member-team-text")))
            if Params.getvalue("member-activite-enable"):
                fields.append(("activity", Params.getvalue("member-activite-text")))
            if Params.getvalue("member-licence-enabled"):
                fields.append(("licence", "Licence"))
            fields.append(("reduce", _('reduce')))
        return fields

    def read(self):
        import json
        if (self.file_name != '') and isfile(self.file_name):
            with open(self.file_name) as data_file:
                self.commands = json.load(data_file)
        elif self.items is not None:
            for item in self.items:
                cmd_value = {}
                cmd_value["adherent"] = item.id
                cmd_value["type"] = item.last_subscription.subscriptiontype.id
                team = []
                activity = []
                licence = []
                prestations = []
                for lic in item.last_subscription.license_set.all():
                    if Params.getvalue("member-team-enable") and (len(Prestation.objects.all()) > 0):
                        pesta = Prestation.objects.filter(team_id=lic.team_id,
                                                          activity_id=lic.activity_id).order_by('-article__price')
                        if pesta.count() > 0:
                            prestations.append(pesta[0].id)
                    else:
                        team.append(lic.team.id)
                        activity.append(lic.activity.id)
                        licence.append(lic.value if lic.value is not None else '')
                cmd_value["team"] = team
                cmd_value["activity"] = activity
                cmd_value["licence"] = licence
                cmd_value["reduce"] = 0.0
                cmd_value["prestations"] = sorted(prestations)
                self.commands.append(cmd_value)
            self.write()

    def write(self):
        import json
        self.file_name = join(get_tmp_dir(), 'list-%s.cmd' % self.username)
        if isfile(self.file_name):
            unlink(self.file_name)
        with open(self.file_name, 'w') as f:
            json.dump(self.commands, f, ensure_ascii=False)

    def get_content_txt(self):
        content = []
        for content_item in self.commands:
            content.append((content_item["adherent"], self.get_txt(content_item)))
        return content

    def get_txt(self, content_item):
        item = Adherent.objects.get(id=content_item["adherent"])
        cmd_value = {}
        cmd_value["adherent"] = six.text_type(item)
        cmd_value["type"] = SubscriptionType.objects.get(id=content_item["type"]).get_text_value()
        cmd_value["age"] = item.age_category
        teams = []
        for team in Team.objects.filter(id__in=content_item["team"]):
            teams.append(six.text_type(team))
        cmd_value["team"] = '{[br/]}'.join(teams)
        activities = []
        for team in Activity.objects.filter(id__in=content_item["activity"]):
            activities.append(six.text_type(team))
        cmd_value["activity"] = '{[br/]}'.join(activities)
        cmd_value["licence"] = '{[br/]}'.join(content_item["licence"])
        cmd_value["reduce"] = content_item["reduce"]
        prestations = []
        for presta in Prestation.objects.filter(id__in=content_item["prestations"]):
            prestations.append(presta.get_text())
        cmd_value["prestations"] = '{[br/]}'.join(prestations)
        return cmd_value

    def get(self, adherentid):
        cmd_to_select = None
        for content_item in self.commands:
            if content_item["adherent"] == adherentid:
                cmd_to_select = content_item
        return cmd_to_select

    def set(self, adherentid, item):
        cmd_to_change = self.get(adherentid)
        if cmd_to_change is not None:
            for fname in ["team", "activity", "licence", "prestations"]:
                if not isinstance(item[fname], list):
                    item[fname] = [item[fname]]
            self.commands[self.commands.index(cmd_to_change)] = item
            self.write()

    def delete(self, adherentid):
        cmd_to_del = self.get(adherentid)
        if cmd_to_del is not None:
            self.commands.remove(cmd_to_del)
            self.write()

    def create_subscription(self, dateref, sendemail=None):
        nb_sub = 0
        nb_bill = 0
        bill_list = []
        for content_item in self.commands:
            new_subscription = Subscription(adherent_id=content_item["adherent"], subscriptiontype_id=content_item["type"], status=1)
            new_subscription.set_periode(dateref)
            if Params.getvalue("member-team-enable") and (len(Prestation.objects.all()) > 0):
                new_subscription.save(with_bill=False)
                new_subscription.prestations.set(Prestation.objects.filter(id__in=content_item["prestations"]))
                new_subscription.save(with_bill=True)
            else:
                new_subscription.save()
                teams = content_item["team"]
                activities = content_item["activity"]
                licences = content_item["licence"]
                for license_id in range(max(len(teams), len(activities), len(licences))):
                    license_item = License()
                    license_item.subscription = new_subscription
                    try:
                        license_item.value = licences[license_id]
                    except Exception:
                        license_item.value = ''
                    try:
                        license_item.team_id = teams[license_id]
                    except Exception:
                        license_item.team_id = None
                    try:
                        license_item.activity_id = activities[license_id]
                    except Exception:
                        license_item.activity_id = 0
                    license_item.save()
            nb_sub += 1
            if new_subscription.bill is not None:
                details = new_subscription.bill.detail_set.all().order_by('-id')
                if len(details) > 0:
                    details[0].reduce = content_item["reduce"]
                    details[0].save()
                    bill_list.append(new_subscription.bill)
        if sendemail is not None:
            for subscription_bill in set(bill_list):
                subscription_bill.valid()
                if subscription_bill.third.contact.email != '':
                    subscription_message = toHtml(Params.getvalue("member-subscription-message").replace('\n', '<br/>'))
                    if subscription_bill.payoff_have_payment() and (len(PaymentMethod.objects.all()) > 0):
                        subscription_message += get_html_payment(sendemail[0], sendemail[1], subscription_bill)
                    subscription_bill.send_email(_('New subscription'), "<html>%s</html>" % subscription_message, PrintModel.get_print_default(2, subscription_bill))
                nb_bill += 1
        return (nb_sub, nb_bill)


@Signal.decorate('checkparam')
def member_checkparam():
    Parameter.check_and_create(name="member-age-enable", typeparam=3, title=_("member-age-enable"), args="{}", value='True')
    Parameter.check_and_create(name="member-team-enable", typeparam=3, title=_("member-team-enable"), args="{}", value='True')
    Parameter.check_and_create(name="member-team-text", typeparam=0, title=_("member-team-text"), args="{'Multi':False}", value=_('Team'))
    Parameter.check_and_create(name="member-activite-enable", typeparam=3, title=_("member-activite-enable"), args="{}", value="True")
    Parameter.check_and_create(name="member-activite-text", typeparam=0, title=_("member-activite-text"), args="{'Multi':False}", value=_('Activity'))
    Parameter.check_and_create(name="member-connection", typeparam=3, title=_("member-connection"), args="{}", value='False')
    Parameter.check_and_create(name="member-birth", typeparam=3, title=_("member-birth"), args="{}", value='True')
    Parameter.check_and_create(name="member-filter-genre", typeparam=3, title=_("member-filter-genre"), args="{}", value='True')
    Parameter.check_and_create(name="member-numero", typeparam=3, title=_("member-numero"), args="{}", value='True')
    Parameter.check_and_create(name="member-licence-enabled", typeparam=3, title=_("member-licence-enabled"), args="{}", value='True')
    Parameter.check_and_create(name="member-subscription-message", typeparam=0, title=_("member-subscription-message"),
                               args="{'Multi':True, 'HyperText': True}", value=_('Welcome,{[br/]}{[br/]}You have a new subscription.Joint, the quotation relative.{[br/]}{[br/]}Regards,'))
    Parameter.check_and_create(name="member-subscription-mode", typeparam=4, title=_("member-subscription-mode"), args="{'Enum':3}", value='0',
                               param_titles=(_("member-subscription-mode.0"), _("member-subscription-mode.1"), _("member-subscription-mode.2")))
    Parameter.check_and_create(name="member-family-type", typeparam=1, title=_("member-family-type"), args="{}", value='0', meta='("contacts","StructureType", Q(), "id", False)')
    Parameter.check_and_create(name="member-size-page", typeparam=1, title=_("member-size-page"), args="{}", value='25', meta='("","", "[(25,\'25\'),(50,\'50\'),(100,\'100\'),(250,\'250\'),]", "", True)')
    Parameter.check_and_create(name="member-fields", typeparam=0, title=_("member-fields"), args="{'Multi':False}", value='')


@Signal.decorate('auditlog_register')
def member_auditlog_register():
    auditlog.register(Activity, exclude_fields=['ID'])
    auditlog.register(Team, exclude_fields=['ID'])
    auditlog.register(Age, include_fields=["name", "date_min", "date_max"])
    auditlog.register(SubscriptionType, include_fields=["name", "description", 'duration', 'unactive', 'price', 'articles'])
    auditlog.register(Season, include_fields=["designation", 'iscurrent'])
    auditlog.register(Period, exclude_fields=['ID'])
    auditlog.register(Document, exclude_fields=['ID'])
    auditlog.register(Prestation, exclude_fields=['ID'])
    auditlog.register(Adherent, exclude_fields=['ID'])
    auditlog.register(Subscription, include_fields=["season", "subscriptiontype", "status", "begin_date", "end_date"])
    auditlog.register(DocAdherent, include_fields=["document", "value"])
    auditlog.register(License, include_fields=["value", "team", "activity"])
