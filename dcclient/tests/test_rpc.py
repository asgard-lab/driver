import testtools
import mock
import neutron.plugins.ml2.drivers.datacom.dcclient.rpc as rpc
import neutron.plugins.ml2.drivers.datacom.dcclient.xml_manager.\
                                            data_structures as ds
from StringIO import StringIO as sio
import gzip

# mock requests lib so it does not actually try to send the packet
import requests
requests.post = mock.Mock()


class main_test(testtools.TestCase):

    def test_send_xml(self):

        test_url = '1.1.1.1'
        test_auth = ('user', 'pass')
        test_method = ('https')

        test_rpc = rpc.RPC(test_auth[0], test_auth[1], test_url, test_method)

        rpc.get = mock.Mock()
        cfg = ds.CfgData()

        vlan = ds.VlanGlobal(42, name="vlan_test", ports=ds.Pbits([1, 3, 4]))

        cfg.vlans.append(vlan)

        test_rpc.send_xml(cfg.as_xml_text())

        # mock_calls returns the calls executed to this method, the 0 means we
        # are getting the first (and only) call, and the 2 means we are getting
        # the keyword parameters.
        parameters = requests.post.mock_calls[0][2]

        # retrieve url
        received_url = parameters['url']

        expected_url = 'https://1.1.1.1/System/File/file_config.html'

        self.assertEquals(expected_url, received_url)

        # retrieve data from the parameters.
        data = parameters['data']

        expected_xml = '<cfg_data><vlan_global id0="42"><vid>42</vid>' + \
                       '<active>1</active><name>vlan_test</name>' + \
                       '<pbmp_untagged id0="0"><pbits id0="0">13</pbits>' + \
                       '</pbmp_untagged></vlan_global></cfg_data>'

        # Since the XML has to be the last parameter to be passed, we have to
        # get the last field.
        zippedXML = data.fields[-1][-1][-2]

        # decompress to do the comparison.
        # get the file with the zipped xml as content
        zipFileObject = sio(zippedXML)

        # get the actual file (from which we read)
        with gzip.GzipFile(fileobj=zipFileObject, mode='r') as zipFile:
            received_xml = zipFile.read()

        zipFileObject.close()

        self.assertEquals(expected_xml, received_xml)
