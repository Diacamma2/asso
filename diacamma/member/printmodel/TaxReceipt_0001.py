# -*- coding: utf-8 -*-
'''
Printmodel django module for invoice

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

from django.utils.translation import ugettext_lazy as _
from diacamma.member.models import TaxReceipt

name = _("tax receipt")
kind = 2
modelname = TaxReceipt.get_long_name()
value = """
<model hmargin="10.0" vmargin="10.0" page_width="210.0" page_height="148.5">
<header extent="25.0">
<text height="20.0" width="120.0" top="5.0" left="70.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="center" line_height="20" font_family="sans-serif" font_weight="" font_size="20">
{[b]}#OUR_DETAIL.name{[/b]}
</text>
<image height="25.0" width="30.0" top="0.0" left="10.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2">
#OUR_DETAIL.image
</image>
</header>
<bottom extent="10.0">
<text height="10.0" width="190.0" top="00.0" left="0.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="center" line_height="8" font_family="sans-serif" font_weight="" font_size="8">
{[italic]}
#OUR_DETAIL.address - #OUR_DETAIL.postal_code #OUR_DETAIL.city - #OUR_DETAIL.tel1 #OUR_DETAIL.tel2 #OUR_DETAIL.email{[br/]}#OUR_DETAIL.identify_number
{[/italic]}
</text>
</bottom>
<body>
<text height="8.0" width="120.0" top="0.0" left="0.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="center" line_height="15" font_family="sans-serif" font_weight="" font_size="15">
{[b]}%(tax receipt title)s{[/b]}{[br/]}
{[font size="10"]}{[i]}%(legal reference)s{[/i]}{[/font]}
</text>
<text height="8.0" width="60.0" top="0.0" left="130.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="left" line_height="13" font_family="sans-serif" font_weight="" font_size="11">
%(Number receipt)s : {[b]}#num{[/b]}{[br/]}
%(Year)s : {[b]}#year{[/b]}
</text>
<text height="20.0" width="190.0" top="20.0" left="0.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="center" line_height="12" font_family="sans-serif" font_weight="" font_size="10">
{[font size="15"]}{[b]}{[u]}%(contributor)s{[/u]}{[/b]}{[/font]}{[br/]}
{[b]}#third.contact.str{[/b]}{[br/]}#third.contact.address{[br/]}#third.contact.postal_code #third.contact.city
</text>
<text height="15.0" width="170.0" top="45.0" left="10.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="left" line_height="10" font_family="sans-serif" font_weight="" font_size="9">
%(text recipient)s : {[b]}***#total***{[/b]}{[br/]}
{[br/]}
%(Date payoff)s : {[b]}#date_payoff{[/b]}{[br/]}
%(Mode payoff)s : {[b]}#mode_payoff{[/b]}{[br/]}
</text>
<text height="15.0" width="60.0" top="60.0" left="130.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2" text_align="right" line_height="10" font_family="sans-serif" font_weight="" font_size="9">
#date{[br/]}
%(signature)s
</text>
<image height="20.0" width="20.0" top="70.0" left="160.0" padding="1.0" spacing="0.0" border_color="black" border_style="" border_width="0.2">
#DEFAULT_DOCUMENTS.signature
</image>
</body>
</model>
""" % {
        'tax receipt title': _('Tax receipt for donation'),
        'legal reference': _('legal reference'),
        'Number receipt': _('Number receipt'),
        'Year': _('Year'),
        'contributor': _('CONTRIBUTOR'),
        'text recipient': _('Recipient acknowledges receipt of donations'),
        'Date payoff': _('Date payoff'),
        'Mode payoff': _('Mode payoff'),
        'signature': _('Signature')
}
