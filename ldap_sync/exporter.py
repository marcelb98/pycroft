# -*- coding: utf-8; -*-

import logging
import os
import sys
from collections import Counter, defaultdict, namedtuple

import ldap3
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker

from pycroft.model.user import User
from pycroft.model.session import set_scoped_session, session as global_session
from .record import Record, RecordState

logger = logging.getLogger('ldap_sync')


class LdapExporter(object):
    """The ldap Exporter

    Usage:

        >>> from ldap_sync.record import Record
        >>> record = Record(dn='cn=admin,ou=users,dc=agdsn,dc=de', attrs={})
        >>> exporter = LdapExporter(current=[], desired=[record])
        >>> exporter.compile_actions()
        >>> exporter.execute_all()

    Since the desired state is to be represented by a postgres
    database and the current state by the LDAP being synced to,
    :py:meth:`from_orm_objects_and_ldap_result` is there to not
    have to convert the entries to :py:cls:`Record`s manually.

    :param iterable current: An iterable of :py:cls:`Record`s
    :param iterable desired: An iterable of the desired
        :py:cls:`Record`s
    """
    RecordState = RecordState
    Record = Record

    def __init__(self, current, desired):
        self.states_dict = defaultdict(self.RecordState)
        for record in current:
            self.states_dict[record.dn].current = record
        for record in desired:
            self.states_dict[record.dn].desired = record
        self.actions = []

    @classmethod
    def from_orm_objects_and_ldap_result(cls, current, desired, base_dn):
        """Construct an exporter instance with non-raw parameters

        :param cls:
        :param current: An iterable of records as returned by
            ldapsearch
        :param desired: An iterable of sqlalchemy objects
        """
        return cls((cls.Record.from_ldap_record(x) for x in current),
                   (cls.Record.from_db_user(x, base_dn) for x in desired))

    def compile_actions(self):
        """Consolidate current and desired records into necessary actions"""
        if self.actions:
            raise RuntimeError("Actions can only be compiled once")
        for state in self.states_dict.values():
            self.actions.append(state.desired - state.current)

    def execute_all(self, *a, **kw):
        for action in self.actions:
            action.execute(*a, **kw)


def establish_and_return_session(connection_string):
    engine = create_engine(connection_string)
    set_scoped_session(scoped_session(sessionmaker(bind=engine)))
    return global_session  # from pycroft.model.session


def fetch_users_to_sync(session, required_property=None):
    """Fetch the users who should be synced

    :param session: The SQLAlchemy session to use

    :returns: A list of :py:cls:`User` objects having the property
              'mail' having a unix_account.
    """
    property_filter = True  # idempotent on `.filter()`
    if required_property is not None:
        property_filter = User.has_property(required_property)
    count_mail_but_not_account = (
        session.query(func.count(User.id))
        .filter(property_filter, User.unix_account == None)
        .scalar()
    )
    if required_property:
        logger.warning("%s users have the '%s' property but not a unix_account",
                       count_mail_but_not_account, required_property)
    else:
        logger.warning("%s users applicable to exporting don't have a unix_account",
                       count_mail_but_not_account)

    return User.q.filter(property_filter, User.unix_account != None).all()


def establish_and_return_ldap_connection(host, port, bind_dn, bind_pw):
    server = ldap3.Server(host=host, port=port)
    return ldap3.Connection(server, user=bind_dn, password=bind_pw, auto_bind=True)


def fetch_current_ldap_users(connection, base_dn):
    success = connection.search(search_base=base_dn,
                                search_filter='(objectclass=*)',
                                attributes=ldap3.ALL_ATTRIBUTES)
    if not success:
        logger.warning("LDAP search not successful.  Result: %s", connection.result)
        return []

    return [r for r in connection.response if r['dn'] != base_dn]


def fake_connection():
    server = ldap3.Server('mocked')
    connection = ldap3.Connection(server, client_strategy=ldap3.MOCK_SYNC)
    connection.open()
    return connection


def add_stdout_logging(logger, level=logging.INFO):
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(levelname)s %(asctime)s %(name)s %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(level)


def sync_all(db_users, ldap_users, connection, base_dn):
    """Execute the LDAP sync given a connection and state data.

    :param db_users: A list of ORM objects corresponding to the users
        to be synced
    :param ldap_users: An LDAP search result representing the current
        set of users
    :param connection: An LDAP connection
    :param base_dn: The LDAP base_dn
    """
    exporter = LdapExporter.from_orm_objects_and_ldap_result(current=ldap_users,
                                                             desired=db_users,
                                                             base_dn=base_dn)
    logger.info("Initialized LdapExporter (%s unique objects in total) from fetched objects",
                len(exporter.states_dict))

    exporter.compile_actions()
    action_types = Counter((type(a).__name__ for a in exporter.actions))
    logger.info("Compiled %s actions (%s)", len(exporter.actions),
                ", ".join("{}: {}".format(type_, count)
                          for type_, count in action_types.items()))

    logger.info("Executing actions")
    exporter.execute_all(connection)
    logger.info("Executed %s actions", len(exporter.actions))



_sync_config = namedtuple(
    'LdapSyncConfig',
    ['host', 'port', 'bind_dn', 'bind_pw', 'base_dn', 'db_uri', 'required_property']
)


def _from_environ_or_defaults(key, defaults):
    try:
        return os.environ['PYCROFT_LDAP_{}'.format(key.upper())]
    except KeyError as e:
        if key not in defaults:
            print("defaults:", defaults)
            raise ValueError("Missing configuration key {}".format(key)) from e
        return defaults[key]


def get_config(**defaults):
    config_dict = {
        # e.g. 'host': 'PYCROFT_LDAP_HOST'
        key: _from_environ_or_defaults(key, defaults)
        for key in _sync_config._fields if key != 'db_uri'
    }
    config_dict['port'] = int(config_dict['port'])
    config_dict['db_uri'] = os.environ['PYCROFT_DB_URI']
    config = _sync_config(**config_dict)

    return config


def get_config_or_exit(**defaults):
    try:
        return get_config(**defaults)
    except KeyError as exc:
        logger.critical("%s not set, quitting", exc.args[0])
        exit()
