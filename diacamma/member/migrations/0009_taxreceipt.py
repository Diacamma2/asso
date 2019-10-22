# Generated by Django 2.2.6 on 2019-10-18 14:02

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

from lucterios.framework.tools import set_locale_lang
from lucterios.CORE.models import PrintModel


def initial_values(*args):
    set_locale_lang(settings.LANGUAGE_CODE)
    PrintModel().load_model('diacamma.member', "TaxReceipt_0001", is_default=True)


class Migration(migrations.Migration):

    dependencies = [
        ('payoff', '0007_bankaccount'),
        ('accounting', '0013_fiscalyear_folder'),
        ('member', '0008_thirdadherent'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxReceipt',
            fields=[
                ('supporting_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='payoff.Supporting')),
                ('num', models.IntegerField(null=False, verbose_name='numeros')),
                ('entries', models.ManyToManyField(to='accounting.EntryAccount', verbose_name='entries')),
                ('fiscal_year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.FiscalYear', verbose_name='fiscal year')),
                ('year', models.IntegerField(null=False, verbose_name='year')),
                ('date', models.DateField(verbose_name='date', null=False)),
            ],
            options={
                'verbose_name': 'tax receipt',
                'verbose_name_plural': 'tax receipts',
                'ordering': ['year', 'num', 'third'],
                'default_permissions': ['change'],
            },
            bases=('payoff.supporting',),
        ),
        migrations.RunPython(initial_values),
    ]
