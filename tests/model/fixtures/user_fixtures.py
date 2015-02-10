# Copyright (c) 2015 The Pycroft Authors. See the AUTHORS file.
# This file is part of the Pycroft project and licensed under the terms of
# the Apache License, Version 2.0. See the LICENSE file for details.
from datetime import datetime, timedelta
from fixture import DataSet


class DormitoryData(DataSet):
    class dummy_house:
        number = "01"
        short_name = "abc"
        street = "dummy"


class RoomData(DataSet):
    class dummy_room:
        number = 1
        level = 1
        inhabitable = True
        dormitory = DormitoryData.dummy_house


class FinanceAccountData(DataSet):
    class finance_account:
        name = ''
        type = 'ASSET'


class UserData(DataSet):
    class dummy_user:
        login = "test"
        name = "John Doe"
        registered_at = datetime.utcnow()
        room = RoomData.dummy_room
        finance_account = FinanceAccountData.finance_account


class PropertyGroupData(DataSet):
    class dummy_group:
        name = "dummy"


class TrafficGroupData(DataSet):
    class dummy_group:
        name = "dummy"
        traffic_limit = 0


class MembershipData(DataSet):
    class dummy_membership:
        begins_at = datetime.utcnow() - timedelta(hours=1)
        ends_at = datetime.utcnow() + timedelta(hours=1)
        group = PropertyGroupData.dummy_group
        user = UserData.dummy_user


class PropertyData(DataSet):
    class granted:
        property_group = PropertyGroupData.dummy_group
        name = "granted_property"
        granted = True

    class denied:
        property_group = PropertyGroupData.dummy_group
        name = "denied_property"
        granted = False
