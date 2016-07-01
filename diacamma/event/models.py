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
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.utils import six

from lucterios.framework.models import LucteriosModel, get_value_converted,\
    get_value_if_choices
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual

from diacamma.member.models import Activity, Adherent, Subscription, Season
from diacamma.invoice.models import Article, Bill, Detail,\
    get_or_create_customer
from diacamma.accounting.models import Third, AccountThird, CostAccounting
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
from lucterios.framework.signal_and_lock import Signal
from lucterios.CORE.models import Parameter
from django_fsm import transition, FSMIntegerField


class DegreeType(LucteriosModel):
    name = models.CharField(verbose_name=_('name'), max_length=100)
    level = models.IntegerField(verbose_name=_('level'), null=False, default=1, validators=[
                                MinValueValidator(1), MaxValueValidator(100)])
    activity = models.ForeignKey(
        Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)

    def __str__(self):
        if Params.getvalue("member-activite-enable"):
            return "[%s] %s" % (self.activity, self.name)
        else:
            return self.name

    def get_text_value(self):
        return self.name

    @classmethod
    def get_default_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [(Params.getvalue("member-activite-text"), "activity"), 'name', 'level']
        else:
            return ['name', 'level']

    @classmethod
    def get_edit_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [((Params.getvalue("member-activite-text"), "activity"),), 'name', 'level']
        else:
            return ['name', 'level']

    @classmethod
    def get_show_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [((Params.getvalue("member-activite-text"), "activity"),), 'name', 'level']
        else:
            return ['name', 'level']

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


