pyLDAPHelper
############

``ldaphelper`` is a simple Python module/package based on
`python-ldap <http://www.python-ldap.org/>`_ that make my Life as an LDAP
operator easier. I use it in a lot of scripts for automatic or
manual manage of LDAP entries.

At this point you should consider ldaphelper to be experimental, and there
are likely plenty of bugs and missing features to address, so please file
them as you run into them on the
`issue tracker <https://github.com/rroemhild/pyLDAPHelper/issues>`_.


Requirements
============

- python 2.6 or newer
- python-ldap


Install
=======

From Github
-----------

Get the latest code from Github::

    pip install -r http://github.com/rroemhild/pyLDAPHelper/raw/master/requirements_pip.txt


Examples
========

Change titles
-------------

Change the ``title`` for developers from *Developer* to *Development*::

	from ldaphelper import LDAPHelper

	uri = 'ldaps://localhost'
	basedn = 'dc=example,dc=tld'
	binddn = 'uid=admin,' + basedn
	secret = 'AdminSecret'
	ldapcon = LDAPHelper(uri, binddn, secret)

	searchdn = 'ou=people,' + basedn
	searchfilter = '(&(objectClass=inetOrgPerson)(title=Developer))'
	attributes = ['uid', 'displayName', 'title']
	entries = ldapcon.search(searchdn, searchfilter, attributes)

	for entry in entries:
		print "Set new title for %s." entry.get('title')
		entry.set('title', 'Development')

	ldapcon.update(entries)


Make a CSV list
---------------

Get a CSV list from your eymployees with givenname, surname and email::

    from ldaphelper import LDAPHandler

    uri = 'ldaps://localhost'
    basedn = 'ou=people,dc=example,dc=tld'
	binddn = 'cn=admin,dc=example,dc=tld'
	secret = 'AdminSecret'
    ldapcon = LDAPHelper(uri, binddn, secret)

    searchfilter = '(&(objectClass=inetOrgPerson)(active=1))'
    attributes = ['givenName', 'sn', 'mail']
    entries = ldapcon.search(basedn, searchfilter, attributes)

    for entry in entries:
        print '"%s","%s","%s"' % (entry.get('givenName')[0],
                                  entry.get('sn')[0],
                                  entry.get('mail')[0])


Author
======

Rafael Römhild (rafael@roemhild.de)

