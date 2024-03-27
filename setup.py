# -*- coding: utf-8 -*-
'''
setup module to pip integration of Diacamma asso

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


from setuptools import setup
from diacamma.asso import __version__

setup(
    name="diacamma-asso",
    version=__version__,
    author="Lucterios",
    author_email="info@diacamma.org",
    url="http://www.diacamma.fr",
    description="association application.",
    long_description="""
    Association application with Lucterios framework.
    """,
    include_package_data=True,
    platforms=('Any',),
    license="GNU General Public License v3",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 4.2',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Natural Language :: French',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Database :: Front-Ends',
        'Topic :: Office/Business :: Financial',
    ],
    # Packages
    packages=["diacamma", "diacamma.asso",
              "diacamma.member", "diacamma.event"],
    install_requires=["lucterios ~=2.7", "lucterios-contacts ~=2.7", "diacamma-financial"],
)
