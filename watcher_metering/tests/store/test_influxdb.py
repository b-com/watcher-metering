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
from influxdb import InfluxDBClient

from mock import patch
from oslo_config import cfg
from oslotest.base import BaseTestCase
from watcher_metering.store.base import MetricsStoreError
from watcher_metering.store.influxdb import InfluxClient
from watcher_metering.tests.publisher.publisher_fixtures import ConfFixture


class TestInfluxDBClient(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestInfluxDBClient, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.useFixture(ConfFixture(self.conf))

        self.patches.extend([])

        for _patch in self.patches:
            _patch.start()

        self.client = InfluxClient(
            default_host="192.168.1.40",
            default_port=8087,
            default_database="my_db",
            default_username="user",
            default_password="password",
            create_database=False
        )

    def tearDown(self):
        super(TestInfluxDBClient, self).tearDown()

        for _patch in self.patches:
            _patch.stop()

    def test_influxdb_connect_disconnect(self):
        self.client.connect()
        self.client.disconnect()
        assert self.client.store_endpoint

    @patch("influxdb.InfluxDBClient.query", autopec=True)
    def test_influxdb_create_database(self, m_query):

        default_database = 'my_db'
        self.client = InfluxClient(
            default_host="192.168.1.40",
            default_port=8087,
            default_database=default_database,
            default_username="user",
            default_password="password",
            create_database=True
        )

        self.client.connect()
        assert self.client.store_endpoint
        m_query.assert_called_with('CREATE DATABASE %s' % default_database)

    @patch.object(InfluxDBClient, "write_points", autopec=True)
    def test_influxdb_send_metric(self, m_write_points):
        m_write_points.return_value = True

        fake_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type", "gauge"),
            ("value", 97.9),
            ("resource_id", ""),
            ("host", "test_node"),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("title", "compute.node.cpu.percent")]))
        ])

        self.client.send(fake_metric)
        self.assertEqual(m_write_points.call_count, 1)

    @patch.object(InfluxDBClient, "write_points", autopec=True)
    def test_influxdb_send_invalid_metric(self, m_write_points):
        m_write_points.return_value = True

        fake_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type_", "gauge"),  # wrong name
            ("value", 97.9),
            ("resource_id", ""),
            ("host", "test_node"),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("title", "compute.node.cpu.percent")]))
        ])

        # This raises an error if the send did not succeed
        self.assertRaises(MetricsStoreError, self.client.send, fake_metric)
