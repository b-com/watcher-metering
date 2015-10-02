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

import json

from oslo_log import log
import requests
from watcher_metering.load.loadable import ExternalOptConfig
from watcher_metering.store.base import MetricsStoreClientBase
from watcher_metering.store.base import MetricsStoreError
from watcher_metering.store.utils.keystone import KeystoneClient
from watcher_metering.store.utils.keystone import KeystoneError

LOG = log.getLogger(__name__)


class CeilometerClient(MetricsStoreClientBase):
    """Ceilometer client"""

    def __init__(self, auth_uri, admin_user,
                 admin_password, admin_tenant_name):
        super(CeilometerClient, self).__init__()
        self._store_endpoint = None
        self.auth_uri = auth_uri
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.admin_tenant_name = admin_tenant_name

        self.keystone_client = KeystoneClient(
            self.auth_uri, self.admin_user,
            self.admin_password, self.admin_tenant_name
        )
        self._ceilometer_uri = None

    @classmethod
    def get_name(cls):
        return "ceilometer"

    @classmethod
    def get_config_opts(cls):
        return []  # No need for store_endpoint in cfg

    @classmethod
    def get_external_opts_configs(cls):
        """This store client requires some Keystone configuration options
        :return: The list of options relative to this store client
        :rtype: list of :class:`ExternalOptConfig` instances
        """
        return [
            ExternalOptConfig(
                name="auth_uri",
                module_str="keystoneclient.middleware.auth_token",
                group="keystone_authtoken"),
            ExternalOptConfig(
                name="admin_user",
                module_str="keystoneclient.middleware.auth_token",
                group="keystone_authtoken"),
            ExternalOptConfig(
                name="admin_password",
                module_str="keystoneclient.middleware.auth_token",
                group="keystone_authtoken"),
            ExternalOptConfig(
                name="admin_tenant_name",
                module_str="keystoneclient.middleware.auth_token",
                group="keystone_authtoken"),
        ]

    @property
    def store_endpoint(self):
        """Dynamically retrieved from Keystone
        :return: The Ceilometer endpoint
        :rtype: str
        """
        # Kind of cache for logging purposes (avoids repeated calls)
        self._store_endpoint = self.keystone_client.ceilometer_uri
        return self._store_endpoint

    def connect(self):
        LOG.info("No need to connect: Stateless via HTTP.")

    def disconnect(self):
        LOG.info("No need to disconnect: Stateless via HTTP.")

    def _send(self, metric):
        is_successful = self.request_http_post(metric)
        if not is_successful:
            LOG.error(
                "[Ceilometer] Could not deliver the message to the server."
            )
            raise MetricsStoreError("Could not deliver the message "
                                    "to the Ceilometer server.")

    def send(self, metric):
        LOG.debug('Publishing metrics to `%s`', self._store_endpoint)
        try:
            self._send(metric)
        except MetricsStoreError as exc:
            LOG.warn('Unable to send metric `%r`', metric)
            LOG.exception(exc)

    def encode_data(self, metric):
        try:
            return json.dumps([
                {
                    "name": metric["name"],
                    "unit": metric["unit"],
                    "type": metric["type"],
                    "volume": metric["value"],
                    "host": metric["host"],
                    "user_id": metric.get("user_id", ""),
                    "project_id": metric.get("project_id", ""),
                    "resource_id": metric.get("resource_id", ""),
                    "resource_metadata": metric["resource_metadata"],
                    "timestamp": metric["timestamp"]
                }
            ])
        except KeystoneError as exc:
            LOG.exception(exc)

    def request_http_post(self, metric):
        try:
            token = self.keystone_client.token
            if not token:
                LOG.warning("token is empty!")
                raise MetricsStoreError("Keystone token is empty!")
        except KeyError as exc:
            LOG.exception(exc)
            raise MetricsStoreError("Could not get a token from Keystone!")

        data = self.encode_data(metric)
        headers = {
            "X-Auth-Token": token,
            "content-type": "application/json",
            "User-Agent": "metering-agent"
        }

        response = requests.post(
            "%s/%s" % (self.store_endpoint, metric["name"]),
            data=data,
            headers=headers,
            timeout=10
        )

        return response.status_code == requests.codes.ok
