# -*- coding: utf-8 -*-

'''
ldaphelper.utils
~~~~~~~~~~~~~~~~

This module provides helper methods
in combination with LDAPHandler.

Part of LDAPHelper: A simple LDAP helper module

:copyright: (c) 2012 Rafael Römhild
:license: MIT, see LICENSE for more details.
'''

from ldaphelper.handler import LDAPHandler


def authenticate(uri, binddn='', secret='', timeout=10, referrals=''):
    '''
    This method provides a simple user authentification.

    :param uri:
    :param binddn:
    :param secret:
    :param timeout:
    :param referrals:
    '''
    ldapcon = LDAPHandler(uri, binddn, secret, timeout, referrals)
    if ldapcon.bind():
        ldapcon.unbind()
        return True
    else:
        return ldapcon.get_error()


def list_of_attr(ldaphandler, attr, basedn, search_filter=None, sort=True):
    '''
    This method returns a list with the values from one attribute. This is
    helpfull if you i.e. just need all locations.

    .. code-block:: python

        from ldaputils import LDAPHandler
        from ldaputils.helper import list_of_entries
        con = LDAPHandler('ldaps://ldap1', 'cn=test,dc=domain,dc=tld', 's3Cr3t')
        basedn = 'ou=people,dc=domain,dc=tld'
        search_filter = '(active=1)'
        retlist = list_of_entries(con, 'uid', basedn, search_filter)
        print retlist

    :param ldaphandler: An LDAPHandler object.
    :param attr: The attribute to return
    :param search_filter: LDAP Serch filter (objectClass=*)
    :param retrieve_attrs:List with attributes to receive.
    :param sort: Tries to sort the list bevor return it.
    '''

    if not search_filter and attr == 'dn':
        search_filter = '(objectClass=*)'
    elif search_filter and attr == 'dn':
        search_filter = search_filter
    elif search_filter:
        search_filter = '(& (%s=*) %s )' % (attr, search_filter)
    else:
        search_filter = '%s=*' % attr

    entries = []
    results = ldaphandler.search(basedn, search_filter, [attr])

    if results:
        for entry in results:
            if attr == 'dn':
                entries.append(entry[0])
            else:
                entries.append(entry[1][attr][0])
        if sort:
            entries.sort()

    return entries
