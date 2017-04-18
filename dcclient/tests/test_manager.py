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
import neutron.plugins.ml2.drivers.datacom.dcclient.xml_manager.manager as mg
import neutron.plugins.ml2.drivers.datacom.dcclient.xml_manager.data_structures as ds


class MainTest(testtools.TestCase):
    def test_find_vlan(self):
        # tests if none type is return when vlan is not found
        xml = mg.ManagedXml()

        answer = xml.find_vlan(61)
        self.assertIs(answer, None)

        # tests if Vlan_global object is return when vlan is found
        xml.add_vlan(60, name='vlan_test', ports=[1, 5, 9])

        answer = xml.find_vlan(60)
        self.assertIsInstance(answer, ds.VlanGlobal)

        # tests if found vlan xml is correct
        expected_xml = '<vlan_global id0="60"><vid>60</vid><active>1' + \
                       '</active><name>vlan_test</name>' + \
                       '<pbmp_untagged id0="0"><pbits id0="0">273</pbits>' + \
                       '</pbmp_untagged></vlan_global>'

        self.assertEquals(expected_xml, answer.as_xml_text())