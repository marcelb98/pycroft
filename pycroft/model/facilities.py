# -*- coding: utf-8 -*-
# Copyright (c) 2015 The Pycroft Authors. See the AUTHORS file.
# This file is part of the Pycroft project and licensed under the terms of
# the Apache License, Version 2.0. See the LICENSE file for details.
"""
    pycroft.model.dormitory
    ~~~~~~~~~~~~~~

    This module contains the classes Dormitory, Room, Subnet, VLAN.

    :copyright: (c) 2011 by AG DSN.
"""

import ipaddr
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Table, Column
from sqlalchemy.orm import backref, object_session, relationship
from sqlalchemy.types import Boolean, Integer, String, Enum
from pycroft.model.base import ModelBase


association_table_dormitory_vlan = Table(
    'association_dormitory_vlan',
    ModelBase.metadata,
    Column('dormitory_id', Integer, ForeignKey('dormitory.id')),
    Column('vlan_id', Integer, ForeignKey('vlan.id')))

association_table_subnet_vlan = Table(
    "association_subnet_vlan",
    ModelBase.metadata,
    Column("subnet_id", Integer, ForeignKey("subnet.id")),
    Column("vlan_id", Integer, ForeignKey("vlan.id")))


class Dormitory(ModelBase):
    number = Column(String(3), nullable=False)
    short_name = Column(String(5), unique=True, nullable=False)
    street = Column(String(20), nullable=False)

    __table_args__ = (UniqueConstraint("street", "number", name="address"),)

    # many to many from Dormitory to VLAN
    vlans = relationship("VLAN", backref=backref("dormitories"),
                         secondary=association_table_dormitory_vlan)

    @property
    def subnets(self):
        return object_session(self).query(
            Subnet
        ).join(
            Subnet.vlans
        ).join(
            VLAN.dormitories
        ).filter(
            Dormitory.id == self.id
        ).all()

    def __repr__(self):
        return u"{} {}".format(self.street, self.number)


class Room(ModelBase):
    number = Column(String(36), nullable=False)
    level = Column(Integer, nullable=False)
    inhabitable = Column(Boolean, nullable=False)

    # many to one from Room to Dormitory
    dormitory_id = Column(Integer, ForeignKey(Dormitory.id), nullable=False)
    dormitory = relationship(Dormitory, backref=backref("rooms"))

    def __repr__(self):
        return u"{} {:d}{}".format(self.dormitory, self.level, self.number)


class VLAN(ModelBase):
    name = Column(String(127), nullable=False)
    tag = Column(Integer, nullable=False)


class Subnet(ModelBase):
    #address = Column(postgresql.INET, nullable=False)
    address = Column(String(51), nullable=False)
    #gateway = Column(postgresql.INET, nullable=False)
    gateway = Column(String(51), nullable=False)
    dns_domain = Column(String)
    reserved_addresses = Column(Integer, default=0, nullable=False)
    ip_type = Column(Enum("4", "6", name="subnet_ip_type"), nullable=False)

    # many to many from Subnet to VLAN
    vlans = relationship(VLAN, backref=backref("subnets"),
                         secondary=association_table_subnet_vlan)

    @property
    def netmask(self):
        net = ipaddr.IPNetwork(self.address)
        return str(net.netmask)

    @property
    def ip_version(self):
        return ipaddr.IPNetwork(self.address).version