# -*- coding: utf-8 -*-
'''
Initial django functions

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
from datetime import date

from django.db import migrations, models
from django.utils.translation import ugettext_lazy as _

from lucterios.CORE.models import Parameter, PrintModel
from diacamma.member.models import Adherent


def initial_values(*args):
    # pylint: disable=unused-argument, no-member, expression-not-assigned

    param = Parameter.objects.create(
        name="member-age-enable", typeparam=3)
    param.title = _("member-age-enable")
    param.args = "{}"
    param.value = 'True'
    param.save()

    param = Parameter.objects.create(
        name="member-team-enable", typeparam=3)
    param.title = _("member-team-enable")
    param.args = "{}"
    param.value = 'True'
    param.save()

    param = Parameter.objects.create(
        name="member-team-text", typeparam=0)
    param.title = _("member-team-text")
    param.args = "{'Multi':False}"
    param.value = _('Team')
    param.save()

    param = Parameter.objects.create(
        name="member-activite-enable", typeparam=3)
    param.title = _("member-activite-enable")
    param.args = "{}"
    param.value = "True"
    param.save()

    param = Parameter.objects.create(
        name="member-activite-text", typeparam=0)
    param.title = _("member-activite-text")
    param.args = "{'Multi':False}"
    param.value = _('Activity')
    param.save()

    param = Parameter.objects.create(
        name="member-connection", typeparam=3)
    param.title = _("member-connection")
    param.args = "{}"
    param.value = 'False'
    param.save()

    param = Parameter.objects.create(
        name="member-birth", typeparam=3)
    param.title = _("member-birth")
    param.args = "{}"
    param.value = 'True'
    param.save()

    param = Parameter.objects.create(
        name="member-filter-genre", typeparam=3)
    param.title = _("member-filter-genre")
    param.args = "{}"
    param.value = 'True'
    param.save()

    param = Parameter.objects.create(
        name="member-numero", typeparam=3)
    param.title = _("member-numero")
    param.args = "{}"
    param.value = 'True'
    param.save()

    param = Parameter.objects.create(
        name="member-licence-enabled", typeparam=3)
    param.title = _("member-licence-enabled")
    param.args = "{}"
    param.value = 'True'
    param.save()

    prtmdl = PrintModel.objects.create(
        name=_("adherents listing"), kind=0, modelname=Adherent.get_long_name())
    prtmdl.change_listing(297, 210, [(22, _('numeros'), '#num'),
                                     (25, _('lastname'), '#lastname'),
                                     (40, _('firstname'), '#firstname'),
                                     (50, _('address'), '#address'),
                                     (15, _('postal code'), '#postal_code'),
                                     (30, _('city'), '#city'),
                                     (20, _('phone'), '#tel1 #tel2'),
                                     (35, _('email'), '#email'),
                                     (30, _('comment'), '#comment')])
    prtmdl.save()

    prtmdl = PrintModel.objects.create(
        name=_("List émargement"), kind=0, modelname=Adherent.get_long_name())
    prtmdl.change_listing(297, 210, [(30, "%(last)s{[br/]}%(first)s" % {'last': _('lastname'), 'first': _('firstname')}, '#lastname{[br/]}#firstname'),
                                     (25, '', ''),
                                     (25, '', ''),
                                     (25, '', ''),
                                     (25, '', ''),
                                     (25, '', ''),
                                     (25, '', '')])
    prtmdl.save()

    prtmdl = PrintModel.objects.create(
        name=_("Complet listing"), kind=0, modelname=Adherent.get_long_name())
    prtmdl.change_listing(297, 210, [(1, _('numeros'), '#num'),
                                     (1, _('lastname'), '#lastname'),
                                     (1, _('firstname'), '#firstname'),
                                     (1, _('address'), '#address'),
                                     (1, _('postal code'), '#postal_code'),
                                     (1, _('city'), '#city'),
                                     (1, _('tel1'), '#tel1'),
                                     (1, _('tel2'), '#tel2'),
                                     (1, _('email'), '#email'),
                                     (1, _('comment'), '#comment'),
                                     (1, _("birthday"), "#birthday"),
                                     (1, _("birthplace"), "#birthplace"),
                                     (1, _('season'),
                                      '#subscription_set.season'),
                                     (1, _('subscription type'),
                                      '#subscription_set.subscriptiontype'),
                                     (1, _('begin date'),
                                      '#subscription_set.begin_date'),
                                     (1, _('end date'),
                                      '#subscription_set.end_date'),
                                     (1, _('team'),
                                      '#subscription_set.license_set.team'),
                                     (1, _('activity'),
                                      '#subscription_set.license_set.activity'),
                                     (1, _('license #'), '#subscription_set.license_set.value')])
    prtmdl.save()

    prtmdl = PrintModel.objects.create(
        name=_("label"), kind=1, modelname=Adherent.get_long_name())
    prtmdl.value = "#firstname #lastname{[newline]}#address{[newline]}#postal_code #city"
    prtmdl.save()

    prtmdl = PrintModel.objects.create(
        name=_("card"), kind=1, modelname=Adherent.get_long_name())
    prtmdl.value = "#num #firstname #lastname{[newline]}#birthday #birthplace{[newline]}#subscription_set.license_set.team #subscription_set.license_set.activity #subscription_set.license_set.value"
    prtmdl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
            ],
            options={
                'verbose_name_plural': 'activities',
                'verbose_name': 'activity',
            },
        ),
        migrations.CreateModel(
            name='Adherent',
            fields=[
                ('individual_ptr', models.OneToOneField(on_delete=models.CASCADE, parent_link=True, auto_created=True,
                                                        to='contacts.Individual', primary_key=True, serialize=False)),
                ('num', models.IntegerField(
                    default=0, verbose_name='numeros')),
                ('birthday', models.DateField(
                    default=date.today, null=True, verbose_name='birthday')),
                ('birthplace', models.CharField(
                    blank=True, max_length=50, verbose_name='birthplace')),
            ],
            options={
                'verbose_name_plural': 'adherents',
                'verbose_name': 'adherent',
            },
            bases=('contacts.individual',),
        ),
        migrations.CreateModel(
            name='Age',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('minimum', models.IntegerField(
                    verbose_name='minimum', default=0)),
                ('maximum', models.IntegerField(
                    verbose_name='maximum', default=0)),
            ],
            options={
                'verbose_name_plural': 'ages',
                'ordering': ['-minimum'],
                'verbose_name': 'age',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(
                    max_length=100, verbose_name='name')),
            ],
            options={
                'verbose_name_plural': 'documents needs',
                'verbose_name': 'document needs',
                'default_permissions': [],
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('num', models.IntegerField(
                    null=True, verbose_name='numeros', default=None)),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
            ],
            options={
                'verbose_name_plural': 'periods',
                'ordering': ['num'],
                'verbose_name': 'period',
                'default_permissions': [],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('designation', models.CharField(
                    max_length=100, verbose_name='designation')),
                ('iscurrent', models.BooleanField(
                    verbose_name='is current', default=False)),
            ],
            options={
                'verbose_name_plural': 'seasons',
                'ordering': ['-designation'],
                'verbose_name': 'season',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('begin_date', models.DateField(verbose_name='begin date')),
                ('end_date', models.DateField(verbose_name='end date')),
                ('adherent', models.ForeignKey(on_delete=models.CASCADE,
                                               default=None, to='member.Adherent', verbose_name='adherent')),
                ('season', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                             default=None, to='member.Season', verbose_name='season')),
            ],
            options={
                'verbose_name_plural': 'subscription',
                'verbose_name': 'subscription',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionType',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
                ('duration', models.IntegerField(choices=[(0, 'annually'), (1, 'periodic'), (
                    2, 'monthly'), (3, 'calendar')], default=0, db_index=True, verbose_name='duration')),
                ('unactive', models.BooleanField(
                    verbose_name='unactive', default=False)),
                ('articles', models.ManyToManyField(
                    to='invoice.Article', blank=True, verbose_name='articles')),
            ],
            options={
                'verbose_name_plural': 'subscription types',
                'verbose_name': 'subscription type',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(
                    primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    null=True, verbose_name='description', default='')),
                ('unactive', models.BooleanField(
                    verbose_name='unactive', default=False)),
            ],
            options={
                'verbose_name_plural': 'teams',
                'verbose_name': 'team',
            },
        ),
        migrations.CreateModel(
            name='DocAdherent',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value', models.BooleanField(
                    default=False, verbose_name='value')),
                ('document', models.ForeignKey(default=None, on_delete=models.deletion.PROTECT,
                                               verbose_name='document', to='member.Document')),
                ('subscription', models.ForeignKey(default=None, on_delete=models.deletion.CASCADE,
                                                   verbose_name='subscription', to='member.Subscription')),
            ],
            options={
                'default_permissions': [],
                'verbose_name_plural': 'documents',
                'verbose_name': 'document',
            },
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value', models.CharField(
                    null=True, verbose_name='license #', max_length=50)),
                ('activity', models.ForeignKey(default=None, null=True,
                                               on_delete=models.deletion.PROTECT, verbose_name='activity', to='member.Activity')),
                ('subscription', models.ForeignKey(on_delete=models.CASCADE,
                                                   verbose_name='subscription', default=None, to='member.Subscription')),
                ('team', models.ForeignKey(default=None, null=True,
                                           on_delete=models.deletion.PROTECT, verbose_name='team', to='member.Team')),
            ],
            options={
                'verbose_name': 'license',
                'default_permissions': [],
                'verbose_name_plural': 'licenses'
            },
        ),
        migrations.AddField(
            model_name='subscription',
            name='subscriptiontype',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, default=None,
                                    to='member.SubscriptionType', verbose_name='subscription type'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='bill',
            field=models.ForeignKey(
                null=True, verbose_name='bill', on_delete=models.deletion.PROTECT, to='invoice.Bill', default=None),
        ),
        migrations.AddField(
            model_name='period',
            name='season',
            field=models.ForeignKey(on_delete=models.CASCADE,
                                    default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.AddField(
            model_name='document',
            name='season',
            field=models.ForeignKey(on_delete=models.CASCADE,
                                    default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.RunPython(initial_values),
    ]
