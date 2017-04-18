import neutron.plugins.ml2.drivers.datacom.dcclient.dcclient as dc
from oslo_config import cfg

def base_manager(mockedparser):
        config_dict = {'192.160.0.1':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http'],
                             'compute1':'1/2'
                            },
                       '192.160.0.2':
                            {'dm_username':['admin'],
                             'dm_password':['admin'],
                             'dm_method':['http'],
                             'compute1':'1/1'
                            }
                      }

        mockedparser.return_value.read.return_value = cfg.CONF.config_file
        mockedparser.return_value.parsed = [config_dict]
        return dc.Manager()