class Event(LucteriosModel):
    activity = models.ForeignKey(Activity, verbose_name=_(
        'activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    date = models.DateField(verbose_name=_('date'), null=False)
    comment = models.TextField(_('comment'), blank=False)
    status = FSMIntegerField(verbose_name=_('status'), choices=(
        (0, _('building')), (1, _('valid'))), null=False, default=0, db_index=True)
    event_type = models.IntegerField(verbose_name=_('event type'), choices=(
        (0, _('examination')), (1, _('trainning/outing'))), null=False, default=0, db_index=True)
    date_end = models.DateField(verbose_name=_('end date'), null=True)
    default_article = models.ForeignKey(Article, verbose_name=_(
        'default article'), null=True, default=None, on_delete=models.PROTECT)

    def __str__(self):
        if Params.getvalue("member-activite-enable"):
            return "%s %s" % (self.activity, self.date)
        else:
            return six.text_type(self.date)

    @classmethod
    def get_default_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [(Params.getvalue("member-activite-text"), "activity"), 'status', 'event_type', ('date', 'date_txt'), 'comment']
        else:
            return ['status', 'event_type', ('date', 'date_txt'), 'comment']

    @classmethod
    def get_edit_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [((Params.getvalue("member-activite-text"), "activity"),), 'status', 'event_type', 'date', 'date_end', 'default_article', 'comment']
        else:
            return ['status', 'event_type', 'date', 'date_end', 'default_article', 'comment']

    @classmethod
    def get_show_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [('date', 'date_end'), ('status', (Params.getvalue("member-activite-text"), "activity")), 'organizer_set', 'participant_set', ('comment',), (('default_article', 'default_article.ref_price'), )]
        else:
            return [('date', 'date_end'), ('status',), 'organizer_set', 'participant_set', ('comment',), (('default_article', 'default_article.ref_price'), )]

    @classmethod
    def get_search_fields(cls):
        return ['status', 'event_type', 'date', 'date_end', 'comment']

    @property
    def event_type_txt(self):
        return get_value_if_choices(self.event_type, self._meta.get_field('event_type'))

    @property
    def date_txt(self):
        if self.event_type == 0:
            return get_value_converted(self.date)
        else:
            return "%s -> %s" % (get_value_converted(self.date), get_value_converted(self.date_end))

    def can_delete(self):
        if self.status > 0:
            return _('%s validated!') % self.event_type_txt
        return ''

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.event_type == 0:
            self.date_end = None
        elif (self.date_end is None) or (self.date_end < self.date):
            self.date_end = self.date
        return LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def chech_validity(self):
        msg = ''
        if self.status > 0:
            msg = _('%s validated!') % get_value_if_choices(
                self.event_type, self._meta.get_field('event_type'))
        elif len(self.organizer_set.filter(isresponsible=True)) == 0:
            msg = _('no responsible!')
        elif len(self.participant_set.all()) == 0:
            msg = _('no participant!')
        return msg

    def can_be_valid(self):
        msg = self.chech_validity()
        if msg != '':
            raise LucteriosException(IMPORTANT, msg)

    transitionname__validate = _("Validation")

    @transition(field=status, source=0, target=1, conditions=[lambda item:item.chech_validity() == ''])
    def validate(self):
        for participant in self.participant_set.all():
            participant.give_result(self.xfer.getparam('degree_%d' % participant.id, 0),
                                    self.xfer.getparam('subdegree_%d' % participant.id, 0),
                                    self.xfer.getparam('comment_%d' % participant.id, ''))
            participant.create_bill()

    class Meta(object):
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-date']


class Organizer(LucteriosModel):
    event = models.ForeignKey(
        Event, verbose_name=_('event'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    contact = models.ForeignKey(
        Individual, verbose_name=_('contact'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    isresponsible = models.BooleanField(
        verbose_name=_('responsible'), default=False)

    def __str__(self):
        return self.contact

    def set_has_responsible(self):
        all_organizer = Organizer.objects.filter(event=self.event)
        for organizer_item in all_organizer:
            organizer_item.isresponsible = False
            organizer_item.save()
        self.isresponsible = True
        self.save()

    @classmethod
    def get_default_fields(cls):
        return ["contact", 'isresponsible']

    @classmethod
    def get_edit_fields(cls):
        return ["contact", 'isresponsible']

    @classmethod
    def get_show_fields(cls):
        return ["contact", 'isresponsible']

    def can_delete(self):
        if self.event.status > 0:
            return _('examination validated!')
        return ''

    class Meta(object):
        verbose_name = _('organizer')
        verbose_name_plural = _('organizers')
        default_permissions = []


class Degree(LucteriosModel):
    adherent = models.ForeignKey(
        Adherent, verbose_name=_('adherent'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    degree = models.ForeignKey(
        DegreeType, verbose_name=_('degree'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    subdegree = models.ForeignKey(
        SubDegreeType, verbose_name=_('sub degree'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    date = models.DateField(verbose_name=_('date'), null=False)
    event = models.ForeignKey(Event, verbose_name=_(
        'event'), null=True, default=None, db_index=True, on_delete=models.SET_NULL)

    def __str__(self):
        if (self.subdegree is None) or (Params.getvalue("event-subdegree-enable") == 0):
            return six.text_type(self.degree)
        else:
            return "%s %s" % (self.degree, self.subdegree)

    def get_text(self):
        if (self.subdegree is None) or (Params.getvalue("event-subdegree-enable") == 0):
            return six.text_type(self.degree.name)
        else:
            return "%s %s" % (self.degree.name, self.subdegree.name)

    @classmethod
    def get_default_fields(cls):
        fields = ["date", (Params.getvalue("event-degree-text"), 'degree')]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append(
                (Params.getvalue("event-subdegree-text"), 'subdegree'))
        return fields

    @classmethod
    def get_edit_fields(cls):
        fields = [
            "adherent", "date", ((Params.getvalue("event-degree-text"), 'degree'),)]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append(
                ((Params.getvalue("event-subdegree-text"), 'subdegree'),))
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = [
            "adherent", "date", ((Params.getvalue("event-degree-text"), 'degree'),)]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append(
                ((Params.getvalue("event-subdegree-text"), 'subdegree'),))
        return fields

    @classmethod
    def get_statistic(cls, season):
        def sort_fct(item):
            if item[1][1] is None:
                return item[1][0].level * 100000
            else:
                return item[1][0].level * 100000 + item[1][1].level
        static_res = []
        for activity in Activity.objects.all():
            degree_activity = {}
            for degree in Degree.objects.filter(date__gte=season.begin_date, date__lte=season.end_date, degree__activity=activity):
                if degree.get_text() not in degree_activity.keys():
                    degree_activity[
                        degree.get_text()] = [degree.degree, degree.subdegree, 0]
                degree_activity[degree.get_text()][2] += 1
            result_activity = []
            for item in sorted(degree_activity.items(), key=lambda item: sort_fct(item), reverse=True):
                result_activity.append((item[0], item[1][2]))
            if Params.getvalue("member-activite-enable"):
                static_res.append((activity, result_activity))
            else:
                static_res.append((None, result_activity))
        return static_res

    def can_delete(self):
        if not (self.event is None):
            return _('examination validated!')
        return ''

    class Meta(object):
        verbose_name = _('degree')
        verbose_name_plural = _('degrees')
        ordering = ['-date']


class Participant(LucteriosModel):
    event = models.ForeignKey(
        Event, verbose_name=_('event'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    contact = models.ForeignKey(
        Individual, verbose_name=_('contact'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    degree_result = models.ForeignKey(
        DegreeType, verbose_name=_('degree result'), null=True, default=None, db_index=True, on_delete=models.CASCADE)
    subdegree_result = models.ForeignKey(
        SubDegreeType, verbose_name=_('sub-degree result'), null=True, default=None, db_index=True, on_delete=models.CASCADE)
    comment = models.TextField(_('comment'), blank=True)
    article = models.ForeignKey(Article, verbose_name=_(
        'article'), null=True, default=None, on_delete=models.PROTECT)
    bill = models.ForeignKey(Bill, verbose_name=_(
        'bill'), null=True, default=None, on_delete=models.SET_NULL)

    def __str__(self):
        return six.text_type(self.contact)

    @classmethod
    def get_default_fields(cls):
        fields = ["contact", (_('subscript?'), 'is_subscripter'), (_('current'), 'current_degree'), (_(
            '%s result') % Params.getvalue("event-degree-text"), 'degree_result_simple')]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append(
                (_('%s result') % Params.getvalue("event-subdegree-text"), 'subdegree_result'))
        fields.append((_('article'), 'article.ref_price'))
        fields.append('comment')
        return fields

    @classmethod
    def get_edit_fields(cls):
        return ["contact", 'comment', 'article']

    @classmethod
    def get_show_fields(cls):
        return ["contact", 'degree_result', 'subdegree_result', 'comment', 'article']

    def get_current_degree(self):
        degree_list = Degree.objects.filter(
            Q(adherent_id=self.contact_id) & Q(degree__activity=self.event.activity)).order_by('-degree__level', '-subdegree__level')
        if len(degree_list) > 0:
            return degree_list[0]
        else:
            return None

    @property
    def current_degree(self):
        degree = self.get_current_degree()
        if degree is not None:
            return degree.get_text()
        else:
            return ""

    @property
    def degree_result_simple(self):
        if self.degree_result is not None:
            return self.degree_result.name
        else:
            return None

    @property
    def is_subscripter(self):
        return len(Subscription.objects.filter(adherent_id=self.contact_id, season=Season.get_from_date(self.event.date))) > 0

    def allow_degree(self):
        degree = self.get_current_degree()
        if degree is not None:
            return DegreeType.objects.filter(level__gte=degree.degree.level, activity=self.event.activity).order_by('level')
        else:
            return DegreeType.objects.filter(activity=self.event.activity).order_by('level')

    def allow_subdegree(self):
        return SubDegreeType.objects.all().order_by('level')

    def give_result(self, degree, subdegree, comment):
        self.degree_result_id = degree
        if self.degree_result_id == 0:
            self.degree_result_id = None
        self.subdegree_result_id = subdegree
        if self.subdegree_result_id == 0:
            self.subdegree_result_id = None
        if (self.degree_result_id is None) and not (self.subdegree_result_id is None):
            old_degree = self.get_current_degree()
            self.degree_result = old_degree.degree
        self.comment = comment
        self.save()
        if not (self.degree_result is None):
            try:
                adh = Adherent.objects.get(id=self.contact_id)
                Degree.objects.create(adherent=adh, degree=self.degree_result,
                                      subdegree=self.subdegree_result, date=self.event.date, event=self.event)
            except:
                pass

    def create_bill(self):
        if self.bill is not None:
            self.bill.delete()
            self.bill = None
            self.save()
        if self.article is not None:
            self.bill = Bill.objects.create(
                bill_type=1, date=date.today(), third=get_or_create_customer(self.contact_id))
            cost_acc = CostAccounting.objects.filter(is_default=True)
            if len(cost_acc) > 0:
                self.bill.cost_accounting = cost_acc[0]
            self.bill.comment = "{[b]}%s{[/b]}: %s" % (
                self.event.event_type_txt, self.event.date_txt)
            self.bill.save()
            Detail.create_for_bill(self.bill, self.article)
            self.save()

    def can_delete(self):
        if self.event.status > 0:
            return _('%s validated!') % self.event.event_type_txt
        if self.bill is not None:
            return self.bill.can_delete()
        return ''

    def delete(self, using=None):
        if self.bill is not None:
            self.bill.delete()
        LucteriosModel.delete(self, using=using)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if (self.id is None) and (self.event.event_type == 0) and ((self.comment is None) or (self.comment == '')):
            self.comment = Params.getvalue("event-comment-text")
        if (self.id is None) and (self.event.default_article is not None):
            self.article = self.event.default_article
        return LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta(object):
        verbose_name = _('participant')
        verbose_name_plural = _('participants')
        default_permissions = []


@Signal.decorate('checkparam')
def event_checkparam():
    Parameter.check_and_create(name="event-subdegree-enable", typeparam=3, title=_("event-subdegree-enable"),
                               args="{}", value='True')

    Parameter.check_and_create(name="event-degree-text", typeparam=0, title=_("event-degree-text"),
                               args="{'Multi':False}", value=_('Degree'))

    Parameter.check_and_create(name="event-subdegree-text", typeparam=0, title=_("event-subdegree-text"),
                               args="{'Multi':False}", value=_('Sub-degree'))

    Parameter.check_and_create(name="event-comment-text", typeparam=0,
                               title=_("event-comment-text"), args="{'Multi':True}", value='')
