# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.translation import ugettext_lazy as _

from lucterios.CORE.models import Parameter


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
        name="member-account-third", typeparam=0)
    param.title = _("member-account-third")
    param.args = "{'Multi':False}"
    param.value = '411'
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


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    default='', verbose_name='description', null=True)),
            ],
            options={
                'verbose_name_plural': 'activities',
                'verbose_name': 'activity',
            },
        ),
        migrations.CreateModel(
            name='Age',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('minimum', models.IntegerField(
                    default=0, verbose_name='minimum')),
                ('maximum', models.IntegerField(
                    default=0, verbose_name='maximum')),
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
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
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
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('num', models.IntegerField(
                    default=None, verbose_name='numeros', null=True)),
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
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('designation', models.CharField(
                    max_length=100, verbose_name='designation')),
                ('iscurrent', models.BooleanField(
                    default=False, verbose_name='is current')),
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
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    default='', verbose_name='description', null=True)),
                ('duration', models.IntegerField(default=0, choices=[
                 (0, 'annually'), (1, 'periodic'), (2, 'monthly'), (3, 'calendar')], verbose_name='duration', db_index=True)),
                ('unactive', models.BooleanField(
                    default=False, verbose_name='unactive')),
                ('articles', models.ManyToManyField(
                    to='invoice.Article', verbose_name='articles', blank=True)),
            ],
            options={
                'verbose_name_plural': 'subscriptions',
                'verbose_name': 'subscription',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(
                    default='', verbose_name='description', null=True)),
                ('unactive', models.BooleanField(
                    default=False, verbose_name='unactive')),
            ],
            options={
                'verbose_name_plural': 'teams',
                'verbose_name': 'team',
            },
        ),
        migrations.AddField(
            model_name='period',
            name='season',
            field=models.ForeignKey(
                default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.AddField(
            model_name='document',
            name='season',
            field=models.ForeignKey(
                default=None, to='member.Season', verbose_name='season'),
        ),
        migrations.RunPython(initial_values),
    ]
