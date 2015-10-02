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

from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import json

from mock import MagicMock
from mock import patch
from mock import PropertyMock
from oslo_config import cfg
from oslotest.base import BaseTestCase
import requests
from watcher_metering.store.ceilometer import CeilometerClient
from watcher_metering.store.utils.keystone import KeystoneClient
from watcher_metering.tests.publisher.publisher_fixtures import ConfFixture


class TestCeilometerClient(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestCeilometerClient, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.useFixture(ConfFixture(self.conf))

        self.patches.extend([
            patch.object(
                KeystoneClient,
                "token",
                new=PropertyMock(return_value="fake-token")
            ),
            patch.object(
                KeystoneClient,
                "ceilometer_uri",
                new=PropertyMock(return_value="http://fake-ceilometer-ep:7777")
            ),
        ])

        self.client = CeilometerClient(
            auth_uri="http://fake-keystone-ep:1337",
            admin_user="fake_admin",
            admin_password="fake_pwd",
            admin_tenant_name="fake_tenant",
        )

        for _patch in self.patches:
            _patch.start()

    def tearDown(self):
        super(TestCeilometerClient, self).tearDown()

        for _patch in self.patches:
            _patch.stop()

    def test_ceilometer_connect_disconnect(self):
        self.client.connect()
        self.client.disconnect()
        assert self.client.keystone_client.auth_uri
        assert self.client.keystone_client.username
        assert self.client.keystone_client.password
        assert self.client.keystone_client.tenant_name

    @patch.object(json, "dumps", new=MagicMock(side_effect=lambda x: x))
    @patch.object(requests, "post", autopec=True)
    def test_ceilometer_send_valid_metric(self, m_post):
        m_post.return_value = MagicMock(status_code=200)

        fake_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type", "gauge"),
            ("value", 97.9),
            ("resource_id", "res_id-fake"),
            ("host", "test_node"),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("title", "compute.node.cpu.percent")]))
        ])

        expected_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type", "gauge"),
            ("volume", 97.9),
            ("host", "test_node"),
            ("user_id", ""),
            ("project_id", ""),
            ("resource_id", "res_id-fake"),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("title", "compute.node.cpu.percent"),
            ])),
        ])

        self.client.send(fake_metric)

        # Should check that the data send over via the Ceilometer client are OK
        m_post.assert_called_once_with(
            "http://fake-ceilometer-ep:7777/compute.node.cpu.percent",
            headers={"X-Auth-Token": "fake-token",
                     "User-Agent": "metering-agent",
                     "content-type": "application/json"},
            data=[expected_metric],
            timeout=10,
        )

    @patch.object(requests, "post", autopec=True)
    def test_ceilometer_send_invalid_metric(self, m_post):
        m_post.return_value = MagicMock(status_code=404)

        fake_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type", "gauge"),
            ("value", "97.9"),  # A string instead of a numerical value
            ("resource_id", ""),
            ("host", "test_node"),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("title", "compute.node.cpu.percent")]))
        ])

        self.client.send(fake_metric)
        # No assertion (done on purpose)
        # This means that something went wrong but the program didn't crash,
        # though it could not send the metrics to Ceilometer
