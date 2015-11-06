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
from datetime import datetime, timedelta
from calendar import monthrange

from django.db.models.aggregates import Max
from django.utils.translation import ugettext_lazy as _

from lucterios.framework.editors import LucteriosEditor
from lucterios.framework.xfercomponents import XferCompLabelForm, XferCompDate, XferCompGrid
from lucterios.framework.error import LucteriosException, IMPORTANT

from diacamma.member.models import Period, Season


class SeasonEditor(LucteriosEditor):

    def before_save(self, xfer):
        date = xfer.getparam('begin_date')
        if date is None:
            raise LucteriosException(IMPORTANT, _("date invalid!"))
        date = datetime.strptime(date, "%Y-%m-%d")
        new_season = "%d/%d" % (date.year, date.year + 1)
        if len(Season.objects.filter(designation=new_season)) > 0:
            raise LucteriosException(IMPORTANT, _("Season exists yet!"))
        self.item.designation = new_season
        self.item.iscurrent = False

    def saving(self, xfer):
        def same_day_months_after(start_date, months=1):
            target_year = start_date.year + \
                int((start_date.month - 1 + months) / 12)
            target_month = (start_date.month - 1 + months) % 12 + 1
            num_days_target_month = monthrange(
                target_year, target_month)[1]
            return start_date.replace(year=target_year, month=target_month,
                                      day=min(start_date.day, num_days_target_month))
        if not xfer.has_changed:
            self.before_save(xfer)
            self.item.save()
        date = datetime.strptime(xfer.getparam('begin_date'), "%Y-%m-%d")
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
