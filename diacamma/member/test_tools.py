# -*- coding: utf-8 -*-
'''
diacamma.member test_tools package

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

from lucterios.framework.xfergraphic import XferContainerAcknowledge

from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params

from diacamma.accounting.test_tools import default_compta_fr
from diacamma.invoice.test_tools import default_articles
from diacamma.payoff.test_tools import default_bankaccount_fr
from diacamma.member.editors import SeasonEditor
from diacamma.member.models import Season, Activity, Team, Age, Document,\
    Adherent, SubscriptionType, Prestation
from diacamma.invoice.models import Article


def default_financial():
    from diacamma.invoice.views_conf import paramchange_invoice
    from diacamma.payoff.views_conf import paramchange_payoff
    paramchange_invoice([])
    paramchange_payoff([])
    default_compta_fr()
    default_articles()
    default_bankaccount_fr()


def default_season():
    xfer = XferContainerAcknowledge()
    for idx in range(20):
        xfer.params['begin_date'] = '%d-09-01' % (2000 + idx)
        xfer.item = Season()
        editor = SeasonEditor(xfer.item)
        editor.saving(xfer)
    Season.objects.get(id=10).set_has_actif()


def default_params():
    Parameter.change_value('member-team-text', 'group')
    Parameter.change_value('member-activite-text', 'passion')
    Params.clear()
    default = Activity.objects.get(id=1)
    default.name = "activity1"
    default.description = "activity N°1"
    default.save()
    Activity.objects.create(name="activity2", description="activity N°2")
    Team.objects.create(name="team1", description="team N°1{[br/]}The bests")
    Team.objects.create(name="team2", description="team N°2{[br/]}The chalengers")
    Team.objects.create(name="team3", description="team N°3{[br/]}The newbies")
    Age.objects.create(name="Poussins", minimum=9, maximum=10)
    Age.objects.create(name="Benjamins", minimum=11, maximum=12)
    Age.objects.create(name="Minimes", minimum=13, maximum=14)
    Age.objects.create(name="Cadets", minimum=15, maximum=16)
    Age.objects.create(name="Juniors", minimum=17, maximum=18)
    Age.objects.create(name="Espoirs", minimum=19, maximum=21)
    Age.objects.create(name="Seniors", minimum=22, maximum=38)
    Age.objects.create(name="Vétérans", minimum=39, maximum=108)
    Document.objects.create(season=Season.current_season(), name="Doc 1")
    Document.objects.create(season=Season.current_season(), name="Doc 2")


def create_adherent(firstname, lastname, birthday):
    new_adh = Adherent()
    new_adh.firstname = firstname
    new_adh.lastname = lastname
    new_adh.address = "rue de la liberté"
    new_adh.postal_code = "97250"
    new_adh.city = "LE PRECHEUR"
    new_adh.country = "MARTINIQUE"
    new_adh.tel2 = "02-78-45-12-95"
    new_adh.email = "%s.%s@worldcompany.com" % (firstname, lastname)
    new_adh.birthday = birthday
    new_adh.save()
    return new_adh


def default_adherents():
    # adherent 2 - 2009 = 9ans
    create_adherent('Avrel', 'Dalton', '2000-02-10')
    # adherent 3 - 2009 = 11ans
    create_adherent('William', 'Dalton', '1998-03-31')
    # adherent 4 - 2009 = 17ans
    create_adherent('Jack', 'Dalton', '1992-04-23')
    create_adherent('Joe', 'Dalton', '1989-05-18')  # adherent 5 - 2009 = 20ans
    create_adherent('Lucky', 'Luke', '1979-06-04')  # adherent 6 - 2009 = 30ans


def default_subscription():
    sub1 = SubscriptionType.objects.create(
        name="Annually", description="AAA", duration=0)
    sub1.articles.set(Article.objects.filter(id__in=(1, 5)))
    sub1.save()
    sub2 = SubscriptionType.objects.create(
        name="Periodic", description="BBB", duration=1)
    sub2.articles.set(Article.objects.filter(id__in=(1, 5)))
    sub2.save()
    sub3 = SubscriptionType.objects.create(
        name="Monthly", description="CCC", duration=2)
    sub3.articles.set(Article.objects.filter(id__in=(1, 5)))
    sub3.save()
    sub4 = SubscriptionType.objects.create(
        name="Calendar", description="DDD", duration=3)
    sub4.articles.set(Article.objects.filter(id__in=(1, 5)))
    sub4.save()


def set_parameters(values):
    param_lists = ["team", "activite", "age", "licence", "genre", 'numero', 'birth']
    for param_item in param_lists:
        if param_item == "genre":
            param_name = "member-filter-genre"
        elif param_item == "numero":
            param_name = "member-numero"
        elif param_item == "birth":
            param_name = "member-birth"
        else:
            param_name = "member-%s-enable" % param_item
            if param_item == "licence":
                param_name += 'd'
        Parameter.change_value(param_name, param_item in values)
    Params.clear()


def default_prestation():
    Prestation.objects.create(name="Presta 1", description="Prestation N°1", team_id=3, activity_id=2, article_id=1)
    Prestation.objects.create(name="Presta 2", description="Prestation N°2", team_id=2, activity_id=2, article_id=2)
    Prestation.objects.create(name="Presta 3", description="Prestation N°3", team_id=1, activity_id=1, article_id=3)
