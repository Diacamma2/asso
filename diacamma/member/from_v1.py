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
from diacamma.accounting.from_v1 import convert_code
from lucterios.CORE.models import Parameter


class MemberMigrate(MigrateAbstract):

    def __init__(self, old_db):
        MigrateAbstract.__init__(self, old_db)
        self.season_list = {}
        self.period_list = {}
        self.doc_list = {}
        self.age_list = {}
        self.team_list = {}
        self.activity_list = {}

    def _season(self):
        season_mdl = apps.get_model("member", "Season")
        season_mdl.objects.all().delete()
        self.season_list = {}
        period_mdl = apps.get_model("member", "Period")
        period_mdl.objects.all().delete()
        self.period_list = {}
        doc_mdl = apps.get_model("member", "Document")
        doc_mdl.objects.all().delete()
        self.doc_list = {}
        cur_s = self.old_db.open()
        cur_s.execute(
            "SELECT id, designation,docNeed,courant FROM fr_sdlibre_membres_saisons")
        for seasonid, designation, doc_need, courant in cur_s.fetchall():
            self.print_log("=> SEASON %s", (designation,))
            self.season_list[seasonid] = season_mdl.objects.create(
                designation=designation, iscurrent=courant == 'o')
            if doc_need is not None:
                doc_idx = 0
                for doc_item in doc_need.split('|'):
                    if doc_item != '':
                        self.doc_list["%d_%d" % (seasonid, doc_idx)] = doc_mdl.objects.create(
                            season=self.season_list[seasonid], name=doc_item)
                    doc_idx += 1
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

    def _categories(self):
        age_mdl = apps.get_model("member", "Age")
        age_mdl.objects.all().delete()
        self.age_list = {}
        team_mdl = apps.get_model("member", "Team")
        team_mdl.objects.all().delete()
        self.team_list = {}
        activity_mdl = apps.get_model("member", "Activity")
        activity_mdl.objects.all().delete()
        self.activity_list = {}

        cur_a = self.old_db.open()
        cur_a.execute(
            "SELECT id,nom,ageMin,ageMax  FROM fr_sdlibre_membres_ages")
        for ageid, nom, age_min, age_max in cur_a.fetchall():
            self.print_log(
                "=> Age:%s", (nom,))
            self.age_list[ageid] = age_mdl.objects.create(
                name=nom, minimum=age_min, maximum=age_max)
        cur_t = self.old_db.open()
        cur_t.execute(
            "SELECT id,nom, description, noactive FROM fr_sdlibre_membres_equipes")
        for teamid, nom, description, noactive in cur_t.fetchall():
            self.print_log(
                "=> Team:%s", (nom,))
            self.team_list[teamid] = team_mdl.objects.create(
                name=nom, description=description, unactive=noactive == 'o')
        cur_y = self.old_db.open()
        cur_y.execute(
            "SELECT id,nom, description FROM fr_sdlibre_membres_activite")
        for activityid, nom, description in cur_y.fetchall():
            self.print_log(
                "=> Activity:%s", (nom,))
            self.activity_list[activityid] = activity_mdl.objects.create(
                name=nom, description=description)

    def _params(self):
        cur_p = self.old_db.open()
        cur_p.execute(
            "SELECT paramName,value FROM CORE_extension_params WHERE extensionId LIKE 'fr_sdlibre_membres' and paramName in ('EquipeEnable', 'EquipeText', 'ActiviteEnable', 'ActiviteText', 'AgeEnable', 'LicenceEnabled', 'FiltreGenre', 'Numero', 'Naissance', 'compteTiersDefault', 'connexion')")
        for param_name, param_value in cur_p.fetchall():
            pname = ''
            if param_name == "EquipeEnable":
                pname = "member-team-enable"
            if param_name == "EquipeText":
                pname = "member-team-text"
            if param_name == "ActiviteEnable":
                pname = "member-activite-enable"
            if param_name == "ActiviteText":
                pname = "member-activite-text"
            if param_name == "AgeEnable":
                pname = "member-age-enable"
            if param_name == "LicenceEnabled":
                pname = "member-licence-enabled"
            if param_name == "FiltreGenre":
                pname = "member-filter-genre"
            if param_name == "Numero":
                pname = "member-numero"
            if param_name == "Naissance":
                pname = "member-birth"
            if param_name == "compteTiersDefault":
                pname = "member-account-third"
                param_value = convert_code(param_value)
            if param_name == "connexion":
                pname = "member-connection"
            if pname != '':
                self.print_log(
                    "=> parameter of invoice %s - %s", (pname, param_value))
                Parameter.change_value(pname, param_value)

    def run(self):
        try:
            self._params()
            self._season()
            self._subscription()
            self._categories()
        except:
            import traceback
            traceback.print_exc()
            six.print_("*** Unexpected error: %s ****" % sys.exc_info()[0])
