import testtools
import mock
from neutron.plugins.ml2.drivers.datacom.dcclient.xml_manager.\
                                            manager import ManagedXml
import neutron.plugins.ml2.drivers.datacom.dcclient.dcclient as dc
import neutron.plugins.ml2.drivers.datacom.dcclient.rpc as rpc
from oslo_config import cfg
import neutron.plugins.ml2.drivers.datacom.utils as utils

import requests
requests.post = mock.Mock()

#used to test one of the setup errors
cfg.CONF.config_file = '2'
cfg.CONF.ml2_datacom = {}

# function used to extract the fields from switches dictionary
def fields_from(rpc_obj):
    return [rpc_obj.host, rpc_obj.auth, rpc_obj.method]

def new_switch(ip):
        new_dict = {}
        new_dict['dm_username'] = 'admin'
        new_dict['dm_password'] = 'admin'
        new_dict['dm_method'] = 'http'

        new_dict['rpc'] = rpc.RPC('admin',
                                  'admin',
                                  ip,
                                  'http')

        new_dict['xml'] = ManagedXml().as_xml()

        # we are not able to compare two dictionaries, it will allways be
        # different because of the instances, so we use this function to
        # transform this dictionary into a tuple
        new_dict['rpc'] = fields_from(new_dict['rpc'])
        return new_dict

def base_manager(mockedparser):
        config_dict = {'192.160.0.1':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http']
                            },
                       '192.160.0.2':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http']
                            }
                      }

        mockedparser.return_value.read.return_value = cfg.CONF.config_file
        mockedparser.return_value.parsed = [config_dict]
        return dc.Manager()


class main_test(testtools.TestCase):
    # mocking the read method
    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_setup(self, mockedparser):
        # setting up what the mocked method should return
        mockedparser.return_value.read.return_value = ''
        cfg.CONF.config_file = '2'
        test_manager = dc.Manager()

        # tests if the right error is raised, when the parser return
        # something different from the config file
        self.assertRaises(utils.DMConfigError, test_manager.setup)

        mockedparser.return_value.read.return_value = cfg.CONF.config_file

        # test case with no switches being passed
        config_dict = {}
        mockedparser.return_value.parsed = [config_dict]

        test_manager.setup()
        self.assertEquals({}, test_manager.switches_dic,
                          'expected empty dictionary')

        # test case with one switch being passed
        test_manager = dc.Manager()

        # setup the dictionary with the expected values
        # setup the dictionary that will mock our configuration file
        config_dict = {'192.160.0.1':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http']
                            }
                      }

        # setup the dictionary that should be received as expected values
        # from switches dict.
        # this dictionary should have the switch ip followed by its credentials
        # then it should have the rpc definitions
        # and last it should have the xml file
        expected_dict = {'192.160.0.1':new_switch('192.160.0.1')}

        # the following works just like the case with no switch
        cfg.CONF.ml2_datacom = {}
        mockedparser.return_value.parsed = [config_dict]
        test_manager.setup()

        # just like the expected dict, switches dict also must me transformed
        # into a tuple
        received_dict_fields = test_manager.switches_dic['192.160.0.1']
        received_dict_fields['rpc'] = fields_from(received_dict_fields['rpc'])
        received_dict_fields['xml'] = received_dict_fields['xml'].as_xml()

        # finally makes the assertion
        self.assertEquals(expected_dict, test_manager.switches_dic,
                          'did not get expected dictionary with one switch')

        test_manager = dc.Manager()

        # setup the dictionary with the expected values
        # the following will be similar to the case with just one switch
        # except that here we will be setting up 2 switches in the mocked
        # file and in the expected tuple.
        config_dict = {'192.160.0.1':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http']
                            },
                       '192.160.0.2':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http']
                            }
                      }

        expected_dict = {'192.160.0.1':new_switch('192.160.0.1'),
                         '192.160.0.2':new_switch('192.160.0.2')}

        mockedparser.return_value.parsed = [config_dict]

        test_manager.setup()

        received_dict_fields = test_manager.switches_dic['192.160.0.1']

        received_dict_fields['rpc'] = fields_from(received_dict_fields['rpc'])
        received_dict_fields['xml'] = received_dict_fields['xml'].as_xml()

        received_dict_fields = test_manager.switches_dic['192.160.0.2']

        received_dict_fields['rpc'] = fields_from(received_dict_fields['rpc'])
        received_dict_fields['xml'] = received_dict_fields['xml'].as_xml()

        self.assertEquals(expected_dict, test_manager.switches_dic,
                          'did not get expected dictionary with two switches')

        test_manager = dc.Manager()

        # test using global values from the configuration file
        cfg.CONF.ml2_datacom = {'dm_method':'https'}

        config_dict = {'192.160.0.1':
                            {'dm_username':['admin'],
                             'dm_password':['admin']
                            }
                      }
        mockedparser.return_value.parsed = [config_dict]
        test_manager.setup()

        expected_dict = {'192.160.0.1': new_switch('192.160.0.1')}

        expected_dict['192.160.0.1']['dm_method'] = 'https'
        expected_dict['192.160.0.1']['rpc'][2] = 'https'


        received_dict_fields = test_manager.switches_dic['192.160.0.1']

        received_dict_fields['rpc'] = fields_from(received_dict_fields['rpc'])
        received_dict_fields['xml'] = received_dict_fields['xml'].as_xml()

        self.assertEquals(expected_dict, test_manager.switches_dic,
                          'expected use of global values')

    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_update(self, mockedparser):
        requests.post = mock.Mock()

        test_manager = base_manager(mockedparser)

        test_manager.setup()

        test_manager._update()
        self.assertEquals(requests.post.call_count, 2,
                          'update method should have been called twice')

    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_create_network(self, mockedparser):
        ManagedXml.add_vlan = mock.Mock()

        test_manager = base_manager(mockedparser)

        test_manager.setup()

        test_manager.create_network(14, name = 'test_vlan')
        self.assertEquals(ManagedXml.add_vlan.call_count, 2,
                          'expected create network to be called twice')
        ManagedXml.add_vlan.assert_called_with(14, name='test_vlan')

    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_delete_network(self, mockedparser):
        ManagedXml.remove_vlan = mock.Mock()

        test_manager = base_manager(mockedparser)

        test_manager.setup()

        test_manager.delete_network(14)
        self.assertEquals(ManagedXml.remove_vlan.call_count, 2,
                          'expected delete network to be called twice')
        ManagedXml.remove_vlan.assert_called_with(14)

    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_update_port(self, mockedparser):
        ManagedXml.add_ports_to_vlan = mock.Mock()

        test_manager = base_manager(mockedparser)

        test_manager.setup()

        ports = {'192.160.0.1':[1,2],'192.160.0.2':[1,2]}

        test_manager.update_port(14, ports)
        self.assertEquals(ManagedXml.add_ports_to_vlan.call_count, 2,
                          'expected update port to be called twice')
        ManagedXml.add_ports_to_vlan.assert_called_with(14, [1,2])

    @mock.patch('%s.MultiConfigParser' % cfg.__name__)
    def test_delete_port(self, mockedparser):
        ManagedXml.remove_ports_from_vlan = mock.Mock()

        test_manager = base_manager(mockedparser)

        test_manager.setup()

        ports = {'192.160.0.1':[1,2],'192.160.0.2':[1,2]}

        test_manager.delete_port(14, ports)
        self.assertEquals(ManagedXml.remove_ports_from_vlan.call_count, 2,
                          'expected update port to be called twice')
        ManagedXml.remove_ports_from_vlan.assert_called_with(14, [1,2])
