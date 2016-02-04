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
import sys

from django.apps import apps
from django.utils import six

from lucterios.install.lucterios_migration import MigrateAbstract


class EventMigrate(MigrateAbstract):

    def __init__(self, old_db):
        MigrateAbstract.__init__(self, old_db)
        self.degreetype_list = {}
        self.subdegreetype_list = {}
        self.degree_list = {}

    def _config(self):
        degreetype_mdl = apps.get_model("event", "DegreeType")
        self.degreetype_list = {}
        subdegreetype_mdl = apps.get_model("event", "SubDegreeType")
        self.subdegreetype_list = {}
        cur_dt = self.old_db.open()
        cur_dt.execute(
            "SELECT id,  nom, niveau, activite  FROM fr_sdlibre_FormationSport_TypeDiplome")
        for degreetypeid, nom, niveau, activite in cur_dt.fetchall():
            if activite in self.old_db.objectlinks['activity'].keys():
                self.print_debug("=> DegreeType %s", (nom,))
                self.degreetype_list[degreetypeid] = degreetype_mdl.objects.create(
                    name=nom, level=niveau, activity=self.old_db.objectlinks['activity'][activite])
            else:
                self.print_debug("=> no DegreeType %s - %s", (nom, activite))
        cur_sdt = self.old_db.open()
        cur_sdt.execute(
            "SELECT id,  nom, niveau  FROM fr_sdlibre_FormationSport_TypeSousDiplome")
        for subdegreetypeid, nom, niveau in cur_sdt.fetchall():
            self.print_debug("=> SubDegreeType %s", (nom,))
            self.subdegreetype_list[subdegreetypeid] = subdegreetype_mdl.objects.create(
                name=nom, level=niveau)

    def _degree(self):
        degree_mdl = apps.get_model("event", "Degree")
        self.degree_list = {}
        cur_d = self.old_db.open()
        cur_d.execute(
            "SELECT id, membre, diplome, sousDiplome, date, formation FROM fr_sdlibre_FormationSport_Diplome")
        for degreeid, membre, diplome, sousDiplome, date, _ in cur_d.fetchall():
            if (diplome in self.degreetype_list.keys()) and (membre in self.old_db.objectlinks['adherent'].keys()):
                self.print_debug(
                    "=> Degree %s %s %s", (membre, diplome, sousDiplome))
                self.degree_list[degreeid] = degree_mdl.objects.create(
                    adherent=self.old_db.objectlinks['adherent'][membre], degree=self.degreetype_list[diplome], date=date)
                if sousDiplome in self.subdegreetype_list.keys():
                    self.degree_list[
                        degreeid].subdegree = self.subdegreetype_list[sousDiplome]
                    self.degree_list[degreeid].save()
            else:
                self.print_debug(
                    "=> No Degree %s %s %s", (membre, diplome, sousDiplome))

    def run(self):
        try:
            self._config()
            self._degree()
        except:
            import traceback
            traceback.print_exc()
            six.print_("*** Unexpected error: %s ****" % sys.exc_info()[0])
        self.print_info("Nb degree types:%d", len(self.degreetype_list))
        self.print_info("Nb sub degree types:%d", len(self.subdegreetype_list))
        self.print_info("Nb degrees:%d", len(self.degree_list))
