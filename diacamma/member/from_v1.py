# -*- coding: utf-8 -*-
'''
from_v1 module for accounting

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
import sys

from django.apps import apps
from django.utils import six

from lucterios.install.lucterios_migration import MigrateAbstract


class MemberMigrate(MigrateAbstract):

    def __init__(self, old_db):
        MigrateAbstract.__init__(self, old_db)
        self.season_list = {}
        self.period_list = {}

    def _season(self):
        season_mdl = apps.get_model("member", "Season")
        season_mdl.objects.all().delete()
        self.season_list = {}
        period_mdl = apps.get_model("member", "Period")
        period_mdl.objects.all().delete()
        self.period_list = {}
        cur_s = self.old_db.open()
        cur_s.execute(
            "SELECT id, designation,docNeed,courant FROM fr_sdlibre_membres_saisons")
        for seasonid, designation, doc_need, courant in cur_s.fetchall():
            self.print_log("=> SEASON %s", (designation,))
            self.season_list[seasonid] = season_mdl.objects.create(
                designation=designation, iscurrent=courant == 'o', doc_need=doc_need)
        cur_p = self.old_db.open()
        cur_p.execute(
            "SELECT id, saison,num,begin,end  FROM fr_sdlibre_membres_periodSaisons")
        for periodid, saison, num, begin, end in cur_p.fetchall():
            if saison in self.season_list.keys():
                self.print_log("=> PERIOD %s %d", (saison, num))
                self.period_list[periodid] = period_mdl.objects.create(
                    season=self.season_list[saison], num=num, begin_date=begin, end_date=end)

    def _subscription(self):
        article_mdl = apps.get_model("invoice", "Article")
        subscription_mdl = apps.get_model("member", "Subscription")
        subscription_mdl.objects.all().delete()
        self.subscription_list = {}

        cur_s = self.old_db.open()
        cur_s.execute(
            "SELECT id,nom,description,duration,noactive FROM fr_sdlibre_membres_typeCotisations")
        for subid, nom, description, duration, noactive in cur_s.fetchall():
            self.print_log(
                "=> SUBSCRIPTION:%s", (nom,))
            self.subscription_list[subid] = subscription_mdl.objects.create(
                name=nom, description=description, duration=duration, unactive=noactive == 'o')
            ids = []
            artcur = self.old_db.open()
            artcur.execute(
                'SELECT article FROM fr_sdlibre_membres_cotisationArticles WHERE typeCotisation=%d' % subid)
            for article, in artcur.fetchall():
                if article in self.old_db.objectlinks['article'].keys():
                    ids.append(self.old_db.objectlinks['article'][article].pk)
            self.subscription_list[
                subid].articles = article_mdl.objects.filter(id__in=ids)
            self.subscription_list[subid].save()

    def _params(self):
        pass

    def run(self):
        try:
            self._params()
            self._season()
            self._subscription()
        except:
            import traceback
            traceback.print_exc()
            six.print_("*** Unexpected error: %s ****" % sys.exc_info()[0])
