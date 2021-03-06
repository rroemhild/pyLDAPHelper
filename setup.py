#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ldaphelper
~~~~~~~~~~

ldaphelper is a simple Python helper module for
dealing with LDAP server based on python-ldap.

:copyright: (c) 2012 Rafael Römhild
:license: MIT, see LICENSE for more details.
"""

from setuptools import setup


setup(
    name = 'ldaphelper',
    version = '0.1.1',
    author = 'Rafael Römhild',
    author_email = 'rafael@roemhild.de',
    description = 'Simple helper module for python-ldap.',
    license = 'MIT',
    packages = ['ldaphelper'],
    url = 'http://github.com/rroemhild/pyLDAPHelper',
    keywords = ['ldap'],
    long_description = '__doc__',
    install_requires = ['python-ldap >= 2.4.19'],
    classifiers = [
        'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
