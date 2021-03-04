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
from datetime import date

from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Count
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition, FSMIntegerField

from lucterios.framework.models import LucteriosModel
from lucterios.framework.model_fields import get_value_if_choices, LucteriosVirtualField
from lucterios.framework.tools import get_date_formating
from lucterios.framework.error import LucteriosException, IMPORTANT
from lucterios.framework.signal_and_lock import Signal
from lucterios.framework.auditlog import auditlog
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params
from lucterios.contacts.models import Individual

from diacamma.invoice.models import Article, Bill, Detail, get_or_create_customer
from diacamma.accounting.models import CostAccounting
from diacamma.member.models import Activity, Adherent, Subscription, Season
from diacamma.accounting.tools import get_amount_from_format_devise


class DegreeType(LucteriosModel):
    name = models.CharField(verbose_name=_('name'), max_length=100)
    level = models.IntegerField(verbose_name=_('level'), null=False, default=1,
                                validators=[MinValueValidator(1), MaxValueValidator(100)])
    activity = models.ForeignKey(Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)

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
    level = models.IntegerField(verbose_name=_('level'), null=False, default=1,
                                validators=[MinValueValidator(1), MaxValueValidator(100)])

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
    EVENTTYPE_EXAMINATION = 0
    EVENTTYPE_TRAINING = 1
    LIST_EVENTTYPES = ((EVENTTYPE_EXAMINATION, _('examination')), (EVENTTYPE_TRAINING, _('trainning/outing')))

    STATUS_BUILDING = 0
    STATUS_VALID = 1
    LIST_STATUS = ((STATUS_BUILDING, _('building event')), (STATUS_VALID, _('valid event')))

    activity = models.ForeignKey(Activity, verbose_name=_('activity'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    date = models.DateField(verbose_name=_('date'), null=False)
    comment = models.TextField(_('comment'), blank=False)
    status = FSMIntegerField(verbose_name=_('status'), choices=LIST_STATUS, null=False, default=STATUS_BUILDING, db_index=True)
    event_type = models.IntegerField(verbose_name=_('event type'), choices=LIST_EVENTTYPES, null=False, default=EVENTTYPE_EXAMINATION, db_index=True)
    date_end = models.DateField(verbose_name=_('end date'), null=True)
    default_article = models.ForeignKey(Article, verbose_name=_('default article (member)'), related_name="event", null=True, default=None, on_delete=models.PROTECT)
    default_article_nomember = models.ForeignKey(Article, verbose_name=_('default article (no member)'), related_name="eventnomember", null=True, default=None, on_delete=models.PROTECT)
    cost_accounting = models.ForeignKey(CostAccounting, verbose_name=_('cost accounting'), null=True, default=None, db_index=True, on_delete=models.PROTECT)

    date_txt = LucteriosVirtualField(verbose_name=_('date'), compute_from='get_date_txt')

    def __str__(self):
        if Params.getvalue("member-activite-enable"):
            return "%s %s" % (self.activity, self.date)
        else:
            return str(self.date)

    @classmethod
    def get_default_fields(cls):
        if Params.getvalue("member-activite-enable"):
            return [(Params.getvalue("member-activite-text"), "activity"), 'status', 'event_type', 'date_txt', 'comment']
        else:
            return ['status', 'event_type', ('date', 'date_txt'), 'comment']

    @classmethod
    def get_edit_fields(cls):
        field = []
        if Params.getvalue("member-activite-enable"):
            field.append(((Params.getvalue("member-activite-text"), "activity"),))
        field.extend(['status', 'event_type', 'date', 'date_end', 'default_article', 'default_article_nomember', 'comment'])
        return field

    @classmethod
    def get_show_fields(cls):
        field = [('date', 'date_end')]
        if Params.getvalue("member-activite-enable"):
            field.append(('status', (Params.getvalue("member-activite-text"), "activity")))
        else:
            field.append(('status', ))
        field.extend(['organizer_set', 'participant_set', ('comment',), ((_('default article (member)'), 'default_article.ref_price'), (_('default article (no member)'), 'default_article_nomember.ref_price'))])
        return field

    @classmethod
    def get_search_fields(cls):
        return ['status', 'event_type', 'date', 'date_end', 'comment']

    @property
    def event_type_txt(self):
        return get_value_if_choices(self.event_type, self._meta.get_field('event_type'))

    def get_date_txt(self):
        if self.event_type == self.EVENTTYPE_EXAMINATION:
            return get_date_formating(self.date)
        else:
            return "%s -> %s" % (get_date_formating(self.date), get_date_formating(self.date_end))

    def can_delete(self):
        if self.status != self.STATUS_BUILDING:
            return _('%s validated!') % self.event_type_txt
        return ''

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.event_type == self.EVENTTYPE_EXAMINATION:
            self.date_end = None
        elif (self.date_end is None) or (self.date_end < self.date):
            self.date_end = self.date
        return LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def chech_validity(self):
        msg = ''
        if self.status != self.STATUS_BUILDING:
            msg = _('%s validated!') % get_value_if_choices(self.event_type, self._meta.get_field('event_type'))
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

    @transition(field=status, source=STATUS_BUILDING, target=STATUS_VALID, conditions=[lambda item:item.chech_validity() == ''])
    def validate(self):
        for participant in self.participant_set.all():
            participant.give_result(self.xfer.getparam('degree_%d' % participant.id, 0),
                                    self.xfer.getparam('subdegree_%d' % participant.id, 0),
                                    self.xfer.getparam('comment_%d' % participant.id))
            participant.create_bill()

    class Meta(object):
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-date']


class Organizer(LucteriosModel):
    event = models.ForeignKey(Event, verbose_name=_('event'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    contact = models.ForeignKey(Individual, verbose_name=_('contact'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    isresponsible = models.BooleanField(verbose_name=_('responsible'), default=False)

    def __str__(self):
        return self.contact

    def get_auditlog_object(self):
        return self.event

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
        if self.event.status != Event.STATUS_BUILDING:
            return _('examination validated!')
        return ''

    class Meta(object):
        verbose_name = _('organizer')
        verbose_name_plural = _('organizers')
        default_permissions = []


class Degree(LucteriosModel):
    adherent = models.ForeignKey(Adherent, verbose_name=_('adherent'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    degree = models.ForeignKey(DegreeType, verbose_name=_('degree'), null=False, default=None, db_index=True, on_delete=models.PROTECT)
    subdegree = models.ForeignKey(SubDegreeType, verbose_name=_('sub degree'), null=True, default=None, db_index=True, on_delete=models.PROTECT)
    date = models.DateField(verbose_name=_('date'), null=False)
    event = models.ForeignKey(Event, verbose_name=_('event'), null=True, default=None, db_index=True, on_delete=models.SET_NULL)

    def __str__(self):
        if (self.subdegree is None) or (Params.getvalue("event-subdegree-enable") == 0):
            return str(self.degree)
        else:
            return "%s %s" % (self.degree, self.subdegree)

    def get_text(self):
        if (self.subdegree is None) or (Params.getvalue("event-subdegree-enable") == 0):
            return str(self.degree.name)
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
        fields = ["adherent", "date", ((Params.getvalue("event-degree-text"), 'degree'),)]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append(
                ((Params.getvalue("event-subdegree-text"), 'subdegree'),))
        return fields

    @classmethod
    def get_show_fields(cls):
        fields = ["adherent", "date", ((Params.getvalue("event-degree-text"), 'degree'),)]
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
            for degree in Degree.objects.filter(date__gte=season.begin_date, date__lte=season.end_date, degree__activity=activity).distinct():
                if degree.get_text() not in degree_activity.keys():
                    degree_activity[degree.get_text()] = [degree.degree, degree.subdegree, 0]
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
    event = models.ForeignKey(Event, verbose_name=_('event'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    contact = models.ForeignKey(Individual, verbose_name=_('contact'), null=False, default=None, db_index=True, on_delete=models.CASCADE)
    degree_result = models.ForeignKey(DegreeType, verbose_name=_('degree result'), null=True, default=None, db_index=True, on_delete=models.CASCADE)
    subdegree_result = models.ForeignKey(SubDegreeType, verbose_name=_('sub-degree result'), null=True, default=None, db_index=True, on_delete=models.CASCADE)
    comment = models.TextField(_('comment'), blank=True)
    article = models.ForeignKey(Article, verbose_name=_('article'), null=True, default=None, on_delete=models.PROTECT)
    reduce = models.DecimalField(verbose_name=_('reduce'), max_digits=10, decimal_places=3,
                                 default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(9999999.999)])
    bill = models.ForeignKey(Bill, verbose_name=_('bill'), null=True, default=None, on_delete=models.SET_NULL)

    is_subscripter = LucteriosVirtualField(verbose_name=_('subscript?'), compute_from='get_is_subscripter', format_string='B')
    current_degree = LucteriosVirtualField(verbose_name=_('current'), compute_from='get_current_degree')
    article_ref_price = LucteriosVirtualField(verbose_name=_('article'), compute_from='get_article_ref_price')

    def __str__(self):
        return str(self.contact)

    def get_auditlog_object(self):
        return self.event

    @classmethod
    def get_default_fields(cls):
        fields = ["contact", 'is_subscripter', 'current_degree', (_('%s result') % Params.getvalue("event-degree-text"), 'degree_result_simple')]
        if Params.getvalue("event-subdegree-enable") == 1:
            fields.append((_('%s result') % Params.getvalue("event-subdegree-text"), 'subdegree_result'))
        fields.append('article_ref_price')
        fields.append('comment')
        return fields

    @classmethod
    def get_edit_fields(cls):
        return ["contact", 'comment', 'article', 'reduce']

    @classmethod
    def get_show_fields(cls):
        return ["contact", 'degree_result', 'subdegree_result', 'comment', 'article', 'reduce']

    def get_article_ref_price(self):
        if self.article_id is None:
            return None
        elif abs(float(self.reduce)) > 0.0001:
            return "%s (-%s)" % (self.article.ref_price, get_amount_from_format_devise(float(self.reduce), 7))
        else:
            return self.article.ref_price

    def get_current_degree_ex(self):
        degree_list = Degree.objects.filter(Q(adherent_id=self.contact_id) & Q(degree__activity=self.event.activity)).distinct().order_by('-degree__level', '-subdegree__level')
        if len(degree_list) > 0:
            return degree_list[0]
        else:
            return None

    def get_current_degree(self):
        degree = self.get_current_degree_ex()
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

    def get_is_subscripter(self):
        return len(Subscription.objects.filter(adherent_id=self.contact_id, season=Season.get_from_date(self.event.date))) > 0

    def allow_degree(self):
        degree = self.get_current_degree_ex()
        if degree is not None:
            return DegreeType.objects.filter(level__gte=degree.degree.level, activity=self.event.activity).distinct().order_by('level')
        else:
            return DegreeType.objects.filter(activity=self.event.activity).distinct().order_by('level')

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
        if comment is not None:
            self.comment = comment
        self.save()
        if not (self.degree_result is None):
            try:
                adh = Adherent.objects.get(id=self.contact_id)
                Degree.objects.create(adherent=adh, degree=self.degree_result,
                                      subdegree=self.subdegree_result, date=self.event.date, event=self.event)
            except Exception:
                pass

    def _search_or_create_bill(self):
        high_contact = self.contact.get_final_child()
        new_third = get_or_create_customer(high_contact.get_ref_contact().id)
        bill_list = Bill.objects.filter(third=new_third, bill_type=Bill.BILLTYPE_BILL, status=Bill.STATUS_BUILDING).annotate(participant_count=Count('participant')).filter(participant_count__gte=1).order_by('-date')
        if len(bill_list) > 0:
            self.bill = bill_list[0]
        if self.bill is None:
            self.bill = Bill.objects.create(bill_type=1, date=date.today(), third=new_third)
        return high_contact

    def create_bill(self):
        if self.article is not None:
            high_contact = self._search_or_create_bill()
            bill_comment = ["{[b]}%s{[/b]}: %s" % (self.event.event_type_txt, self.event.date_txt)]
            bill_comment.append("{[i]}%s{[/i]}" % self.event.comment)
            if (self.bill.third.contact.id == high_contact.id) and (self.event.event_type == Event.EVENTTYPE_TRAINING) and (self.comment is not None) and (self.comment != ''):
                bill_comment.append(self.comment)
            self.bill.comment = "{[br/]}".join(bill_comment)
            self.bill.save()
            self.bill.detail_set.all().delete()
            participant_list = list(self.bill.participant_set.all())
            if self not in participant_list:
                participant_list.append(self)
            for participant in participant_list:
                detail_comment = [participant.article.designation]
                if participant.bill.third.contact.id != participant.contact.id:
                    detail_comment.append(_("Participant: %s") % str(participant.contact))
                    if (participant.event.event_type == 1) and (participant.comment is not None) and (participant.comment != ''):
                        detail_comment.append(participant.comment)
                Detail.create_for_bill(participant.bill, participant.article, reduce=participant.reduce, designation="{[br/]}".join(detail_comment))
            self.save()

    def can_delete(self):
        if self.event.status != Event.STATUS_BUILDING:
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
        if (self.id is None) and (self.event.event_type == Event.EVENTTYPE_EXAMINATION) and ((self.comment is None) or (self.comment == '')):
            self.comment = Params.getvalue("event-comment-text")
        if (self.id is None) and self.is_subscripter and (self.event.default_article is not None):
            self.article = self.event.default_article
        if (self.id is None) and not self.is_subscripter and (self.event.default_article_nomember is not None):
            self.article = self.event.default_article_nomember
        return LucteriosModel.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta(object):
        verbose_name = _('participant')
        verbose_name_plural = _('participants')
        default_permissions = []


@Signal.decorate('checkparam')
def event_checkparam():
    Parameter.check_and_create(name="event-degree-enable", typeparam=3, title=_("event-degree-enable"),
                               args="{}", value='True')
    Parameter.check_and_create(name="event-subdegree-enable", typeparam=3, title=_("event-subdegree-enable"),
                               args="{}", value='True')
    Parameter.check_and_create(name="event-degree-text", typeparam=0, title=_("event-degree-text"),
                               args="{'Multi':False}", value=_('Degree'))
    Parameter.check_and_create(name="event-subdegree-text", typeparam=0, title=_("event-subdegree-text"),
                               args="{'Multi':False}", value=_('Sub-degree'))
    Parameter.check_and_create(name="event-comment-text", typeparam=0,
                               title=_("event-comment-text"), args="{'Multi':True}", value='')


@Signal.decorate('auditlog_register')
def event_auditlog_register():
    auditlog.register(DegreeType, exclude_fields=['ID'])
    auditlog.register(SubDegreeType, exclude_fields=['ID'])
    auditlog.register(Event, include_fields=['activity', 'status', 'event_type', 'date_txt', 'default_article',
                                             'default_article_nomember', 'comment'])
    auditlog.register(Organizer, exclude_fields=['ID'])
    auditlog.register(Participant, include_fields=["contact", 'degree_result', 'subdegree_result', 'comment', 'article', 'reduce'])
    auditlog.register(Degree, exclude_fields=['ID'])
