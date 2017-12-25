# -*- coding: utf-8 -*-
# Copyright (c) 2016 The Pycroft Authors. See the AUTHORS file.
# This file is part of the Pycroft project and licensed under the terms of
# the Apache License, Version 2.0. See the LICENSE file for details.
from factory import SubFactory, LazyAttribute, Sequence
from factory.faker import Faker

from pycroft.model.facilities import Site, Building, Room
from .base import BaseFactory


class SiteFactory(BaseFactory):
    class Meta:
        model = Site

    name = Faker('street_name')


class BuildingFactory(BaseFactory):
    class Meta:
        model = Building

    site = SubFactory(SiteFactory)

    number = Sequence(lambda n: n)
    street = LazyAttribute(lambda b: b.site.name)
    short_name = LazyAttribute(lambda b: "{}{}".format(b.street[:3], b.number))


class RoomFactory(BaseFactory):
    class Meta:
        model = Room

    number = Faker('numerify', text='## #')
    level = Faker('random_int', min=0, max=16)
    inhabitable = Faker('boolean')

    building = SubFactory(BuildingFactory)
