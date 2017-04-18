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

""" Main class from dcclient. Manages XML interaction, as well as switch and
creates the actual networks
"""

import rpc
from xml_manager.manager import ManagedXml
import neutron.plugins.ml2.drivers.datacom.utils as utils

from oslo_log import log as logger
from oslo_config import cfg

LOG = logger.getLogger(__name__)


class Manager:
    def __init__(self):
        self.switches_dic = {}

    def setup(self):
        # Setup specific configurations
        oslo_parser = cfg.MultiConfigParser()
        parsed_buf = oslo_parser.read(cfg.CONF.config_file)

        if not len(parsed_buf) == len(cfg.CONF.config_file):
            raise utils.DMConfigError("Parsing problem")

        config = oslo_parser.parsed[0]

        # get each switch from config file
        switches = [i for i in config if str(i) != 'ml2_datacom']

        # create the actual dictionary
        for switch in switches:
            sw_dic = config[switch]
            # each field is a list, when it should be a value
            for i in sw_dic:
                if i.startswith('dm'):
                    sw_dic[i] = sw_dic[i][0]

            # get each global configuration, when not mentioned in the specific
            for field in cfg.CONF.ml2_datacom:
                if field not in sw_dic:
                    sw_dic[field] = cfg.CONF.ml2_datacom[field]

            sw_dic['rpc'] = rpc.RPC(str(sw_dic['dm_username']),
                                    str(sw_dic['dm_password']),
                                    str(switch),
                                    str(sw_dic['dm_method']))

            sw_dic['xml'] = ManagedXml()
            self.switches_dic[switch] = sw_dic

    def _update(self):
        for switch in self.switches_dic:
            xml = self.switches_dic[switch]['xml']
            self.switches_dic[switch]['rpc'].send_xml(xml.tostring())

    def create_network(self, vlan, name=''):
        """ Creates a new network on the switch, if it does not exist already.
        """
        self._create_network_xml(vlan, name)
        self._update()

    def _create_network_xml(self, vlan, name=''):
        """ Configures the xml for a new network.
        """
        try:
            for switch in self.switches_dic:
                xml = self.switches_dic[switch]['xml']
                xml.add_vlan(vlan, name=name)
        except:
            LOG.info("Trying to create already existing network %d:", vlan)

    def create_network_bulk(self, networks, interfaces={}):
        """ Creates multiple networks on the switch, also creating the ports
            associated.
        """
        for vlan, name in networks:
            self._create_network_xml(vlan, name)
            if vlan in interfaces:
                self._update_port_xml(vlan, interfaces[vlan])
        self._update()

    def delete_network(self, vlan):
        """ Delete a network on the switch, if it exsists
            Actually just sets it to inactive
        """
        try:
            for switch in self.switches_dic:
                xml = self.switches_dic[switch]['xml']
                xml.remove_vlan(vlan)
            self._update()
        except:
            LOG.info("Trying to delete inexisting vlan: %d", vlan)

    def update_port(self, vlan, ports):
        """ Add new ports to vlan on the switch, if vlan exists
        and port is not already there.
        """
        self._update_port_xml(vlan, ports)
        self._update()
        # needs other exception

    def _update_port_xml(self, vlan, ports):
        """ Configures the xml to the port-updating process
        """
        try:
            for switch in ports:
                xml = self.switches_dic[switch]['xml']
                xml.add_ports_to_vlan(vlan, ports[switch])
        except:
            LOG.info("Trying to add ports to nonexistant network %d:", vlan)

    def delete_port(self, vlan, ports):
        """ Delete not used ports from switch
        """
        try:
            for switch in ports:
                xml = self.switches_dic[switch]['xml']
                xml.remove_ports_from_vlan(vlan, ports[switch])
            self._update()
        except:
            LOG.info("Trying to remove ports from nonexistant network %d:", vlan)
        # needs other exception