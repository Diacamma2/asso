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

from django.db import models
from django.db.models.aggregates import Min, Max, Count
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import formats, six
from django.core.exceptions import ObjectDoesNotExist

from lucterios.framework.models import LucteriosModel
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import convert_date, same_day_months_after

from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual

from diacamma.invoice.models import Article, Bill, Detail,\
    get_or_create_customer
from diacamma.accounting.tools import format_devise
from diacamma.accounting.models import Third, AccountThird, CostAccounting
import logging


class Season(LucteriosModel):
    designation = models.CharField(_('designation'), max_length=100)
    iscurrent = models.BooleanField(
        verbose_name=_('is current'), default=False)

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
        return ["designation", ((_('begin date'), "begin_date"), (_('end date'), 'end_date')), 'period_set', 'document_set']

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

    def stats_by_criteria(self, duration_id, field, name):
        val_by_city = {}
        query = Q(subscription__begin_date__lte=self.date_ref) & Q(
            subscription__end_date__gte=self.date_ref)
        query &= Q(subscription__subscriptiontype__duration=duration_id)
        birthday = date(
            self.date_ref.year - 18, self.date_ref.month, self.date_ref.day)
        total = 0
        for age in range(2):
            if age == 0:
                new_query = query & Q(birthday__gte=birthday)
                offset = +1
            else:
                new_query = query & Q(birthday__lt=birthday)
                offset = -1
            values = Adherent.objects.filter(new_query).values(
                field, 'genre').annotate(genre_sum=Count('genre'))
            for value in values:
                if value[field] not in val_by_city.keys():
                    val_by_city[value[field]] = [0, 0, 0, 0]
                val_by_city[value[field]][
                    value['genre'] + offset] += value['genre_sum']
                total += value['genre_sum']
        total_by_city = [0, 0, 0, 0]
        values_by_city = []
        for city in val_by_city.keys():
            city_sum = val_by_city[city][
                0] + val_by_city[city][1] + val_by_city[city][2] + val_by_city[city][3]
            values_by_city.append({name: city, "MajM": val_by_city[city][0], "MajW": val_by_city[
                                  city][1], "MinM": val_by_city[city][2], "MinW": val_by_city[city][3], "sum": city_sum, "ratio": "%d (%.1f%%)" % (city_sum, 100 * city_sum / total)})
            for idx in range(4):
                total_by_city[idx] += val_by_city[city][idx]
        values_by_city.sort(key=lambda val: -1 * val['sum'])
        if len(values_by_city) > 0:
            values_by_city.append({name: "{[b]}%s{[/b]}" % _('total'), "MajM": "{[b]}%d{[/b]}" % total_by_city[0], "MajW": "{[b]}%d{[/b]}" % total_by_city[
                                  1], "MinM": "{[b]}%d{[/b]}" % total_by_city[2], "MinW": "{[b]}%d{[/b]}" % total_by_city[3], "ratio": "{[b]}%d{[/b]}" % total})
        return values_by_city

    def get_statistic(self):
        stat_res = []
        for duration_id, duration_title in SubscriptionType().get_field_by_name('duration').choices:
            res1 = self.stats_by_criteria(duration_id, 'city', 'city')
            res2 = self.stats_by_criteria(
                duration_id, 'subscription__subscriptiontype', 'type')
            if (len(res1) > 0) or (len(res2) > 0):
                stat_res.append((duration_title, res1, res2))
        return stat_res

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

    @property
    def begin_date(self):
        val = self.period_set.all().aggregate(Min('begin_date'))
        if 'begin_date__min' in val.keys():
            return val['begin_date__min']
        else:
            return "---"

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

    @property
    def end_date(self):
        val = self.period_set.all().aggregate(Max('end_date'))
        if 'end_date__max' in val.keys():
            return val['end_date__max']
        else:
            return "---"

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
    season = models.ForeignKey(
        Season, verbose_name=_('season'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
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
    duration = models.IntegerField(verbose_name=_('duration'), choices=((0, _('annually')), (1, _(
        'periodic')), (2, _('monthly')), (3, _('calendar'))), null=False, default=0, db_index=True)
    unactive = models.BooleanField(verbose_name=_('unactive'), default=False)
    articles = models.ManyToManyField(
        Article, verbose_name=_('articles'), blank=True)

    def __str__(self):
        return self.name

    def get_text_value(self):
        return "%s [%s]" % (self.name, self.price)

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", 'duration', "unactive", (_('price'), 'price')]

    @classmethod
    def get_edit_fields(cls):
        return ["name", "description", 'duration', "unactive", ('articles', None)]

    @classmethod
    def get_show_fields(cls):
        return ["name", "description", 'duration', 'unactive', ((_('price'), 'price'),), 'articles']

    @property
    def price(self):
        total_price = 0
        for art in self.articles.all():
            total_price += art.price
        return format_devise(total_price, 5)

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


class Age(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    minimum = models.IntegerField(
        verbose_name=_('minimum'), null=False, default=0)
    maximum = models.IntegerField(
        verbose_name=_('maximum'), null=False, default=0)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ["name", (_("date min."), "date_min"), (_("date max."), "date_max")]

    @classmethod
    def get_edit_fields(cls):
        return ["name"]

    @classmethod
    def get_show_fields(cls):
        return ["name", ((_("date min."), "date_min"),), ((_("date max."), "date_max"),)]

    def set_dates(self, datemin, datemax):
        if datemin > datemax:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        ref_year = Season.current_season().reference_year
        self.maximum = ref_year - datemin
        self.minimum = ref_year - datemax

    @property
    def date_min(self):
        return Season.current_season().reference_year - self.maximum

    @property
    def date_max(self):
        return Season.current_season().reference_year - self.minimum

    class Meta(object):
        verbose_name = _('age')
        verbose_name_plural = _('ages')
        ordering = ['-minimum']
        default_permissions = []


class Adherent(Individual):
    num = models.IntegerField(
        verbose_name=_('numeros'), null=False, default=0,)
    birthday = models.DateField(
        verbose_name=_('birthday'), default=date.today, null=True)
    birthplace = models.CharField(_('birthplace'), max_length=50, blank=True)

    def __init__(self, *args, **kwargs):
        Individual.__init__(self, *args, **kwargs)
        self.date_ref = None

    def set_context(self, xfer):
        if xfer is not None:
            self.date_ref = convert_date(xfer.getparam("dateref"))

    @classmethod
    def get_renew_fields(cls):
        fields = Individual.get_default_fields()
        if Params.getvalue("member-numero"):
            fields.insert(0, "num")
        return fields

    @classmethod
    def get_default_fields(cls):
        fields = cls.get_renew_fields()
        if Params.getvalue("member-licence-enabled"):
            fields.append((_('license'), 'license'))
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = Individual.get_edit_fields()
        if Params.getvalue("member-birth"):
            fields.insert(-1, ("birthday", "birthplace"))
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = Individual.get_show_fields()
        keys = list(fields.keys())
        if Params.getvalue("member-numero"):
            fields[keys[0]][0] = ("num", fields[keys[0]][0])
        if Params.getvalue("member-birth"):
            fields[keys[0]].insert(-1, ("birthday", "birthplace"))
            fields[keys[0]].insert(-1, ((_("age category"), "age_category"),))
        fields[_('002@Subscription')] = ['subscription_set']
        fields[''] = [((_("reference date"), "dateref"),)]
        return fields

    @classmethod
    def get_search_fields(cls):
        if Params.getvalue("member-numero"):
            ident_field = ['num']
        else:
            ident_field = []
        ident_field.extend(super(Adherent, cls).get_search_fields())
        if Params.getvalue("member-birth"):
            ident_field.extend(['birthday', 'birthplace'])
        ident_field.extend(['subscription_set.season', 'subscription_set.subscriptiontype',
                            'subscription_set.begin_date', 'subscription_set.end_date'])
        if Params.getvalue("member-team-enable"):
            # Params.getvalue("member-team-text")
            ident_field.append('subscription_set.license_set.team')
        if Params.getvalue("member-activite-enable"):
            # Params.getvalue("member-activite-text")
            ident_field.append('subscription_set.license_set.activity')
        if Params.getvalue("member-licence-enabled"):
            ident_field.append('subscription_set.license_set.value')
        return ident_field

    @classmethod
    def get_import_fields(cls):
        fields = super(Individual, cls).get_import_fields()
        fields.append(('subscriptiontype', _('subscription type')))
        if Params.getvalue("member-team-enable"):
            fields.append(('team', Params.getvalue("member-team-text")))
        if Params.getvalue("member-activite-enable"):
            fields.append(
                ('activity', Params.getvalue("member-activite-text")))
        if Params.getvalue("member-licence-enabled"):
            fields.append(('value', _('license #')))
        return fields

    def _import_subscription(self, type_name, dateformat):
        working_subscription = None
        current_season = Season.current_season()
        type_option = 0
        if '#' in type_name:
            type_name, type_option = type_name.split('#')
        try:
            type_obj = SubscriptionType.objects.filter(name=type_name)
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
                    working_subscription = Subscription.objects.get(
                        adherent=self, season=current_season, subscriptiontype=type_obj, begin_date=begin_date, end_date=end_date)
                except ObjectDoesNotExist:
                    working_subscription = Subscription()
                    working_subscription.adherent = self
                    working_subscription.season = current_season
                    working_subscription.subscriptiontype = type_obj
                    working_subscription.begin_date = begin_date
                    working_subscription.end_date = end_date
                    working_subscription.save()
                if isinstance(working_subscription, tuple):
                    working_subscription = working_subscription[0]
        except:
            logging.getLogger('diacamma.member').exception("import_data")
        return working_subscription

    @classmethod
    def import_data(cls, rowdata, dateformat):
        try:
            new_item = super(Individual, cls).import_data(rowdata, dateformat)
            if new_item is not None:
                working_subscription = None
                if 'subscriptiontype' in rowdata.keys():
                    working_subscription = new_item._import_subscription(
                        rowdata['subscriptiontype'], dateformat)
                if working_subscription is None:
                    working_subscription = new_item.last_subscription
                if working_subscription is not None:
                    working_subscription.import_licence(rowdata)
            return new_item
        except:
            logging.getLogger('diacamma.member').exception("import_data")
            return None

    @classmethod
    def get_print_fields(cls):
        return ["image", 'num', "firstname", "lastname", 'address', 'postal_code', 'city', 'country', 'tel1', 'tel2',
                'email', 'birthday', 'birthplace', 'comment', 'user', 'subscription_set', 'responsability_set', 'OUR_DETAIL']

    @property
    def age_category(self):
        try:
            age_val = int(self.dateref.year - self.birthday.year)
            ages = Age.objects.filter(
                minimum__lte=age_val, maximum__gte=age_val)
            val = ages[0]
        except:
            val = "---"
        return val

    @property
    def license(self):
        sub = self.current_subscription()
        if sub is not None:
            resvalue = []
            for sub_lic in sub.license_set.all():
                resvalue.append(six.text_type(sub_lic))
            return "{[br/]}".join(resvalue)
        return None

    @property
    def dateref(self):
        if self.date_ref is None:
            self.date_ref = Season.current_season().date_ref
        return self.date_ref

    def renew(self, dateref):
        last_subscription = self.last_subscription
        if last_subscription is not None:
            current_season = Season.get_from_date(dateref)
            new_subscription = Subscription(
                adherent=self, subscriptiontype=last_subscription.subscriptiontype, season=current_season)
            if new_subscription.subscriptiontype.duration == 0:  # periodic
                new_subscription.begin_date = current_season.begin_date
                new_subscription.end_date = current_season.end_date
            elif new_subscription.subscriptiontype.duration == 1:  # periodic
                period = current_season.get_period_from_date(dateref)
                new_subscription.begin_date = period.begin_date
                new_subscription.end_date = period.end_date
            elif new_subscription.subscriptiontype.duration == 2:  # monthly
                new_subscription.begin_date = convert_date(
                    '%4d-%02d-01' % (dateref.year, dateref.month))
                new_subscription.end_date = same_day_months_after(
                    new_subscription.begin_date, 1) - timedelta(days=1)
            elif new_subscription.subscriptiontype.duration == 3:  # calendar
                new_subscription.begin_date = dateref
                new_subscription.end_date = same_day_months_after(
                    new_subscription.begin_date, 12) - timedelta(days=1)
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

    def current_subscription(self):
        sub = self.subscription_set.filter(
            begin_date__lte=self.dateref, end_date__gte=self.dateref)
        if len(sub) > 0:
            return sub[0]
        else:
            return None

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


class Subscription(LucteriosModel):
    adherent = models.ForeignKey(
        Adherent, verbose_name=_('adherent'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    season = models.ForeignKey(
        Season, verbose_name=_('season'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    subscriptiontype = models.ForeignKey(
        SubscriptionType, verbose_name=_('subscription type'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    bill = models.ForeignKey(
        Bill, verbose_name=_('bill'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    begin_date = models.DateField(verbose_name=_('begin date'), null=False)
    end_date = models.DateField(verbose_name=_('end date'), null=False)

    def __str__(self):
        if not isinstance(self.begin_date, six.text_type) and not isinstance(self.end_date, six.text_type):
            return "%s:%s->%s" % (self.subscriptiontype, formats.date_format(self.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(self.end_date, "SHORT_DATE_FORMAT"))
        else:
            return self.subscriptiontype

    @classmethod
    def get_default_fields(cls):
        fields = ["season", "subscriptiontype", "begin_date", "end_date"]
        if Params.getvalue("member-licence-enabled"):
            fields.append("license_set")
        return fields

    @classmethod
    def get_edit_fields(cls):
        return ["season", "subscriptiontype"]

    @classmethod
    def get_show_fields(cls):
        fields = ["season", "subscriptiontype", "begin_date", "end_date"]
        if Params.getvalue("member-licence-enabled") or Params.getvalue("member-team-enable") or Params.getvalue("member-activite-enable"):
            fields.append("license_set")
        return fields

    def create_bill(self):
        if len(self.subscriptiontype.articles.all()) == 0:
            return
        self.bill = Bill.objects.create(
            bill_type=1, date=self.season.date_ref, third=get_or_create_customer(self.adherent_id))
        cost_acc = CostAccounting.objects.filter(is_default=True)
        if len(cost_acc) > 0:
            self.bill.cost_accounting = cost_acc[0]
        cmt = ["{[b]}%s{[/b]}" % _("subscription"), "{[i]}%s{[/i]}: %s" %
               (_('subscription type'), six.text_type(self.subscriptiontype))]
        self.bill.comment = "{[br/]}".join(cmt)
        self.bill.save()
        for art in self.subscriptiontype.articles.all():
            Detail.create_for_bill(self.bill, art)

    def import_licence(self, rowdata):
        try:
            team = Team.objects.get(name=rowdata['team'])
        except:
            team = None
        try:
            activity = Activity.objects.get(
                name=rowdata['activity'])
        except:
            activity = Activity.objects.all()[0]
        try:
            value = rowdata['value']
        except:
            value = ''
        if ('subscriptiontype' in rowdata.keys()) or (team is not None) or (value != ''):
            return License.objects.create(subscription=self, team=team, activity=activity, value=value)
        else:
            return None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        is_new = self.id is None
        query_dates = (Q(begin_date__lte=self.end_date) & Q(end_date__gte=self.end_date)) | (
            Q(begin_date__lte=self.begin_date) & Q(end_date__gte=self.begin_date))
        if is_new and (len(self.adherent.subscription_set.filter((Q(subscriptiontype__duration=0) & Q(season=self.season)) | (Q(subscriptiontype__duration__gt=0) & query_dates))) > 0):
            raise LucteriosException(IMPORTANT, _("dates always used!"))
        if not force_insert and is_new:
            self.create_bill()
        LucteriosModel.save(self, force_insert=force_insert,
                            force_update=force_update, using=using, update_fields=update_fields)
        if is_new:
            for doc in self.season.document_set.all():
                DocAdherent.objects.create(
                    subscription=self, document=doc, value=False)

    class Meta(object):
        verbose_name = _('subscription')
        verbose_name_plural = _('subscription')


class DocAdherent(LucteriosModel):
    subscription = models.ForeignKey(
        Subscription, verbose_name=_('subscription'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    document = models.ForeignKey(
        Document, verbose_name=_('document'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    value = models.BooleanField(
        verbose_name=_('value'), default=False)

    def __str__(self):
        return "%s %s" % (self.document, self.value)

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
    subscription = models.ForeignKey(
        Subscription, verbose_name=_('subscription'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    value = models.CharField(_('license #'), max_length=50, null=True)
    team = models.ForeignKey(
        Team, verbose_name=_('team'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    activity = models.ForeignKey(
        Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)

    def __str__(self):
        val = []
        if Params.getvalue("member-team-enable") and (self.team is not None):
            val.append(six.text_type(self.team))
        if Params.getvalue("member-activite-enable") and (self.activity is not None):
            val.append("[%s]" % six.text_type(self.activity))
        if Params.getvalue("member-licence-enabled") and (self.value is not None):
            val.append(self.value)
        return " ".join(val)

    @classmethod
    def get_default_fields(cls):
        fields = []
        if Params.getvalue("member-team-enable"):
            fields.append((Params.getvalue("member-team-text"), "team"))
        if Params.getvalue("member-activite-enable"):
            fields.append(
                (Params.getvalue("member-activite-text"), "activity"))
        if Params.getvalue("member-licence-enabled"):
            fields.append("value")
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = []
        if Params.getvalue("member-team-enable"):
            fields.append(((Params.getvalue("member-team-text"), "team"),))
        if Params.getvalue("member-activite-enable"):
            fields.append(
                ((Params.getvalue("member-activite-text"), "activity"),))
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
        verbose_name = _('license')
        verbose_name_plural = _('licenses')
        default_permissions = []
