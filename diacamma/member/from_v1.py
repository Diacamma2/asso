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
from django.db.models import Q

from lucterios.install.lucterios_migration import MigrateAbstract
from lucterios.framework.error import LucteriosException
from lucterios.CORE.models import Parameter

from diacamma.accounting.from_v1 import convert_code
from diacamma.member.models import convert_date
from lucterios.CORE.parameters import Params


class MemberMigrate(MigrateAbstract):

    def __init__(self, old_db):
        MigrateAbstract.__init__(self, old_db)
        self.season_list = {}
        self.period_list = {}
        self.doc_list = {}
        self.age_list = {}
        self.team_list = {}
        self.activity_list = {}
        self.subscriptiontype_list = {}
        self.adherent_list = {}
        self.subscription_list = {}

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
            self.print_debug("=> SEASON %s", (designation,))
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
                self.print_debug("=> PERIOD %s %d", (saison, num))
                self.period_list[periodid] = period_mdl.objects.create(
                    season=self.season_list[saison], num=num, begin_date=begin, end_date=end)

    def _subscription(self):
        article_mdl = apps.get_model("invoice", "Article")
        subscriptiontype_mdl = apps.get_model("member", "SubscriptionType")
        subscriptiontype_mdl.objects.all().delete()
        self.subscriptiontype_list = {}

        cur_s = self.old_db.open()
        cur_s.execute(
            "SELECT id,nom,description,duration,noactive FROM fr_sdlibre_membres_typeCotisations")
        for subid, nom, description, duration, noactive in cur_s.fetchall():
            self.print_debug(
                "=> SUBSCRIPTION:%s", (nom,))
            self.subscriptiontype_list[subid] = subscriptiontype_mdl.objects.create(
                name=nom, description=description, duration=duration, unactive=noactive == 'o')
            ids = []
            artcur = self.old_db.open()
            artcur.execute(
                'SELECT article FROM fr_sdlibre_membres_cotisationArticles WHERE typeCotisation=%d' % subid)
            for article, in artcur.fetchall():
                if article in self.old_db.objectlinks['article'].keys():
                    ids.append(self.old_db.objectlinks['article'][article].pk)
            self.subscriptiontype_list[
                subid].articles = article_mdl.objects.filter(id__in=ids)
            self.subscriptiontype_list[subid].save()

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
            self.print_debug("=> Age:%s", (nom,))
            self.age_list[ageid] = age_mdl.objects.create(
                name=nom, minimum=age_min, maximum=age_max)
        cur_t = self.old_db.open()
        cur_t.execute(
            "SELECT id,nom, description, noactive FROM fr_sdlibre_membres_equipes")
        for teamid, nom, description, noactive in cur_t.fetchall():
            self.print_debug(
                "=> Team:%s", (nom,))
            self.team_list[teamid] = team_mdl.objects.create(
                name=nom, description=description, unactive=noactive == 'o')
        cur_y = self.old_db.open()
        cur_y.execute(
            "SELECT id,nom, description FROM fr_sdlibre_membres_activite")
        for activityid, nom, description in cur_y.fetchall():
            self.print_debug(
                "=> Activity:%s", (nom,))
            self.activity_list[activityid] = activity_mdl.objects.create(
                name=nom, description=description)

    def _adherents(self):
        adherent_mdl = apps.get_model("member", "Adherent")
        adherent_mdl.objects.all().delete()
        self.adherent_list = {}
        subscription_mdl = apps.get_model("member", "Subscription")
        subscription_mdl.objects.all().delete()
        self.subscription_list = {}
        licence_mdl = apps.get_model("member", "License")
        licence_mdl.objects.all().delete()

        cur_a = self.old_db.open()
        cur_a.execute(
            "SELECT id, superId, DateNaissance, LieuNaissance  FROM fr_sdlibre_membres_adherents")
        for adherentid, superid, date_naissance, lieu_naissance in cur_a.fetchall():
            if superid in self.old_db.objectlinks['individual'].keys():
                individual = self.old_db.objectlinks['individual'][superid]
                self.print_debug(
                    "=> Adherent:%s", (six.text_type(individual),))
                self.adherent_list[adherentid] = adherent_mdl(
                    individual_ptr_id=individual.pk)
                self.adherent_list[adherentid].num = adherentid
                self.adherent_list[
                    adherentid].birthday = convert_date(date_naissance)
                if lieu_naissance is None:
                    self.adherent_list[adherentid].birthplace = ''
                else:
                    self.adherent_list[adherentid].birthplace = lieu_naissance
                self.adherent_list[adherentid].save(new_num=False)
                self.adherent_list[adherentid].__dict__.update(
                    individual.__dict__)
                self.adherent_list[adherentid].save()

        cur_s = self.old_db.open()
        cur_s.execute(
            "SELECT id,adherentid,saisonid,type,end,begin,licence,equipe,activite,document,facture FROM fr_sdlibre_membres_licences")
        for subid, adherentid, saisonid, subtype, end, begin, licence, equipe, activite, document, facture in cur_s.fetchall():
            if (adherentid in self.adherent_list.keys()) and (saisonid in self.season_list.keys()) and (subtype in self.subscriptiontype_list.keys()):
                self.print_debug(
                    "=> Subscription:%s %s", (adherentid, saisonid))
                begin = convert_date(
                    begin, self.season_list[saisonid].begin_date)
                end = convert_date(end, self.season_list[saisonid].end_date)
                try:
                    old_sub = subscription_mdl.objects.get_or_create(adherent=self.adherent_list[adherentid], season=self.season_list[
                        saisonid], subscriptiontype=self.subscriptiontype_list[subtype], begin_date=begin, end_date=end)
                except LucteriosException:
                    if self.subscriptiontype_list[subtype].duration == 0:
                        query_search = Q(season=self.season_list[saisonid])
                    else:
                        query_search = (Q(begin_date__lte=end) & Q(end_date__gte=end)) | (
                            Q(begin_date__lte=begin) & Q(end_date__gte=begin))
                    old_sub = self.adherent_list[
                        adherentid].subscription_set.filter(query_search)[0]
                if isinstance(old_sub, tuple):
                    old_sub = old_sub[0]
                self.subscription_list[subid] = old_sub
                if (facture is not None) and ('bill' in self.old_db.objectlinks.keys()):
                    if facture in self.old_db.objectlinks['bill'].keys():
                        old_sub.bill = self.old_db.objectlinks['bill'][facture]
                        old_sub.save()
                if (equipe in self.team_list.keys()) and (activite in self.activity_list.keys()):
                    new_lic = licence_mdl.objects.create(subscription=old_sub, team=self.team_list[
                        equipe], activity=self.activity_list[activite])
                    if licence is not None:
                        new_lic.value = licence
                        new_lic.save()
                if document is not None:
                    doc_idx = 0
                    for doc_item in document:
                        doc_item = "%d_%d" % (
                            self.season_list[saisonid].id, doc_idx)
                        if doc_item in self.doc_list.keys():
                            doc_adh = old_sub.docadherent_set.filter(
                                document=self.doc_list[doc_item])
                            if len(doc_adh) > 0:
                                doc_adh[0].value = doc_item == 'o'
                        doc_idx += 1

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
                pname = "invoice-account-third"
                param_value = convert_code(param_value)
            if param_name == "connexion":
                pname = "member-connection"
            if pname != '':
                self.print_debug(
                    "=> parameter of invoice %s - %s", (pname, param_value))
                Parameter.change_value(pname, param_value)
        Params.clear()

    def run(self):
        try:
            self._params()
            self._season()
            self._subscription()
            self._categories()
            self._adherents()
        except:
            import traceback
            traceback.print_exc()
            six.print_("*** Unexpected error: %s ****" % sys.exc_info()[0])
        self.print_info("Nb seasons:%d", len(self.season_list))
        self.print_info("Nb adherents:%d", len(self.adherent_list))
        self.print_info("Nb subscriptions:%d", len(self.subscription_list))
        self.old_db.objectlinks['activity'] = self.activity_list
        self.old_db.objectlinks['adherent'] = self.adherent_list
