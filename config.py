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

""" Configuration for the datacom switch.

The options are used to locate datacom switches and identify
openstack. The dm_username and dm_password are the credentials
and the dm_host is the IP for the switch. The region name is the
identifier for the controller.
"""

import oslo_i18n

DOMAIN = "datacom"

_translators = oslo_i18n.TranslatorFactory(domain=DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary

DATACOM_DRIVER_OPTS = [
    cfg.StrOpt('dm_username',
               default='',
               help=_('(required) Username for the dm connection.'
                      'If not set, the identification will fail.')),
    cfg.StrOpt('dm_password',
               default='',
               secret=True,  # do not expose value in the logs
               help=_('(required) Password for the dm connection.'
                      'If not set, the identification will fail.')),
    cfg.StrOpt('dm_host',
               default='',
               help=_('(required) IP to be connected to..'
                      'If not set, the identification will fail.')),
    cfg.IntOpt('dm_port',
               default=443,
               help=_('Port to be connected to, default is 443.')),
    cfg.StrOpt('dm_method',
               default='https',
               help=_('Connection method (default is https)')),
    cfg.StrOpt('region_name',
               default='RegionOne',
               help=_('If multiple OpenStack/Neutron controllers are involved,'
                      'region_name identifies each one. Most of the times the '
                      'value will be "RegionOne", which is the default value '))
]


def setup_config():
    cfg.CONF.register_opts(DATACOM_DRIVER_OPTS, "ml2_datacom")