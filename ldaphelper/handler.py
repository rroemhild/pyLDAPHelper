# -*- coding: utf-8 -*-

"""
ldaphelper.handler
~~~~~~~~~~~~~~~~~~

This module provides a simple handler for the
python-ldap module.

Part of LDAPHelper: A simple LDAP helper module

:copyright: (c) 2012 Rafael Römhild
:license: MIT, see LICENSE for more details.
"""

import logging

import ldap
import ldap.dn
import ldap.filter
import ldap.modlist

from ldaphelper.entry import LDAPEntry


log = logging.getLogger(__name__)
try:
    log.addHandler(logging.NullHandler())
except:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass


class LDAPHandler(object):
    """Handle the communication with an LDAP server.

    .. code-block:: python

        from ldaphelper import LDAPHandler
        con = LDAPHandler('ldaps://localhost/', 'cn=admin,dc=domain,dc=tld',
                          'secret')
        con.search('dc=domain,dc=tld', '(objectClass=*)', ['cn'])

    :param uri: LDAP URI ldaps://localhost/
    :param binddn: DN to bind with, default is None (anonymous)
    :param secret: Secret to bind with, default is None (anonymous)
    :param timeout: Connection timeout
    :param refferral: Whether to follow refferals or not, default always

    """
    def __init__(self, uri, binddn='', secret='', timeout=10,
                 referral=ldap.DEREF_ALWAYS):
        self._ldap = None
        self._ldap_uri = uri
        self._ldap_binddn = binddn
        self._ldap_secret = secret
        self._ldap_timeout = timeout
        self._ldap_referral = referral
        self._error = None

    def get_uri(self):
        """Return the LDAP URI for the object."""
        return self._ldap_uri

    def get_binddn(self):
        """Return the binddn for the LDAP object."""
        return self._ldap_binddn

    def get_error(self):
        """Return the latest error message."""
        return self._error

    def set_uri(self, val):
        """Set a new URI. Use ldaps:// for TLS session.

        :param val: A valid ldap URI (ldaps://localhost)

        """
        self._ldap_uri = val

    def set_binddn(self, val):
        """Set the binddn.

        :param val: The DN to bind with the LDAP server.

        """
        self._ldap_binddn = val

    def set_secret(self, val):
        """Set the secret for the bindDN.

        :param val: BindDN secret.

        """
        self._ldap_secret = val

    def bind(self):
        """Setup the connection to the LDAP server."""
        if not self._ldap:
            log.debug('Connect to LDAP Server %s.', self._ldap_uri)
            ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
            ldap.set_option(ldap.OPT_DEREF, ldap.DEREF_ALWAYS)

            if not self._ldap_referral == ldap.DEREF_ALWAYS:
                ldap.set_option(ldap.OPT_REFERRALS, self._ldap_referral)

            if self._ldap_uri.startswith('ldaps'):
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
                ldap.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)

            ldapcon = ldap.initialize(self._ldap_uri)
            ldapcon.timeout = int(self._ldap_timeout)

            try:
                ldapcon.simple_bind_s(self._ldap_binddn, self._ldap_secret)
            except ldap.INVALID_CREDENTIALS:
                self._error = 'Username or password incorrect.'
                log.error(self._error)
            except ldap.SERVER_DOWN:
                self._error = 'LDAP Server %s down.' % self._ldap_uri
                log.error(self._error)
            except ldap.LDAPError, error:
                self._error = 'LDAP connect error: %s.' % error
                log.error(self._error)

            self._ldap = ldapcon
        # if we are connected, return connection handler
        return self._ldap

    def unbind(self):
        """Disconnect from the LDAP server."""
        if self._ldap:
            log.debug('Disconnect from LDAP Server.')
            self._ldap.unbind_s()
            self._ldap = None

    def add(self, entry, modlist):
        """Add an entry to the directory.

        This method normaly is called by the self.update() method.

        :param entry: The LDAPEntry object to modify.
        :param modlist: A modlist from ldap.modlist.modifyModlist

        """
        log.info('Add new LDAP entry: %s.', entry.get_dn())
        try:
            self.bind()
            self._ldap.add_s(entry.get_dn(), modlist)
        except ldap.LDAPError, error:
            self._error = 'LDAP add entry error: %s.' % error
            log.error(self._error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            log.error(self._error)

    def modify(self, entry, modlist):
        """Modify an LDAP entry.

        This method normaly is called by the self.update() method.

        :param entry: The LDAPEntry object to modify.
        :param modlist: A modlist from ldap.modlist.modifyModlist

        """
        log.info('Modify existing LDAP entry: %s.', entry.get_dn())
        try:
            self.bind()
            self._ldap.modify_s(entry.get_dn(), modlist)
        except ldap.REFERRAL, error:
            log.error('Can not handle refferral: %s', error)
        except ldap.LDAPError, error:
            log.error('LDAP modify entry error: %s.', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            log.error(self._error)

    def delete(self, entry):
        """Delete an entry from the directory.

        :param entry: A LDAP entry tuple. Could be a ldaputils.entry.LDAPEntry
                      object or a string with an DN.

        """
        dn = None
        try:
            if isinstance(entry, str):
                dn = entry
            elif isinstance(entry, LDAPEntry):
                dn = entry.get_dn()

            self.bind()
            self._ldap.delete_s(dn)
            self.unbind()
            log.info('LDAP entry "%s" removed.', dn)
        except ldap.LDAPError, error:
            log.error('LDAP delete error: %s.', error)
        except ldap.DECODING_ERROR:
            log.error('%s is not a valid DN.', dn)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            log.error(self._error)

    def rename(self, dn, newrdn, newsuperior=None, delold=1):
        """Moving a DN in the tree or rename the rdn.

        :param dn: DN from the entry to rename.
        :param newrdn: New RDN for the entry.
        :param newsuperior: New parent DN if move in the tree.
        :param delold: Keep or delete the old rdn as an attribute of the entry.

        """
        try:
            self.bind()
            self._ldap.rename_s(dn, newrdn, newsuperior, delold)
            self.unbind()
            log.info(
                'Renamed dn "%s" to "%s,%s".', dn, newrdn, newsuperior)
        except ldap.LDAPError, error:
            log.error('Can not rename dn %s', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            log.error(self._error)

    def search(self, basedn, search_filter='(objectClass=*)',
               retrieve_attrs=list(), search_scope=ldap.SCOPE_SUBTREE,
               raw=False):
        """Perform an LDAP search on the directory.

        :param basedn: The base as the DN of the entry at which
                       to start the search.
        :param search_filter: LDAP search filter.
        :param retrieve_attrs: List of attributes to receive.
        :param search_scope: LDAP search scope. Default is SUBTREE.
        :param raw: Return the raw search result from ldap.search_s().

        """
        search_result = []
        log.debug('Perform LDAP search.')
        try:
            self.bind()
            search_result = self._ldap.search_s(basedn, search_scope,
                                                search_filter,
                                                retrieve_attrs)
            self.unbind()
            log.debug('LDAP search result: %s.', search_result)
        except ldap.FILTER_ERROR, error:
            log.error('LDAP searchFilter error: %s.', error)
            log.error('searchFilter: %s', search_filter)
        except ldap.PROTOCOL_ERROR, error:
            log.error('LDAP Protocol error: %s.', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            log.error(self._error)

        if raw:
            return search_result

        return map(LDAPEntry, search_result)

    def update(self, entries, dry_run=False):
        """Add or modify one ore more LDAPEntry objects.

        :param entries: List with LDAPEntry objects or a single LDAPEntry.
        :param dry_run: If True perform a trial run with no changes made.

        """
        if not isinstance(entries, list):
            entries = [entries]

        for entry in entries:
            modlist = []
            try:
                dn_str = entry.get_dn()
                basedn = ','.join(ldap.dn.explode_dn(dn_str)[1:])
                rdn = ldap.dn.explode_dn(dn_str)[:1][0]
                orig_dn = self.search(basedn, rdn, raw=True)
            except Exception:
                log.error('DN is not valid.')
                # TODO: Raise error
                return False

            if orig_dn:
                orig_dn = orig_dn[0]
                new = orig_dn[1].copy()
                new.update(entry._attrs)
                modlist = ldap.modlist.modifyModlist(orig_dn[1], new)
                if modlist:
                    self.modify(entry, modlist)
                else:
                    log.debug('Nothing to modify.')
            else:
                modlist = ldap.modlist.addModlist(entry._attrs)
                if modlist:
                    self.add(entry, modlist)
                else:
                    log.debug('Nothing to add.')

            if self._ldap:
                self.unbind()
