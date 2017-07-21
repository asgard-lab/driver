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

""" Methods to create and manipulate the XML
"""
import data_structures
import neutron.plugins.ml2.drivers.datacom.utils as utils

class ManagedXml:
    def __init__(self):
        self.xml = data_structures.CfgData()

    def find_vlan(self, vid):
        """ Find the vlan with the specified vid
        """

        reduced_list = [i for i in self.xml.vlans if i.vid == vid]
        if reduced_list:
            return reduced_list[0]
        else:
            return None

    def add_vlan(self, vid, name='', ports=[]):
        """ This method adds a vlan to the XML an returns it's instance.
        """
        if self.find_vlan(vid):
            raise utils.XMLVlanError("Vlan already exists "+str(vid))
        vlan = data_structures.VlanGlobal(vid)
        if name:
            name = str(name)
            vlan.name = name
        if ports:
            vlan.ports = data_structures.Pbits(ports)

        self.xml.vlans.append(vlan)

        return vlan

    def remove_vlan(self, vid):
        """ This method revmoes a vlan on the XML if it exists.
        """

        if not self.find_vlan(vid):
            raise utils.XMLVlanError("Vlan does not exsits or the vid " + \
                    str(vid) + " is invalid")

        vlan = self.find_vlan(vid)
        del vlan.active

    def add_ports_to_vlan(self, vid, ports):
        """ This method adds ports to an existing vlan
        """

        vlan = self.find_vlan(vid)
        if vlan:
            vlan.ports.add_bits(ports)
        else:
            raise utils.XMLPortError("No such vlan "+str(vid))

    def remove_ports_from_vlan(self, vid, ports):
        """ This method removoes ports from an existing vlan
        """

        vlan = self.find_vlan(vid)
        if vlan:
            vlan.ports.remove_bits(ports)
        else:
            raise utils.XMLVlanError("No such vlan "+str(vid))

    def as_xml(self):
        """ This method returns the xml version of the object
        """
        return self.tostring()

    def tostring(self):
        """ An alias to as_xml()
        """
        return self.xml.as_xml_text()
