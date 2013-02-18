# -*- coding: utf-8 -*-

'''
ldaphelper.entry
~~~~~~~~~~~~~~~~

This module provides a simple pythonic interface
to an LDAP entry.

Part of pyLDAPHelper: A simple LDAP helper module

:copyright: (c) 2012 Rafael Römhild
:license: MIT, see LICENSE for more details.
'''

import sys
import ldap
import logging

from ldif import LDIFWriter


class LDAPEntry(object):

    '''
    Base class for LDAP entries.

    Typical use pattern:

    .. code-block:: python

        entries = map(LDAPEntry, LDAPHandler.search())
        for entry in entries:
            print entry.get_dn()

    :param entry: An LDAP search result tuple (dn, entry).
    '''

    def __init__(self, entry=list()):
        self._dn = ''
        self._attrs = ldap.cidict.cidict()

        if entry and len(entry) == 2:
            self._update(entry)

    def __str__(self):
        '''
        Return the entry DN.
        '''
        return 'DN: %s' % self.get_dn()

    def _update(self, entry):
        '''
        Update object with an search result tuple (dn, entry).
        '''
        self._dn = entry[0]
        self._attrs.update(entry[1])

    def get_dn(self):
        '''
        Return the DN (distinguished name) from the entry.
        '''
        return self._dn

    def get(self, attr, default=['']):
        '''
        Return the content from an attribute or default.

        Typical use pattern:

        .. code-block:: python

            entries = map(LDAPEntry, LDAPHandler.search())
            for entry in entries:
                print entry.givenname
                print entry.get('mail-auto-reply')

        :param attr: Attribute name
        :param default: Default value if attr does not exist.
        '''
        try:
            val = self._attrs[attr]
            if val and len(val) > 0:
                return val
        except KeyError:
            logging.debug('No attribute: %s in entry.', attr)
            if isinstance(default, list):
                return default
            else:
                return [default]

    def set(self, attr, val):
        '''
        Set an attribute from the entry.

        :param attr: LDAP attribute name
        :param val: Value to set for he attribute
        '''
        if isinstance(val, int):
            val = str(val)

        if isinstance(val, str):
            self._attrs.update({attr: [str(val)]})
        elif isinstance(val, list):
            self._attrs.update({attr: val})
        else:
            raise KeyError

    def append(self, attr, val):
        '''
        Add a value to an attribute.
        '''
        try:
            self._attrs[attr].append(val)
            logging.debug('Removed value: %s from attribute: %s.', attr, val)
        except KeyError:
            logging.error('Can not append value: %s to attribute: %s.' \
                          ' Attribute does not exists.', val, attr)
            raise KeyError

    def remove(self, attr, val):
        '''
        Remove a value from an attribute.
        '''
        try:
            self._attrs[attr].remove(val)
        except ValueError:
            logging.error('Value: %s is not in attribute: %s.', attr, val)
        except KeyError:
            logging.error('No attribute: %s in entry.', attr)

    def delete(self, attr):
        '''
        Remove an attribute from the entry.
        '''
        try:
            self._attrs[attr] = []
        except KeyError:
            logging.error('Can not delete attribute: %s. Attribute does' \
                          'not exist.', attr)

    def attributes(self):
        '''
        Return a list with all attributes.
        '''
        return self._attrs.keys()

    def set_dn(self, val):
        '''
        Set the DN for the entry.
        '''
        try:
            dn = ldap.dn.str2dn(val)
            self._dn = ldap.dn.dn2str(dn)
            logging.debug('DN set to: %s.', self._dn)
        except ldap.DECODING_ERROR:
            logging.error('Not a valid DN: %s', self._dn)

    def to_ldif(self, output_file=sys.stdout):
        '''
        Get an LDIF formated output from the LDAP entry.

        :param output_file: Any filehandler object. Default is stdout.
        '''
        ldif_writer = LDIFWriter(output_file)
        ldif_writer.unparse(self._dn, dict(self._attrs))

#    def from_ldif(self, input_file):
#        pass
