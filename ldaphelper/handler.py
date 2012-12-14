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

import ldap
import ldap.dn
import ldap.filter
import ldap.modlist
import logging

from ldaphelper.entry import LDAPEntry


class LDAPHandler(object):
    """
    Class to handle the communication with an LDAP server.

    .. code-block:: python

        from ldaphelper import LDAPHandler
        con = LDAPHandler('ldaps://localhost/', 'cn=admin,dc=domain,dc=tld',
                          'secret')
        con.search('dc=domain,dc=tld', '(objectClass=*)', ['cn'])

    :param uri: LDAP URI ldaps://localhost/
    :param binddn: DN to bind with, default is None (anonymous)
    :param secret: Secret to bind with, default is None (anonymous)
    :param timeout: Connection timeout
    """

    def __init__(self, uri, binddn='', secret='', timeout=10, referrals=''):
        self._ldap = None
        self._ldap_uri = uri
        self._ldap_binddn = binddn
        self._ldap_secret = secret
        self._ldap_timeout = timeout
        self._ldap_referrals = referrals
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
            logging.debug("Connect to LDAP Server %s.", self._ldap_uri)
            ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
            ldap.set_option(ldap.OPT_DEREF, ldap.DEREF_ALWAYS)

            if self._ldap_referrals is None:
                ldap.set_option(ldap.OPT_REFERRALS, ldap.DEREF_NEVER)
            else:
                ldap.set_option(ldap.OPT_REFERRALS, self._ldap_referrals)

            if self._ldap_uri.startswith('ldaps'):
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
                ldap.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)

            ldapcon = ldap.initialize(self._ldap_uri)
            ldapcon.timeout = int(self._ldap_timeout)

            try:
                ldapcon.simple_bind_s(self._ldap_binddn, self._ldap_secret)
            except ldap.INVALID_CREDENTIALS:
                self._error = "Username or password incorrect."
                logging.error(self._error)
            except ldap.SERVER_DOWN:
                self._error = "LDAP Server %s down." % self._ldap_uri
                logging.error(self._error)
            except ldap.LDAPError, error:
                self._error = "LDAP connect error: %s." % error
                logging.error(self._error)

            self._ldap = ldapcon
        # if we are connected, return connection handler
        return self._ldap

    def unbind(self):
        """Disconnect from the LDAP server."""
        if self._ldap:
            logging.debug("Disconnect from LDAP Server.")
            self._ldap.unbind_s()
            self._ldap = None

    def add(self, entry, modlist):
        """
        Add an entry to the directory.

        This method normaly is called by the self.update() method.

        :param entry: The LDAPEntry object to modify.
        :param modlist: A modlist from ldap.modlist.modifyModlist
        """
        logging.info("Add new LDAP entry: %s.", entry.get_dn())
        try:
            self.bind()
            self._ldap.add_s(entry.get_dn(), modlist)
        except ldap.LDAPError, error:
            self._error =  'LDAP add entry error: %s.' % error
            logging.error(self._error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            logging.error(self._error)

    def modify(self, entry, modlist):
        """
        Modify an LDAP entry.

        This method normaly is called by the self.update() method.

        :param entry: The LDAPEntry object to modify.
        :param modlist: A modlist from ldap.modlist.modifyModlist
        """
        logging.info("Modify existing LDAP entry: %s.", entry.get_dn())
        try:
            self.bind()
            self._ldap.modify_s(entry.get_dn(), modlist)
        except ldap.REFERRAL, error:
            logging.error('Can not handle refferral: %s', error)
        except ldap.LDAPError, error:
            logging.error('LDAP modify entry error: %s.', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            logging.error(self._error)

    def delete(self, entry):
        """
        Delete an entry from the directory.

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
            logging.info('LDAP entry "%s" removed.', dn)
        except ldap.LDAPError, error:
            logging.error('LDAP delete error: %s.', error)
        except ldap.DECODING_ERROR:
            logging.error('%s is not a valid DN.', dn)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            logging.error(self._error)

    def rename(self, dn, newrdn, newsuperior=None, delold=1):
        """
        Moving a DN in the tree or rename the rdn.

        :param dn: DN from the entry to rename.
        :param newdn: New RDN for the entry.
        :param newsuperior: New parent DN if move in the tree.
        :param delold: Keep or delete the old rdn as an attribute of the entry.
        """
        try:
            self.bind()
            self._ldap.rename_s(dn, newrdn, newsuperior, delold)
            self.unbind()
            logging.info(
                'Renamed dn "%s" to "%s,%s".', dn, newrdn, newsuperior)
        except ldap.LDAPError, error:
            logging.error('Can not rename dn %s', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            logging.error(self._error)

    def search(self, basedn, search_filter='(objectClass=*)',
               retrieve_attrs=list(), search_scope=ldap.SCOPE_SUBTREE,
               raw=False):
        """
        Perform an LDAP search on the directory.

        :param basedn: The base as the DN of the entry at which
                       to start the search.
        :param search_filter: LDAP search filter.
        :param retrieve_attrs: List of attributes to receive.
        :param search_scope: LDAP search scope. Default is SUBTREE.
        :param raw: Return the raw search result from ldap.search_s().
        """
        search_result = []
        logging.debug('Perform LDAP search.')
        try:
            self.bind()
            search_result = self._ldap.search_s(basedn, search_scope,
                                                search_filter,
                                                retrieve_attrs)
            self.unbind()
            logging.debug('LDAP search result: %s.', search_result)
        except ldap.FILTER_ERROR, error:
            logging.error('LDAP searchFilter error: %s.', error)
            logging.error('searchFilter: %s', search_filter)
        except ldap.PROTOCOL_ERROR, error:
            logging.error('LDAP Protocol error: %s.', error)
        except ldap.SERVER_DOWN:
            self._error = 'LDAP Server %s down.' % self._ldap_uri
            logging.error(self._error)

        if raw:
            return search_result

        return map(LDAPEntry, search_result)

    def update(self, entries):
        """
        Add or modify one ore more LDAPEntry objects.

        :param entries: List with LDAPEntry objects or a single LDAPEntry.
        """
        if not isinstance(entries, list):
            entries = [entries]

        for entry in entries:
            modlist = []
            try:
                # TODO: Use dn2str instead of explode_dn
                explode_dn = ldap.explode_dn(entry.get_dn())
                orig_dn = self.search(','.join(explode_dn[1:]), '(%s)' %
                                      explode_dn[:1][0], raw=True)
            except:
                logging.error('DN is not valid.')
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
                    logging.debug('Nothing to modify.')
            else:
                modlist = ldap.modlist.addModlist(entry._attrs)
                if modlist:
                    self.add(entry, modlist)
                else:
                    logging.debug('Nothing to add.')

            if self._ldap:
                self.unbind()
