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
from shutil import rmtree

from lucterios.framework.test import LucteriosTest
from lucterios.framework.filetools import get_user_dir
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params

from diacamma.member.views_season import SeasonAddModify, SeasonShow, SeasonSubscription,\
    SeasonActive, DocummentAddModify, DocummentDel, SeasonDocummentClone,\
    PeriodDel, PeriodAddModify, SubscriptionTypeAddModify, SubscriptionTypeShow,\
    SubscriptionTypeDel, PrestationDel, PrestationAddModify
from diacamma.member.test_tools import default_season, default_financial,\
    set_parameters, default_params
from diacamma.member.views_conf import CategoryConf, ActivityAddModify,\
    ActivityDel, TeamAddModify, TeamDel, AgeAddModify, AgeDel, CategoryParamEdit


class SeasonTest(LucteriosTest):

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)
        set_parameters(["team", "activite", "age", "licence", "genre", 'numero', 'birth'])

    def test_add(self):
        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 0)

        self.factory.xfer = SeasonAddModify()
        self.calljson('/diacamma.member/seasonAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonAddModify')
        self.assert_count_equal('', 2)
        self.assert_json_equal('DATE', 'begin_date', '')

        self.factory.xfer = SeasonAddModify()
        self.calljson('/diacamma.member/seasonAddModify', {'SAVE': 'YES', "begin_date": '2014-09-01'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'seasonAddModify')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('', 6)
        self.assert_json_equal('LABELFORM', 'designation', "2014/2015")
        self.assert_json_equal('LABELFORM', 'begin_date', "2014-09-01")
        self.assert_json_equal('LABELFORM', 'end_date', "2015-08-31")
        self.assert_grid_equal('period', {'num': "N°", 'begin_date': "date de début", 'end_date': "date de fin"}, 4)
        self.assert_grid_equal('document', {'name': 'nom'}, 0)  # nb=1

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 1)
        self.assert_json_equal('', 'season/@0/designation', "2014/2015")
        self.assert_json_equal('', 'season/@0/iscurrent', True)

        self.factory.xfer = SeasonAddModify()
        self.calljson('/diacamma.member/seasonAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonAddModify')
        self.assert_count_equal('', 2)
        self.assert_json_equal('DATE', 'begin_date', '2015-09-01')

        self.factory.xfer = SeasonAddModify()
        self.calljson('/diacamma.member/seasonAddModify',
                      {'SAVE': 'YES', "begin_date": '2015-09-01'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'seasonAddModify')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 2)
        self.assert_json_equal('', 'season/@0/designation', "2015/2016")
        self.assert_json_equal('', 'season/@0/iscurrent', False)
        self.assert_json_equal('', 'season/@1/designation', "2014/2015")
        self.assert_json_equal('', 'season/@1/iscurrent', True)

        self.factory.xfer = SeasonAddModify()
        self.calljson('/diacamma.member/seasonAddModify',
                      {'SAVE': 'YES', "begin_date": '2015-11-01'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'seasonAddModify')

    def test_list(self):
        default_season()

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('', 9)
        self.assert_grid_equal('season', {'designation': "désignation", 'period_set': "période", 'iscurrent': "courant"}, 5)
        self.assert_json_equal('TAB', '__tab_1', 'Saison')
        self.assert_json_equal('TAB', '__tab_2', 'Les cotisations')
        self.assert_json_equal('TAB', '__tab_3', 'Les prestations')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {'show_filter': 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 20)

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {'show_filter': 0}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 5)
        self.assert_json_equal('', 'season/@0/designation', "2011/2012")
        self.assert_json_equal('', 'season/@1/designation', "2010/2011")
        self.assert_json_equal('', 'season/@2/designation', "2009/2010")
        self.assert_json_equal('', 'season/@3/designation', "2008/2009")
        self.assert_json_equal('', 'season/@4/designation', "2007/2008")
        self.assert_json_equal('', 'season/@0/iscurrent', False)
        self.assert_json_equal('', 'season/@1/iscurrent', False)
        self.assert_json_equal('', 'season/@2/iscurrent', True)
        self.assert_json_equal('', 'season/@3/iscurrent', False)
        self.assert_json_equal('', 'season/@4/iscurrent', False)

        self.factory.xfer = SeasonActive()
        self.calljson('/diacamma.member/seasonActive', {'season': 12}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'seasonActive')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {'show_filter': 0}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('season', 5)
        self.assert_json_equal('', 'season/@0/designation', "2013/2014")
        self.assert_json_equal('', 'season/@1/designation', "2012/2013")
        self.assert_json_equal('', 'season/@2/designation', "2011/2012")
        self.assert_json_equal('', 'season/@3/designation', "2010/2011")
        self.assert_json_equal('', 'season/@4/designation', "2009/2010")

    def test_doc(self):
        default_season()

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('', 6)
        self.assert_json_equal('LABELFORM', 'designation', "2009/2010")
        self.assert_count_equal('period', 4)
        self.assert_count_equal('document', 0)

        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'docummentAddModify')
        self.assert_count_equal('', 2)

        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify',
                      {'SAVE': 'YES', 'season': 10, 'name': 'abc123'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'docummentAddModify')
        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify',
                      {'SAVE': 'YES', 'season': 10, 'name': 'xyz987'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'docummentAddModify')
        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify',
                      {'SAVE': 'YES', 'season': 10, 'name': 'opq357'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'docummentAddModify')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('document', 3)
        self.assert_json_equal('', 'document/@0/name', "abc123")
        self.assert_json_equal('', 'document/@1/name', "xyz987")
        self.assert_json_equal('', 'document/@2/name', "opq357")

        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify', {'season': 10, 'document': 2}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'docummentAddModify')
        self.assert_count_equal('', 2)
        self.assert_json_equal('EDIT', 'name', "xyz987")

        self.factory.xfer = DocummentAddModify()
        self.calljson('/diacamma.member/docummentAddModify', {'SAVE': 'YES', 'season': 10, 'document': 2, 'name': '987xyz'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'docummentAddModify')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('document', 3)
        self.assert_json_equal('', 'document/@0/name', "abc123")
        self.assert_json_equal('', 'document/@1/name', "987xyz")
        self.assert_json_equal('', 'document/@2/name', "opq357")

        self.factory.xfer = DocummentDel()
        self.calljson('/diacamma.member/docummentDel', {'CONFIRME': 'YES', 'season': 10, 'document': 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'docummentDel')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('document', 2)
        self.assert_json_equal('', 'document/@0/name', "abc123")
        self.assert_json_equal('', 'document/@1/name', "opq357")

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 11}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('document', 0)

        self.factory.xfer = SeasonDocummentClone()
        self.calljson('/diacamma.member/seasonDocummentClone', {'season': 11}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'seasonDocummentClone')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 11}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('document', 2)
        self.assert_json_equal('', 'document/@0/name', "abc123")
        self.assert_json_equal('', 'document/@1/name', "opq357")

    def test_period(self):
        default_season()

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('', 6)
        self.assert_json_equal('LABELFORM', 'designation', "2009/2010")
        self.assert_count_equal('period', 4)
        self.assert_count_equal('document', 0)
        self.assert_json_equal('', 'period/@0/id', '37')
        self.assert_json_equal('', 'period/@1/id', '38')
        self.assert_json_equal('', 'period/@2/id', '39')
        self.assert_json_equal('', 'period/@3/id', '40')
        self.assert_json_equal('', 'period/@0/num', '1')
        self.assert_json_equal('', 'period/@1/num', '2')
        self.assert_json_equal('', 'period/@2/num', '3')
        self.assert_json_equal('', 'period/@3/num', '4')
        self.assert_json_equal('', 'period/@0/begin_date', '2009-09-01')
        self.assert_json_equal('', 'period/@1/begin_date', '2009-12-01')
        self.assert_json_equal('', 'period/@2/begin_date', '2010-03-01')
        self.assert_json_equal('', 'period/@3/begin_date', '2010-06-01')

        self.factory.xfer = PeriodDel()
        self.calljson('/diacamma.member/periodDel', {'CONFIRME': 'YES', 'period': 38}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'periodDel')
        self.factory.xfer = PeriodDel()
        self.calljson('/diacamma.member/periodDel', {'CONFIRME': 'YES', 'period': 39}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'periodDel')
        self.factory.xfer = PeriodDel()
        self.calljson('/diacamma.member/periodDel', {'CONFIRME': 'YES', 'period': 40}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'periodDel')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('period', 2)
        self.assert_json_equal('', 'period/@0/id', '37')
        self.assert_json_equal('', 'period/@1/id', '40')
        self.assert_json_equal('', 'period/@0/num', '1')
        self.assert_json_equal('', 'period/@1/num', '2')
        self.assert_json_equal('', 'period/@0/begin_date', '2009-09-01')
        self.assert_json_equal('', 'period/@1/begin_date', '2010-06-01')

        self.factory.xfer = PeriodAddModify()
        self.calljson('/diacamma.member/periodAddModify', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'periodAddModify')
        self.assert_count_equal('', 4)

        self.factory.xfer = PeriodAddModify()
        self.calljson('/diacamma.member/periodAddModify', {'SAVE': 'YES', 'season': 10, 'begin_date': '2010-05-30', 'end_date': '2009-12-01'}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'periodAddModify')

        self.factory.xfer = PeriodAddModify()
        self.calljson('/diacamma.member/periodAddModify', {'SAVE': 'YES', 'season': 10, 'begin_date': '2009-12-01', 'end_date': '2010-05-30'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'periodAddModify')

        self.factory.xfer = SeasonShow()
        self.calljson('/diacamma.member/seasonShow', {'season': 10}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonShow')
        self.assert_count_equal('period', 3)
        self.assert_json_equal('', 'period/@0/num', '1')
        self.assert_json_equal('', 'period/@1/num', '2')
        self.assert_json_equal('', 'period/@2/num', '3')
        self.assert_json_equal('', 'period/@0/begin_date', '2009-09-01')
        self.assert_json_equal('', 'period/@1/begin_date', '2009-12-01')
        self.assert_json_equal('', 'period/@2/begin_date', '2010-06-01')

    def test_subscription(self):
        default_financial()
        default_season()
        set_parameters(["activite", "age", "licence", "genre", 'numero', 'birth'])

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('', 7)
        self.assert_grid_equal('subscriptiontype', {'name': "nom", 'description': "description", 'duration': "durée", 'unactive': "désactivé", 'price': "prix"}, 0)
        self.assert_json_equal('TAB', '__tab_1', 'Saison')
        self.assert_json_equal('TAB', '__tab_2', 'Les cotisations')
        self.assertFalse('__tab_3' in self.json_data.keys(), self.json_data.keys())

        self.factory.xfer = SubscriptionTypeAddModify()
        self.calljson('/diacamma.member/subscriptionTypeAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionTypeAddModify')
        self.assert_count_equal('', 7)

        self.factory.xfer = SubscriptionTypeAddModify()
        self.calljson('/diacamma.member/subscriptionTypeAddModify',
                      {'SAVE': 'YES', 'name': 'abc123', 'description': 'blablabla', 'duration': 1, 'articles': '1;5'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTypeAddModify')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('subscriptiontype', 1)
        self.assert_json_equal('', 'subscriptiontype/@0/name', "abc123")
        self.assert_json_equal('', 'subscriptiontype/@0/description', "blablabla")
        self.assert_json_equal('', 'subscriptiontype/@0/duration', 1)
        self.assert_json_equal('', 'subscriptiontype/@0/unactive', False)
        self.assert_json_equal('', 'subscriptiontype/@0/price', 76.44)

        self.factory.xfer = SubscriptionTypeShow()
        self.calljson('/diacamma.member/subscriptionTypeShow', {"subscriptiontype": 1}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'subscriptionTypeShow')
        self.assert_count_equal('', 7)
        self.assert_json_equal('LABELFORM', 'articles', ["ABC1", "ABC5"])

        self.factory.xfer = SubscriptionTypeDel()
        self.calljson('/diacamma.member/subscriptionTypeDel', {"subscriptiontype": 1, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'subscriptionTypeDel')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('subscriptiontype', 0)

    def test_prestation(self):
        default_financial()
        default_season()
        default_params()

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('', 9)
        self.assert_json_equal('TAB', '__tab_1', 'Saison')
        self.assert_json_equal('TAB', '__tab_2', 'Les cotisations')
        self.assert_json_equal('TAB', '__tab_3', 'Les prestations')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())
        self.assert_grid_equal('prestation', {'name': "nom", 'description': "description", 'team': "group", 'activity': "passion", 'article.price': "prix"}, 0)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'prestationAddModify')
        self.assert_count_equal('', 6)

        self.factory.xfer = PrestationAddModify()
        self.calljson('/diacamma.member/prestationAddModify',
                      {'SAVE': 'YES', 'name': 'abc123', 'description': 'blablabla', 'team': 3, 'activity': 2, 'article': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationAddModify')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('prestation', 1)
        self.assert_json_equal('', 'prestation/@0/name', "abc123")
        self.assert_json_equal('', 'prestation/@0/description', "blablabla")
        self.assert_json_equal('', 'prestation/@0/team', "team3")
        self.assert_json_equal('', 'prestation/@0/activity', "activity2")
        self.assert_json_equal('', 'prestation/@0/article.price', 12.34)

        self.factory.xfer = PrestationDel()
        self.calljson('/diacamma.member/prestationDel', {"prestation": 1, 'CONFIRME': 'YES'}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'prestationDel')

        self.factory.xfer = SeasonSubscription()
        self.calljson('/diacamma.member/seasonSubscription', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'seasonSubscription')
        self.assert_count_equal('prestation', 0)


class CategoriesTest(LucteriosTest):

    def setUp(self):
        LucteriosTest.setUp(self)
        rmtree(get_user_dir(), True)

    def test_activity(self):
        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assert_grid_equal('activity', {'name': "nom", 'description': "description"}, 1)

        self.factory.xfer = ActivityAddModify()
        self.calljson('/diacamma.member/activityAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'activityAddModify')
        self.assert_count_equal('', 3)

        self.factory.xfer = ActivityAddModify()
        self.calljson('/diacamma.member/activityAddModify',
                      {"SAVE": "YES", "name": "xyz", "description": "abc"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'activityAddModify')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('activity', 2)
        self.assert_json_equal('', 'activity/@1/name', "xyz")

        self.factory.xfer = ActivityDel()
        self.calljson('/diacamma.member/activityDel', {"CONFIRME": "YES", "activity": 2}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'activityDel')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('activity', 1)

        self.factory.xfer = ActivityDel()
        self.calljson('/diacamma.member/activityDel', {"CONFIRME": "YES", "activity": 1}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'activityDel')

        Parameter.change_value("member-activite-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 0)
        self.assert_json_equal('LABELFORM', 'member-activite-enable', 'Non')
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Âge')
        self.assert_json_equal('TAB', '__tab_3', 'Équipe')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())

    def test_team(self):
        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assert_grid_equal('team', {'name': "nom", 'description': "description"}, 0)

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {'show_only_enabled_team': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assert_grid_equal('team', {'name': "nom", 'description': "description", 'unactive': "désactivé"}, 0)

        self.factory.xfer = TeamAddModify()
        self.calljson('/diacamma.member/teamAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'teamAddModify')
        self.assert_count_equal('', 4)

        self.factory.xfer = TeamAddModify()
        self.calljson('/diacamma.member/teamAddModify',
                      {"SAVE": "YES", "name": "xyz", "description": "abc", 'unactive': 0}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'teamAddModify')

        self.factory.xfer = TeamAddModify()
        self.calljson('/diacamma.member/teamAddModify',
                      {"SAVE": "YES", "name": "uvw", "description": "def", 'unactive': 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'teamAddModify')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {'show_only_enabled_team': False}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('team', 2)
        self.assert_json_equal('', 'team/@0/name', "uvw")
        self.assert_json_equal('', 'team/@0/unactive', True)
        self.assert_json_equal('', 'team/@1/name', "xyz")
        self.assert_json_equal('', 'team/@1/unactive', False)

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {'show_only_enabled_team': True}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('team', 1)
        self.assert_json_equal('', 'team/@0/name', "xyz")

        self.factory.xfer = TeamDel()
        self.calljson('/diacamma.member/teamDel', {"CONFIRME": "YES", "team": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'teamDel')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('team', 0)

        Parameter.change_value("member-team-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 0 + 2)
        self.assert_json_equal('LABELFORM', 'member-team-enable', 'Non')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Âge')
        self.assert_json_equal('TAB', '__tab_3', 'Activité')

    def test_age(self):
        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assert_grid_equal('age', {'name': "nom", 'date_min': "date min.", 'date_max': "date max."}, 0)

        self.factory.xfer = AgeAddModify()
        self.calljson('/diacamma.member/ageAddModify', {}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'ageAddModify')

        default_season()

        self.factory.xfer = AgeAddModify()
        self.calljson('/diacamma.member/ageAddModify', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'ageAddModify')
        self.assert_count_equal('', 4)

        self.factory.xfer = AgeAddModify()
        self.calljson('/diacamma.member/ageAddModify', {"SAVE": "YES", "name": "xyz", "date_min": "1981", "date_max": "1980"}, False)
        self.assert_observer('core.exception', 'diacamma.member', 'ageAddModify')

        self.factory.xfer = AgeAddModify()
        self.calljson('/diacamma.member/ageAddModify', {"SAVE": "YES", "name": "xyz", "date_min": "1980", "date_max": "1981"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'ageAddModify')
        self.factory.xfer = AgeAddModify()
        self.calljson('/diacamma.member/ageAddModify', {"SAVE": "YES", "name": "uvw", "date_min": "1979", "date_max": "1980"}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'ageAddModify')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('age', 2)
        self.assert_json_equal('', 'age/@0/name', "uvw")
        self.assert_json_equal('', 'age/@0/date_min', "1979")
        self.assert_json_equal('', 'age/@0/date_max', "1980")
        self.assert_json_equal('', 'age/@1/name', "xyz")
        self.assert_json_equal('', 'age/@1/date_min', "1980")
        self.assert_json_equal('', 'age/@1/date_max', "1981")

        self.factory.xfer = SeasonActive()
        self.calljson('/diacamma.member/seasonActive', {'season': 12}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'seasonActive')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('age', 2)
        self.assert_json_equal('', 'age/@0/name', "uvw")
        self.assert_json_equal('', 'age/@0/date_min', "1981")
        self.assert_json_equal('', 'age/@0/date_max', "1982")
        self.assert_json_equal('', 'age/@1/name', "xyz")
        self.assert_json_equal('', 'age/@1/date_min', "1982")
        self.assert_json_equal('', 'age/@1/date_max', "1983")
        self.assert_json_equal('LABELFORM', 'member-age-enable', 'Oui')

        self.factory.xfer = AgeDel()
        self.calljson('/diacamma.member/ageDel', {"CONFIRME": "YES", "age": 1}, False)
        self.assert_observer('core.acknowledge', 'diacamma.member', 'ageDel')

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('age', 1)

        Parameter.change_value("member-age-enable", '0')
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 0 + 3 + 2)
        self.assert_json_equal('LABELFORM', 'member-age-enable', 'Non')
        self.assertFalse('__tab_4' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Équipe')
        self.assert_json_equal('TAB', '__tab_3', 'Activité')

    def test_params(self):
        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assertFalse('__tab_5' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Âge')
        self.assert_json_equal('TAB', '__tab_3', 'Équipe')
        self.assert_json_equal('TAB', '__tab_4', 'Activité')
        self.assert_json_equal('LABELFORM', 'member-team-text', 'Équipe')
        self.assert_json_equal('LABELFORM', 'member-activite-text', 'Activité')
        self.assert_json_equal('LABELFORM', 'member-fields', "N°{[br/]}prénom{[br/]}nom{[br/]}tel1{[br/]}tel2{[br/]}courriel{[br/]}participation")
        self.assert_json_equal('', '#editparam/action/action', 'categoryParamEdit')

        self.factory.xfer = CategoryParamEdit()
        self.calljson('/diacamma.member/categoryParamEdit', {'params': ";".join(["member-team-enable", "member-team-text", "member-activite-enable", "member-activite-text", "member-age-enable",
                                                                                 "member-licence-enabled", "member-filter-genre", "member-numero", "member-birth", "member-family-type", "member-connection",
                                                                                 "member-subscription-mode", "member-size-page", "member-fields", "member-subscription-message"])}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryParamEdit')
        self.assert_json_equal('SELECT', 'member-size-page', '25')
        self.assert_select_equal('member-size-page', 4)
        self.assert_json_equal('CHECKLIST', 'member-fields', ['num', 'firstname', 'lastname', 'tel1', 'tel2', 'email', 'license'])
        self.assert_select_equal('member-fields', 17, checked=True)

        Parameter.change_value("member-team-text", 'Cours')
        Parameter.change_value("member-activite-text", 'Sport')
        Parameter.change_value("member-fields", "firstname;lastname;email;documents")
        Params.clear()

        self.factory.xfer = CategoryConf()
        self.calljson('/diacamma.member/categoryConf', {}, False)
        self.assert_observer('core.custom', 'diacamma.member', 'categoryConf')
        self.assert_count_equal('', 2 + 17 + 2 + 3 + 2)
        self.assertFalse('__tab_5' in self.json_data.keys(), self.json_data.keys())
        self.assert_json_equal('TAB', '__tab_1', 'Paramètres')
        self.assert_json_equal('TAB', '__tab_2', 'Âge')
        self.assert_json_equal('TAB', '__tab_3', 'Cours')
        self.assert_json_equal('TAB', '__tab_4', 'Sport')
        self.assert_json_equal('LABELFORM', 'member-team-text', 'Cours')
        self.assert_json_equal('LABELFORM', 'member-activite-text', 'Sport')
        self.assert_json_equal('LABELFORM', 'member-fields', "prénom{[br/]}nom{[br/]}courriel{[br/]}documents demandés")
