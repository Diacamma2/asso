# -*- coding: utf-8 -*-
'''
diacamma.event package

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

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

from lucterios.framework.models import LucteriosModel

from diacamma.member.models import Activity, Adherent


class DegreeType(LucteriosModel):
    name = models.CharField(verbose_name=_('name'), max_length=100)
    level = models.IntegerField(verbose_name=_('level'), null=False, default=1, validators=[
                                MinValueValidator(1), MaxValueValidator(100)])
    activity = models.ForeignKey(
        Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)

    def __str__(self):
        return "[%s] %s" % (self.activity, self.name)

    @classmethod
    def get_default_fields(cls):
        return ["activity", 'name', 'level']

    @classmethod
    def get_edit_fields(cls):
        return ["activity", 'name', 'level']

    @classmethod
    def get_show_fields(cls):
        return ["activity", 'name', 'level']

    class Meta(object):
        verbose_name = _('degree type')
        verbose_name_plural = _('degree types')
        ordering = ['activity', '-level']


class SubDegreeType(LucteriosModel):
    name = models.CharField(verbose_name=_('name'), max_length=100)
    level = models.IntegerField(verbose_name=_('level'), null=False, default=1, validators=[
                                MinValueValidator(1), MaxValueValidator(100)])

    def __str__(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        return ['name', 'level']

    @classmethod
    def get_edit_fields(cls):
        return ['name', 'level']

    @classmethod
    def get_show_fields(cls):
        return ['name', 'level']

    class Meta(object):
        verbose_name = _('sub degree type')
        verbose_name_plural = _('sub degree types')
        ordering = ['-level']
        default_permissions = []


# class Participant(LucteriosModel):
#     pass
#
#
# class Organizer(LucteriosModel):
#     pass
#
#
# class Event(LucteriosModel):
#     pass


class Degree(LucteriosModel):
    adherent = models.ForeignKey(
        Adherent, verbose_name=_('adherent'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    degree = models.ForeignKey(
        DegreeType, verbose_name=_('degree'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    subdegree = models.ForeignKey(
        SubDegreeType, verbose_name=_('sub degree'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    date = models.DateField(verbose_name=_('date'), null=False)
    # event = models.ForeignKey(Event, verbose_name=_('event'), null=True, default=None, db_index=True, on_delete=models.SET_NULL)

    def __str__(self):
        return "%s %s %s" % (self.adherent, self.degree, self.subdegree)

    @classmethod
    def get_default_fields(cls):
        return ["date", 'degree', 'subdegree']

    @classmethod
    def get_edit_fields(cls):
        return ["adherent", "date", 'degree', 'subdegree']

    @classmethod
    def get_show_fields(cls):
        return ["adherent", "date", 'degree', 'subdegree']

    class Meta(object):
        verbose_name = _('degree')
        verbose_name_plural = _('degrees')
        ordering = ['-date']
