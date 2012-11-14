from tests import OldPythonTestCase, FixtureDataTestBase
from random import randint
import ipaddr

from pycroft.lib.hosts import change_mac

from pycroft.helpers.host_helper import sort_ports, generate_hostname, get_free_ip, select_subnet_for_ip, SubnetFullException
from pycroft.model import dormitory, hosts, session, user, logging

from tests.fixtures.hosts_fixtures import DormitoryData, VLanData, SubnetData, RoomData, UserData, UserHostData, UserNetDeviceData


class Test_010_SimpleHostsHelper(OldPythonTestCase):
    def test_0010_sort_ports(self):
        ports = []
        for letter in ["A", "B", "C", "D", "E", "F", "G"]:
            for number in range(1, 24):
                ports.append("%s%d" % (letter, number))

        class fake_port(object):
            def __init__(self, name):
                self.name = name

        pool = list(ports)
        shuffled = []
        for selected in range(0, len(ports)):
            idx = randint(0, len(pool) - 1)
            shuffled.append(fake_port(pool[idx]))
            del pool[idx]
        resorted = [p.name for p in sort_ports(shuffled)]
        self.assertEqual(resorted, ports)

    def test_0020_generate_hostname(self):
        networks = ["141.30.228", "10.10.10", "141.30.126"]
        for hostpart in range(1, 255):
            for net in networks:
                expected = "whdd%d" % hostpart
                generated = generate_hostname("%s.%d" % (net, hostpart))
                self.assertEqual(generated, expected)


class Test_020_IpHelper(FixtureDataTestBase):
    datasets = [DormitoryData, VLanData, SubnetData, RoomData, UserData, UserHostData, UserNetDeviceData]

    def ip_s1(self, num):
        net_parts = SubnetData.subnet1.gateway.split(".")
        net_parts[3] = str(1 + SubnetData.subnet1.reserved_addresses + num)
        return '.'.join(net_parts)

    def ip_s2(self, num):
        net_parts = SubnetData.subnet2.gateway.split(".")
        net_parts[3] = str(1 + SubnetData.subnet2.reserved_addresses + num)
        return '.'.join(net_parts)

    def test_0010_get_free_ip_simple(self):
        subnets = dormitory.Subnet.q.order_by(dormitory.Subnet.gateway).all()
        ip = get_free_ip(subnets)
        self.assertEqual(ip, self.ip_s1(0))

    def test_0020_select_subnet_for_ip(self):
        subnets = dormitory.Subnet.q.order_by(dormitory.Subnet.gateway).all()
        for subnet in subnets:
            for ip in ipaddr.IPNetwork(subnet.address).iterhosts():
                selected = select_subnet_for_ip(ip.compressed, subnets)
                self.assertEqual(subnet, selected)

    def test_0030_get_free_ip_next_to_full(self):
        subnets = dormitory.Subnet.q.order_by(dormitory.Subnet.gateway).all()
        host = hosts.Host.q.filter(hosts.Host.id == UserHostData.dummy_host1.id).one()

        nd = hosts.UserNetDevice(mac="00:00:00:00:00:00", host = host)
        for num in range(0, 490):
            if num >= 488:
                self.assertRaises(SubnetFullException, get_free_ip, subnets)
                continue
            ip = get_free_ip(subnets)
            net = select_subnet_for_ip(ip, subnets)
            if num < 244:
                self.assertEqual(ip, self.ip_s1(num))
            else:
                self.assertEqual(ip, self.ip_s2(num % 244))

            ip_addr = hosts.Ip(address=ip, subnet=net, net_device=nd)
            session.session.add(ip_addr)
            session.session.commit()

        hosts.Ip.q.filter(hosts.Ip.net_device == nd).delete()
        session.session.delete(nd)
        session.session.commit()


class Test_030_change_mac_net_device(FixtureDataTestBase):
    datasets = [UserNetDeviceData, UserData]

    def setUp(self):
        super(Test_030_change_mac_net_device, self).setUp()
        self.processing_user = user.User.q.get(1)
        self.dummy_device = hosts.UserNetDevice.q.get(1)

    def tearDown(self):
        logging.LogEntry.q.delete()
        session.session.commit()
        super(Test_030_change_mac_net_device, self).tearDown()

    def test_0010_change_mac(self):
        new_mac = "20:00:00:00:00:00"
        change_mac(self.dummy_device, new_mac, self.processing_user)
        self.assertEqual(self.dummy_device.mac, new_mac)



