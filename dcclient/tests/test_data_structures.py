# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testtools
import dcclient.xml_manager.data_structures as ds


class MainTest(testtools.TestCase):
    def test_pbits(self):
        # test constructor consistency
        int_cons = ds.Pbits(9)
        list_cons = ds.Pbits([1, 4])

        self.assertIs(9, int_cons.bits)
        self.assertIs(9, list_cons.bits)

        # test auxiliary methods
        list_cons.add_bits([2, 3])
        self.assertIs(15, list_cons.bits)

        list_cons = list_cons+[5]
        self.assertIs(31, list_cons.bits)

        list_cons = list_cons-[5]
        self.assertIs(15, list_cons.bits)

        list_cons.remove_bits([1, 4])
        self.assertIs(6, list_cons.bits)

        # test xml
        expected_xml = '<pbits id0="0">6</pbits>'
        actual_xml = list_cons.as_xml_text()
        self.assertEquals(expected_xml, actual_xml)

    def test_vlan_global(self):
        vlan = ds.VlanGlobal(42)
        vlan.ports = ds.Pbits([1, 3, 4])
        vlan.name = "vlan_test"

        expected_xml = '<vlan_global id0="42"><vid>42</vid><active>1' + \
                       '</active><name>vlan_test</name>' + \
                       '<pbmp_untagged id0="0"><pbits id0="0">13</pbits>' + \
                       '</pbmp_untagged></vlan_global>'
        actual_xml = vlan.as_xml_text()
        self.assertEquals(expected_xml, actual_xml)

    def test_cfg_data(self):
        cfg = ds.CfgData()

        vlan = ds.VlanGlobal(42, name="vlan_test", ports=ds.Pbits([1, 3, 4]))

        cfg.vlans.append(vlan)

        expected_xml = '<cfg_data><vlan_global id0="42"><vid>42</vid>' + \
                       '<active>1</active><name>vlan_test</name>' + \
                       '<pbmp_untagged id0="0"><pbits id0="0">13</pbits>' + \
                       '</pbmp_untagged></vlan_global></cfg_data>'

        actual_xml = cfg.as_xml_text()

        self.assertEquals(expected_xml, actual_xml)

        del cfg.vlans
        expected_xml = '<cfg_data><vlan_global id0="42"><vid>42</vid>' + \
                       '<active>0</active><name>vlan_test</name>' + \
                       '<pbmp_untagged id0="0"><pbits id0="0">13</pbits>' + \
                       '</pbmp_untagged></vlan_global></cfg_data>'
        actual_xml = cfg.as_xml_text()
        self.assertEquals(expected_xml, actual_xml)