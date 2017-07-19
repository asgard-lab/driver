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


# It is still used the constant bag type, but it will transit to the class bagef class vlan:
class Vlan:
    MIN_INDEX = 2
    MAX_INDEX = 4000


class Ports:
    MAX_PORTS = 2**30 - 1
    MIN_PORTS = 0


class ExceptionTemplate(Exception):
    def __call__(self, *args):
        return self.__class__(*(self.args + args))


class XMLVlanError(ExceptionTemplate):
    pass


class XMLPortError(ExceptionTemplate):
    pass


class RPCError(ExceptionTemplate):
    pass


class DMConfigError(ExceptionTemplate):
    pass

class DMPortError(ExceptionTemplate):
    pass
