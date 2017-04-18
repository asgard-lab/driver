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

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from neutron_lib.db import model_base


class DatacomNetwork(model_base.BASEV2, model_base.HasId):
    """Each VLAN represent a Network
    a network may have multiple ports
    """
    __tablename__ = "datacomnetwork"

    vlan = Column(Integer)
    name = Column(String(30))


class DatacomPort(model_base.BASEV2, model_base.HasId):
    """Each port is connected to a network
    """
    __tablename__ = "datacomport"
    """TODO: create a table interface wich holds interface and ip and only
       create relation between port and this interface
    """
    switch = Column(String(36))
    neutron_port_id = Column(String(36))
    interface = Column(Integer)

    network_id = Column(String(36), ForeignKey('datacomnetwork.id'))
    network = relationship('DatacomNetwork', backref=backref('ports'))