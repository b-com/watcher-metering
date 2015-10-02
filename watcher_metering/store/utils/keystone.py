# -*- encoding: utf-8 -*-
# Copyright (c) 2015 b<>com
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

from __future__ import unicode_literals

from keystoneclient import exceptions
from keystoneclient.v3 import client
from oslo_log import log

LOG = log.getLogger(__name__)
# note we can also think about use get_raw_token_from_identity_service


class KeystoneClient(object):

    def __init__(self, auth_uri, username, password, tenant_name):
        self.auth_uri = auth_uri
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self._keystone = None

    @property
    def keystone(self):
        if not self._keystone:
            keystone = client.Client(
                auth_url=self.auth_uri,
                username=self.username,
                password=self.password,
                tenant_name=self.tenant_name,
            )
            self._keystone = keystone
        return self._keystone

    @property
    def token(self):
        return self.keystone.auth_token

    @property
    def ceilometer_uri(self):
        try:
            return self.keystone.service_catalog.url_for(
                service_type="metering",
                endpoint_type="internal",  # or public
            )
        except exceptions.ClientException as exc:
            raise KeystoneError(
                "Keystone client encountered an error:\n%r" % exc
            )


class KeystoneError(Exception):
    pass
