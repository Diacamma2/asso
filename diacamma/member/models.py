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
from django.core.exceptions import ObjectDoesNotExist
from django_fsm import FSMIntegerField, transition

from lucterios.framework.models import LucteriosModel, get_value_converted
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.tools import convert_date, same_day_months_after
from lucterios.framework.signal_and_lock import Signal
from lucterios.framework.filetools import get_tmp_dir

from lucterios.CORE.models import Parameter, PrintModel, LucteriosUser
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual

from diacamma.invoice.models import Article, Bill, Detail, get_or_create_customer
from diacamma.accounting.tools import format_devise
from diacamma.accounting.models import CostAccounting
from diacamma.payoff.views import get_html_payment


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
        query = Q(subscription__status=2)
        query &= Q(subscription__begin_date__lte=self.date_ref) & Q(subscription__end_date__gte=self.date_ref)
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
            res2 = self.stats_by_criteria(duration_id, 'subscription__subscriptiontype', 'type')
            if (len(res1) > 0) or (len(res2) > 0):
                stat_res.append((duration_title, res1, res2))
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
        for adh in Adherent.objects.filter(Q(subscription__status=2) & Q(subscription__season=self)):
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
        ident_field = []
        ident_field.extend(super(Adherent, cls).get_search_fields())
        if Params.getvalue("member-numero"):
            ident_field.append('num')
        if Params.getvalue("member-birth"):
            ident_field.extend(['birthday', 'birthplace'])
        ident_field.extend(['subscription_set.status', 'subscription_set.season', 'subscription_set.subscriptiontype',
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
                'email', 'birthday', 'birthplace', 'comment', 'user', 'subscription_set', 'responsability_set', 'documents', 'OUR_DETAIL']

    @property
    def documents(self):
        value = ""
        for doc in self.current_subscription.docadherent_set.all():
            if doc.value:
                color = "green"
            else:
                color = "red"
            value += "%s: {[font color='%s']}%s{[/font]}{[br/]}" % (six.text_type(doc.document), color, get_value_converted(doc.value, True))
        return value

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
        sub = self.current_subscription
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
            new_subscription = Subscription(adherent=self, subscriptiontype=last_subscription.subscriptiontype)
            new_subscription.set_periode(dateref)
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
        Bill, verbose_name=_('bill'), null=True, default=None, db_index=True, on_delete=models.SET_NULL)
    begin_date = models.DateField(verbose_name=_('begin date'), null=False)
    end_date = models.DateField(verbose_name=_('end date'), null=False)
    status = FSMIntegerField(verbose_name=_('status'),
                             choices=((0, _('waiting')), (1, _('building')), (2, _('valid')), (3, _('cancel')), (4, _('disbarred'))), null=False, default=2, db_index=True)

    def __str__(self):
        if not isinstance(self.begin_date, six.text_type) and not isinstance(self.end_date, six.text_type):
            return "%s:%s->%s" % (self.subscriptiontype, formats.date_format(self.begin_date, "SHORT_DATE_FORMAT"), formats.date_format(self.end_date, "SHORT_DATE_FORMAT"))
        else:
            return self.subscriptiontype

    @classmethod
    def get_default_fields(cls):
        fields = ["season", "subscriptiontype", "status", "begin_date", "end_date"]
        if Params.getvalue("member-licence-enabled"):
            fields.append("license_set")
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

    def change_bill(self):
        if len(self.subscriptiontype.articles.all()) == 0:
            return
        self.status = int(self.status)
        if self.status in (1, 2):
            if (self.status == 2) and (self.bill is not None) and (self.bill.bill_type == 0) and (self.bill.status == 1):
                self.bill = self.bill.convert_to_bill()
            create_bill = (self.bill is None)
            if self.status == 1:
                bill_type = 0
            else:
                bill_type = 1
            if create_bill:
                self.bill = Bill.objects.create(bill_type=bill_type, date=self.season.date_ref, third=get_or_create_customer(self.adherent_id))
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
                cmt = ["{[b]}%s{[/b]}" % _("subscription"), "{[i]}%s{[/i]}: %s" %
                       (_('subscription type'), six.text_type(self.subscriptiontype))]
                self.bill.comment = "{[br/]}".join(cmt)
                self.bill.save()
                self.bill.detail_set.all().delete()
                for art in self.subscriptiontype.articles.all():
                    Detail.create_for_bill(self.bill, art)
                if hasattr(self, 'send_email_param'):
                    self.sendemail(self.send_email_param)
        if (self.status == 3) and (self.bill is not None):
            if self.bill.status == 0:
                self.bill.delete()
                self.bill = None
            elif self.bill.status == 1:
                new_assetid = self.bill.cancel()
                if new_assetid is not None:
                    self.bill = Bill.objects.get(id=new_assetid)

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
        if not force_insert:
            self.change_bill()
        LucteriosModel.save(self, force_insert=force_insert,
                            force_update=force_update, using=using, update_fields=update_fields)
        if is_new:
            for doc in self.season.document_set.all():
                DocAdherent.objects.create(
                    subscription=self, document=doc, value=False)

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
        pass

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
        if self.status != 0:
            return _('You cannot delete this subscription!')
        return ""

    def sendemail(self, sendemail):
        if sendemail is not None:
            self.bill.valid()
            if self.adherent.email != '':
                subscription_message = Params.getvalue("member-subscription-message")
                subscription_message = subscription_message.replace('\n', '<br/>')
                subscription_message = subscription_message.replace('{[', '<')
                subscription_message = subscription_message.replace(']}', '>')
                if self.bill.payoff_have_payment():
                    subscription_message += get_html_payment(sendemail[0], sendemail[1], self.bill)
                self.bill.send_email(_('New subscription'), "<html>%s</html>" % subscription_message, PrintModel.get_print_default(2, Bill))
                return True
        return False

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


