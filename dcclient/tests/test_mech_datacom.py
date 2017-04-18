import testtools
import neutron.plugins.ml2.drivers.datacom.mech_datacom as mech_datacom
import neutron.plugins.ml2.drivers.datacom.dcclient as dcclient
from oslo_config import cfg
import mock
from neutron_lib.db import model_base
from neutron.db import models_v2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import neutron.db.api as db
import etc
from neutron.plugins.ml2.drivers.datacom.db.models import\
                                            DatacomNetwork, DatacomPort

cfg.CONF.config_file = ''
cfg.MultiConfigParser = mock.Mock()

class mocked_context:
    network_segments = [{'segmentation_id':20}]
    current = {'name':'test'}

class mocked_port_context:
    network = mocked_context()
    bound_segment = {'network_type': 'vxlan', 'segmentation_id':20}
    current = {'device_owner': 'compute1', 'id': 'neutron_port_id'}
    host = 'compute1'

def add_network(session, vlan, name=''):
    dm_network = DatacomNetwork(vlan=vlan, name=name)
    session.add(dm_network)
    return dm_network

def _create_port_db(vlan, network, port_list, session):
    for switch, neutron_port_id, interface in port_list:
        session.add(DatacomPort(switch=switch,
                                neutron_port_id=neutron_port_id,
                                interface=interface,
                                network=network))

# db decorator, creates the local engine and starts db
def uses_db(networks=[], ports={}):
    def wrapp_func(func):
        def func_with_db(*args, **kwargs):
            engine = create_engine('sqlite:///:memory:')
            session = sessionmaker()
            session.configure(bind=engine)
            model_base.BASEV2.metadata.create_all(engine)
            ses = session()
            if (networks):
                for vlan, name in networks:
                    network = add_network(ses, vlan, name)
                    if vlan in ports:
                        _create_port_db(vlan, network, ports[vlan], ses)

            ses.commit()
            ses.close()
            old_session = db.get_session
            db.get_session = session
            func(*args, **kwargs)
            db.get_session = old_session
            del engine
        return func_with_db
    return wrapp_func

class main_test(testtools.TestCase):

    @uses_db([(20, 'test1'),
             (24, 'test2')],
             {20:[('0.0.0.0', 'neutron_port_id', 1)]})
    def test_initialize(self):
        manager_class = dcclient.dcclient.Manager
        manager_class._create_network_xml = mock.Mock()
        manager_class._update_port_xml = mock.Mock()
        manager_class._update = mock.Mock()

        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)

        driver.initialize()

        manager_class._update.assert_called_once()
        self.assertEquals(2, manager_class._create_network_xml.call_count)
        manager_class._update_port_xml.assert_called_once()
        first_call = manager_class._create_network_xml.call_args_list[0][0]
        self.assertEquals((20, 'test1'), first_call)
        second_call = manager_class._create_network_xml.call_args_list[1][0]
        self.assertEquals((24, 'test2'), second_call)

    @uses_db()
    def test_create_network_precommit(self):
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.create_network_precommit(mocked_context())
        session = db.get_session()
        query = session.query(DatacomNetwork)
        resultset = query.filter(DatacomNetwork.vlan == 20)
        self.assertEquals(1, resultset.count())

    def test_create_network_postcommit(self):
        context = mocked_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.create_network = mock.Mock()
        driver.create_network_postcommit(context)
        driver.dcclient.create_network.assertCalledOnceWith(20,'test')

    @uses_db([(20, 'test1')])
    def test_delete_network_precommit(self):
        context = mocked_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.setup()
        session = db.get_session()
        driver.delete_network_precommit(context)
        query = session.query(DatacomNetwork)
        self.assertEquals(0, query.count())

    def test_delete_network_postcommit(self):
        context = mocked_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.delete_network = mock.Mock()
        driver.delete_network_postcommit(context)
        driver.dcclient.delete_network.assertCalledOnceWith(20)

    @uses_db([(20, 'test1')])
    def test_update_port_precommit(self):
        context = mocked_port_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.setup()
        session = db.get_session()
        driver.update_port_precommit(context)
        ports = session.query(DatacomPort.interface, DatacomNetwork.vlan).all()
        self.assertIn((1,20), ports)
        self.assertIn((2,20), ports)

    @uses_db([(20, 'test1')],
             {20:[('192.160.0.2', 'neutron_port_id', 1),
                  ('192.160.0.1', 'neutron_port_id', 2)]})
    def test_update_port_postcommit(self):
        context = mocked_port_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.setup()
        driver.dcclient.update_port = mock.Mock()
        driver.update_port_postcommit(context)
        expected_dict = {'192.160.0.1': [1], '192.160.0.2': [2]}
        driver.dcclient.update_port.assertCalledOnceWith(20, expected_dict)

    @uses_db([(20, 'test1')],
             {20:[('192.160.0.2', 'neutron_port_id', 1),
                  ('192.160.0.1', 'neutron_port_id', 2)]})
    def test_delete_port_precommit(self):
        context = mocked_port_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.setup()
        driver.delete_port_precommit(context)
        session = db.get_session()
        query = session.query(DatacomPort)
        self.assertEquals(0, len(query.all()))

    @uses_db()
    def test_delete_port_postcommit(self):
        context = mocked_port_context()
        driver = mech_datacom.DatacomDriver()
        driver.dcclient = etc.base_manager(cfg.MultiConfigParser)
        driver.dcclient.setup()
        driver.delete_port_postcommit(context)
        driver.dcclient.delete_port = mock.Mock()
        expected_dict = {'192.160.0.1': [1], '192.160.0.2': [2]}
        driver.dcclient.delete_port.assertCalledOnceWith(20, expected_dict)
