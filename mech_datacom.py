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
from oslo_config import cfg

from neutron.plugins.ml2 import driver_api as api
import neutron.db.api as db

from dcclient.dcclient import Manager
from dcclient.xml_manager.data_structures import Pbits
from db.models import DatacomNetwork, DatacomPort

from sqlalchemy import func
from sqlalchemy import exists

import config

config.setup_config()

class DatacomDriver(api.MechanismDriver):
    """    """

    def __init__(self):
        self.dcclient = Manager()

    def initialize(self):
        self.dcclient.setup()
        session = db.get_session()
        
        self.query_bd(session)

        self.dcclient.create_network_bulk(self.networks, interfaces=self.interfaces)

    def query_bd(self, session):
        self.networks = session.query(DatacomNetwork.vlan,
                                 DatacomNetwork.name).all()
        self.ports = session.query(DatacomPort.switch,
                              DatacomPort.interface,
                              DatacomNetwork.vlan).filter(DatacomPort.network_id == DatacomNetwork.id).all()
        porta = session.query(DatacomPort.switch, DatacomPort.interface, DatacomNetwork.vlan).filter(DatacomPort.network_id == DatacomNetwork.id).all()
        self.interfaces = {}

        # first set up the dictionary with each port list
        for port in self.ports:
            if port[2] not in self.interfaces:
                self.interfaces[port[2]] = []
            self.interfaces[port[2]].append(port[:2])

        # now transform each port list into a dictionary, so the dcclient
        # can understand it.
        for vlan in self.interfaces:
            self.interfaces[vlan] = self._ports_to_dict(self.interfaces[vlan])            

    def _find_ports(self, compute):
        """Returns dictionary with the switches containing the compute,
        and each respective port.
        """
        ports = {}
        switches_dic = self.dcclient.switches_dic
        for switch in switches_dic:
            if compute in switches_dic[switch]:
                if switch not in ports:
                    ports[switch] = [switches_dic[switch][compute]]
                else:
                    ports[switch].append(switches_dic[switch][compute])

        for switch in switches_dic:
            for key in switches_dic[switch]:
                if switch in ports:
                    if key.startswith('trunkPort'):
                        ports[switch].append(switches_dic[switch][key])
        return ports

    def _add_ports_to_db(self, ports, context):
        session = db.get_session()
        with session.begin(subtransactions=True):
            vlan = context.network.network_segments[0]['segmentation_id']
            query = session.query(DatacomNetwork)
            resultset = query.filter(DatacomNetwork.vlan == vlan)
            dcnetwork = resultset.first()
            ret = session.query(exists().where(DatacomPort.neutron_port_id==context.current['id'])).scalar()
            if ret == 0:
                for ip in ports:
                    for port in ports[ip]:
                        dcport = DatacomPort(network_id=dcnetwork.id, switch=ip, interface=int(port[0].split("/")[1]),
                                         neutron_port_id=context.current['id'])
                        session.add(dcport)
                        session.flush()

    def create_network_precommit(self, context):
        """Within transaction."""
        session = db.get_session()
        self.query_bd(session)
        with session.begin(subtransactions=True):
            dm_network = DatacomNetwork(
                vlan=int(context.network_segments[0]['segmentation_id']),
                name=context.current['name'])
            session.add(dm_network)

    def create_network_postcommit(self, context):
        """After transaction is done."""
        vlan = int(context.network_segments[0]['segmentation_id'])
        self.dcclient.fill_dic(self.networks, interfaces=self.interfaces)
        self.dcclient.create_network(vlan, name=str(context.current['name']))

    def update_network_precommit(self, context):
        """Within transaction."""
        pass

    def update_network_postcommit(self, context):
        """After transaction is done."""
        pass

    def delete_network_precommit(self, context):
        """Within transaction."""
        session = db.get_session()
        vlan = int(context.network_segments[0]['segmentation_id'])
        with session.begin(subtransactions=True):
            query = session.query(DatacomNetwork)
            self.query_bd(session)
            resultset = query.filter(DatacomNetwork.vlan == vlan)
            dcnetwork = resultset.first()
            session.delete(dcnetwork)

    def delete_network_postcommit(self, context):
        """After transaction is done."""
        vlan = int(context.network_segments[0]['segmentation_id'])
        self.dcclient.fill_dic(self.networks, interfaces=self.interfaces)
        self.dcclient.delete_network(vlan)

    def create_port_precommit(self, context):
        """Within transaction."""
        pass

    def create_port_postcommit(self, context):
        """After transaction is done."""
        pass

    def update_port_precommit(self, context):
        """Within transaction."""

        if context.top_bound_segment is not None and str(context.top_bound_segment['network_type']) == "vlan" and \
                context.current['device_owner'].startswith('compute') and str(context.current['status']) == "ACTIVE":
            session = db.get_session()    
            self.query_bd(session)
            self.dcclient.fill_dic(self.networks, interfaces=self.interfaces)    
            ports = self._find_ports(context.host)
            if ports:
                self._add_ports_to_db(ports, context)

    def _ports_to_dict(self, port_list):
        """ takes a list of ports and returns a dictionary containing the
        dictionary in a way dcclient understands.
        """
        update_interfaces = {}

        for switch, interface in port_list:
            switch = str(switch)
            interface = int(interface)
            if switch not in update_interfaces:
                update_interfaces[switch] = []
            update_interfaces[switch].append(interface)

        return update_interfaces

    def update_port_postcommit(self, context):
        """After transaction."""
        if context.top_bound_segment is not None and str(context.top_bound_segment['network_type']) == "vlan" and \
                context.current['device_owner'].startswith('compute') and str(context.current['status']) == "ACTIVE": 
            session = db.get_session()
            vlan = int(context.network.network_segments[0]['segmentation_id'])
            query = session.query(DatacomPort.switch, DatacomPort.interface)
            r_set = query.filter_by(neutron_port_id=context.current['id']).all()

            interfaces = self._ports_to_dict(r_set)

            self.dcclient.update_port(vlan, interfaces)

    def delete_port_precommit(self, context):
        """Within transaction."""
        if context.top_bound_segment is not None and str(context.top_bound_segment['network_type']) == "vlan" and \
                context.current['device_owner'].startswith('compute'):
            ports = self._find_ports(context.host)
            if ports:
                session = db.get_session()
                with session.begin(subtransactions=True):
                    for ip in ports:
                        for port in ports[ip]:
                            query = session.query(DatacomPort)
                            resultset = query.filter_by(switch=ip, interface=int(port[0].split("/")[1]),
                                                        neutron_port_id=context.current['id'])
                            dcport = resultset.first()
                            session.delete(dcport)

    def delete_port_postcommit(self, context):
        """After transaction."""

        if context.top_bound_segment is not None and str(context.top_bound_segment['network_type']) == "vlan" and \
                context.current['device_owner'].startswith('compute'):
            ports = self._find_ports(context.host)
            delete_interfaces = {}
            if ports:
                session = db.get_session()
                self.query_bd(session)
                self.dcclient.fill_dic(self.networks, interfaces=self.interfaces)    
                for ip in ports:
                    for port in ports[ip]:
                        query = session.query(DatacomPort)
                        resultset = query.filter_by(switch=ip,
                                                    interface=int(port[0].split("/")[1]),
                                                    neutron_port_id=context.current['id'])
                        dcport = resultset.first()
                        query2 = session.query(DatacomNetwork.id)
                        result = query2.filter_by(vlan=int(context.network.network_segments[0]['segmentation_id']))

                        networkId = result.first()
                        result2 = query.filter_by(switch=ip,
                                                    interface=int(port[0].split("/")[1]),
                                                    network_id=str(networkId[0])).first()                            
                        if not dcport and not result2:
                            vlan = int(context.network.network_segments[0]['segmentation_id'])
                            switch = str(ip)
                            interface = int(port[0].split("/")[1])
                            if switch not in delete_interfaces:
                                delete_interfaces[switch] = []
                            delete_interfaces[switch].append(interface)
                            self.dcclient.delete_port(vlan, delete_interfaces)