class CommandManager(object):

    def __init__(self, file_name, items):
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
                for lic in item.last_subscription.license_set.all():
                    team.append(lic.team.id)
                    activity.append(lic.activity.id)
                    licence.append(lic.value)
                cmd_value["team"] = team
                cmd_value["activity"] = activity
                cmd_value["licence"] = licence
                cmd_value["reduce"] = 0.0
                self.commands.append(cmd_value)
            self.write()

    def write(self):
        import json
        self.file_name = join(get_tmp_dir(), 'list.cmd')
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
        cmd_value["reduce"] = format_devise(content_item["reduce"], 5)
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
            for fname in ["team", "activity", "licence"]:
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
        for content_item in self.commands:
            new_subscription = Subscription(adherent_id=content_item["adherent"], subscriptiontype_id=content_item["type"], status=1)
            new_subscription.set_periode(dateref)
            new_subscription.save()
            teams = content_item["team"]
            activities = content_item["activity"]
            licences = content_item["licence"]
            for license_id in range(max(len(teams), len(activities), len(licences))):
                license_item = License()
                license_item.subscription = new_subscription
                try:
                    license_item.value = licences[license_id]
                except:
                    license_item.value = ''
                try:
                    license_item.team_id = teams[license_id]
                except:
                    license_item.team_id = None
                try:
                    license_item.activity_id = activities[license_id]
                except:
                    license_item.activity_id = 0
                license_item.save()
            nb_sub += 1
            if new_subscription.bill is not None:
                details = new_subscription.bill.detail_set.all().order_by('-id')
                details[0].reduce = content_item["reduce"]
                details[0].save()
                if new_subscription.sendemail(sendemail):
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
                               args="{'Multi':True}", value=_('Welcome,\n\nYou have a new subscription.Joint, the quotation relative.\n\nRegards,'))
    Parameter.check_and_create(name="member-subscription-mode", typeparam=4, title=_("member-subscription-mode"), args="{'Enum':3}", value='0',
                               param_titles=(_("member-subscription-mode.0"), _("member-subscription-mode.1"), _("member-subscription-mode.2")))
