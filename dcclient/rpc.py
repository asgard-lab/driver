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

""" RPC class used to communicate with the hardware
"""
import gzip
from StringIO import StringIO as sio
import os
from requests_toolbelt import MultipartEncoder
import requests


class RPC:
    """ RPC class. Used to connect to the client and pass the XML files.
    """
    def __init__(self, username, password, host, method):
        self.auth = (username, password)
        self.host = host
        self.method = method

    def _create_url(self):
        """ Internal method that returns the switches' URLs given the cfg
        attributes.
        """
        return self.method + '://' + self.host + '/System/File/file_config.html'

    def send_xml(self, xml_content):
        """ Method used to send a given xml file to the switches
        """

        # set url being used
        url = self._create_url()

        ziped = sio()
        with gzip.GzipFile(fileobj=ziped, mode='w') as gzip_file:
            gzip_file.write(xml_content)

        run_data = ziped.getvalue()
        ziped.close()

        fields = (('page', 'file_upload'),
                  ('running_part', '1'),
                  ('file_to_upload', ('file_to_upload',
                                      run_data,
                                      'application/octet-stream')))
        m = MultipartEncoder(fields=fields, boundary='-----boundary-----')
        r = requests.post(url=url,
                          data=m,
                          auth=self.auth,
                          headers={'Content-type': m.content_type},
                          verify=False)

        print r.text
