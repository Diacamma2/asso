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

from django.db import models
from django.db.models.aggregates import Min, Max
from django.utils.translation import ugettext_lazy as _
from django.utils import formats, six

from lucterios.framework.models import LucteriosModel
from lucterios.framework.error import LucteriosException, IMPORTANT

from diacamma.invoice.models import Article, Bill
from diacamma.accounting.tools import format_devise
from django.core.exceptions import ObjectDoesNotExist
from lucterios.contacts.models import Individual
from datetime import date, datetime
from lucterios.CORE.parameters import Params


def convert_date(current_date):
    try:
        return datetime.strptime(current_date, "%Y-%m-%d").date()
    except TypeError:
        return None


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
    def current_season(self):
        try:
            return Season.objects.get(iscurrent=True)
        except ObjectDoesNotExist:
            raise LucteriosException(
                IMPORTANT, _('No default season define!'))

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

    class Meta(object):
        verbose_name = _('activity')
        verbose_name_plural = _('activities')


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


class Adherent(Individual):
    num = models.IntegerField(
        verbose_name=_('numeros'), null=False, default=0,)
    birthday = models.DateField(
        verbose_name=_('birthday'), default=date.today, blank=False)
    birthplace = models.CharField(_('birthplace'), max_length=50, blank=True)

    def __init__(self, *args, **kwargs):
        Individual.__init__(self, *args, **kwargs)
        self.date_ref = None

    def set_context(self, xfer):
        if xfer is not None:
            self.date_ref = convert_date(xfer.getparam("dateref"))

    @classmethod
    def get_default_fields(cls):
        fields = Individual.get_default_fields()
        fields.insert(0, "num")
        fields.append((_('license'), 'license'))
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = Individual.get_edit_fields()
        fields.insert(-1, ("birthday", "birthplace"))
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = Individual.get_show_fields()
        keys = list(fields.keys())
        fields[keys[0]][0] = ("num", fields[keys[0]][0])
        fields[keys[0]].insert(-1, ("birthday", "birthplace"))
        fields[keys[0]].insert(-1, ((_("age category"), "age_category"), ))
        fields[_('002@Subscription')] = ['subscription_set']
        fields[''] = [((_("reference date"), "dateref"), )]
        return fields

    @property
    def age_category(self):
        age_val = int((self.dateref - self.birthday).days / 365)
        ages = Age.objects.filter(
            minimum__lte=age_val, maximum__gte=age_val)
        if len(list(ages)) > 0:
            return ages[0]
        else:
            return "---"

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
        return ["season", "subscriptiontype", "begin_date", "end_date", "license_set"]

    @classmethod
    def get_edit_fields(cls):
        return ["season", "subscriptiontype"]

    @classmethod
    def get_show_fields(cls):
        return ["season", "subscriptiontype", "begin_date", "end_date", "license_set"]

    @property
    def season_query(self):
        return Season.objects.all().exclude(id__in=[sub.season_id for sub in self.adherent.subscription_set.all()])

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        is_new = self.id is None
        if is_new and (self.season not in list(self.season_query)):
            raise LucteriosException(IMPORTANT, _("Season always used!"))
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
    value = models.CharField(_('value'), max_length=50, null=True)
    team = models.ForeignKey(
        Team, verbose_name=_('team'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    activity = models.ForeignKey(
        Activity, verbose_name=_('activity'), null=True, default=None, db_index=True, on_delete=models.PROTECT)

    def __str__(self):
        return "%s [%s] %s" % (self.team, self.activity, self.value)

    @classmethod
    def get_default_fields(cls):
        return [(Params.getvalue("member-team-text"), "team"), (Params.getvalue("member-activite-text"), "activity"), "value"]

    @classmethod
    def get_edit_fields(cls):
        return [((Params.getvalue("member-team-text"), "team"),), ((Params.getvalue("member-activite-text"), "activity"),), "value"]

    @classmethod
    def get_show_fields(cls):
        return [((Params.getvalue("member-team-text"), "team"),), ((Params.getvalue("member-activite-text"), "activity"),), "value"]

    class Meta(object):
        verbose_name = _('license')
        verbose_name_plural = _('licenses')
        default_permissions = []
