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
from django.utils import formats

from lucterios.framework.models import LucteriosModel
from lucterios.framework.error import LucteriosException, IMPORTANT

from diacamma.invoice.models import Article
from diacamma.accounting.tools import format_devise


class Season(LucteriosModel):
    designation = models.CharField(_('designation'), max_length=100)
    iscurrent = models.BooleanField(verbose_name=_('is current'), default=True)

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

    @property
    def begin_date(self):
        val = self.period_set.all().aggregate(Min('begin_date'))
        if 'begin_date__min' in val.keys():
            return val['begin_date__min']
        else:
            return "---"

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

    @classmethod
    def get_default_fields(cls):
        return ["name"]

    @classmethod
    def get_edit_fields(cls):
        return ["name"]

    @classmethod
    def get_show_fields(cls):
        return ["season", "name"]

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
            raise LucteriosException(
                IMPORTANT, _("date invalid!") + " %s->%s" % (self.begin_date, self.end_date))
        LucteriosModel.save(self, force_insert=force_insert,
                            force_update=force_update, using=using, update_fields=update_fields)
        if refresh_num:
            self.season.refresh_periodnum()

    class Meta(object):
        verbose_name = _('period')
        verbose_name_plural = _('periods')
        ordering = ['num']
        default_permissions = []


class Subscription(LucteriosModel):
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, default="")
    duration = models.IntegerField(verbose_name=_('duration'), choices=((0, _('annually')), (1, _(
        'periodic')), (2, _('monthly')), (3, _('calendar'))), null=False, default=0, db_index=True)
    unactive = models.BooleanField(verbose_name=_('unactive'), default=True)
    articles = models.ManyToManyField(
        Article, verbose_name=_('articles'), blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ["name", "description", 'duration', (_('price'), 'price')]

    @classmethod
    def get_edit_fields(cls):
        return ["name", "description", 'duration', 'articles']

    @classmethod
    def get_show_fields(cls):
        return ["name", "description", 'duration', 'unactive', ((_('price'), 'price'),)]

    @property
    def price(self):
        total_price = 0
        for art in self.articles.all():
            total_price += art.price
        return format_devise(total_price, 5)

    class Meta(object):
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
