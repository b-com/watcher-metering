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

from mock import patch
from oslo_config import cfg
from oslotest.base import BaseTestCase
from riemann_client.client import Client
from riemann_client.riemann_pb2 import Attribute
from riemann_client import transport
from watcher_metering.store.base import MetricsStoreError
from watcher_metering.store.riemann import RiemannClient
from watcher_metering.tests.publisher.publisher_fixtures import ConfFixture


class TestRiemannClient(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestRiemannClient, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.useFixture(ConfFixture(self.conf))

        self.patches.extend([
            patch.object(transport, "TCPTransport", transport.BlankTransport),
        ])

        for _patch in self.patches:
            _patch.start()

        self.client = RiemannClient(
            store_endpoint="tcp://FAKE:1337",
            datacenter="test_datacenter",
            default_metric_host="test-host",
            default_metric_ttl=7357,
            default_metric_state="ok",
        )

    def tearDown(self):
        super(TestRiemannClient, self).tearDown()

        for _patch in self.patches:
            _patch.stop()

    @patch.object(transport.BlankTransport, "connect")
    def test_riemann_connect(self, m_connect):
        self.client.connect()
        self.assertEqual(m_connect.call_count, 1)

    @patch.object(transport.BlankTransport, "connect")
    def test_riemann_connect_failed(self, m_connect):
        m_connect.side_effect = OSError("Fake fail!")
        self.assertRaises(MetricsStoreError, self.client.connect)

    @patch.object(transport.BlankTransport, "disconnect")
    @patch.object(transport.BlankTransport, "connect")
    def test_riemann_disconnect(self, m_connect, m_disconnect):
        self.client.connect()
        self.client.disconnect()
        self.assertEqual(m_connect.call_count, 1)
        self.assertEqual(m_disconnect.call_count, 1)

    @patch.object(Client, "send_event", autopec=True)
    def test_riemann_send_valid_metric(self, m_send):
        m_send.return_value = True

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

        # Should check that the data send over via the Riemann client are OK
        self.assertEqual(m_send.call_count, 1)

    @patch.object(Client, "send_event", autopec=True)
    def test_riemann_send_invalid_metric(self, m_send):
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

        # This raises an error if the send did not succeed
        self.assertRaises(MetricsStoreError, self.client.send, fake_metric)

    def test_riemann_create_invalid_metric(self):
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

        # This raises an error is not caught properly
        self.assertRaises(
            MetricsStoreError,
            self.client.create_event,
            fake_metric,
        )
        # This means that something went wrong but the program didn't crash,
        # though it could not send the metrics to Riemann

    @patch.object(transport.BlankTransport, "send")
    def test_riemann_create_valid_event(self, m_send):
        m_send.return_value = True

        fake_metric = OrderedDict([
            ("name", "compute.node.cpu.percent"),
            ("timestamp", "2015-08-04T15:15:45.703542"),
            ("unit", "%"),
            ("type", "gauge"),
            ("value", 97.9),
            ("resource_id", ""),
            ("host", "test_node"),
            ("ttl", 1337),
            ("resource_metadata", OrderedDict([
                ("host", "test_node"),
                ("ttl", 1337),
                ("title", "compute.node.cpu.percent")]))
        ])
        expected_attributes = [
            Attribute(key="datacenter", value="test_datacenter"),
            Attribute(key="resource_id", value=""),
            Attribute(key="title", value="compute.node.cpu.percent"),
            Attribute(key="unit", value="%"),
        ]

        event = self.client.create_event(fake_metric)

        self.assertEqual(event.time, 1438701345)
        self.assertEqual(event.state, "ok")
        self.assertEqual(event.service, "compute.node.cpu.percent")
        self.assertEqual(event.host, "test_node")
        self.assertEqual(event.description, "")
        self.assertEqual(event.tags, [])
        self.assertEqual(event.ttl, 1337)
        self.assertEqual(event.metric_sint64, 0)
        self.assertEqual(event.metric_d, 0)
        self.assertEqual(event.metric_f, 97.9)
        self.assertEqual(event.tags, [])
        self.assertEqual(len(event.attributes), 4)

        for actual_attr, expected_attr in zip(
                sorted(event.attributes, key=lambda x: x.key,),
                expected_attributes):
            self.assertEqual(actual_attr.key, expected_attr.key)
            self.assertEqual(actual_attr.value, expected_attr.value)

    @patch.object(transport.BlankTransport, "send")
    def test_riemann_create_event_exclude_ttl(self, m_send):
        m_send.return_value = True

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
                ("ttl", 1234),
                ("title", "compute.node.cpu.percent")]))
        ])
        expected_attributes = [
            Attribute(key="datacenter", value="test_datacenter"),
            Attribute(key="resource_id", value=""),
            Attribute(key="title", value="compute.node.cpu.percent"),
            Attribute(key="unit", value="%"),
        ]

        event = self.client.create_event(fake_metric)

        self.assertEqual(event.time, 1438701345)
        self.assertEqual(event.state, "ok")
        self.assertEqual(event.service, "compute.node.cpu.percent")
        self.assertEqual(event.host, "test_node")
        self.assertEqual(event.description, "")
        self.assertEqual(event.tags, [])
        self.assertEqual(event.ttl, 1234)
        self.assertEqual(event.metric_sint64, 0)
        self.assertEqual(event.metric_d, 0)
        self.assertEqual(event.metric_f, 97.9)
        self.assertEqual(event.tags, [])
        self.assertEqual(len(event.attributes), 4)

        for actual_attr, expected_attr in zip(
                sorted(event.attributes, key=lambda x: x.key,),
                expected_attributes):
            self.assertEqual(actual_attr.key, expected_attr.key)
            self.assertEqual(actual_attr.value, expected_attr.value)

    @patch.object(Client, "send_event", autopec=True)
    def test_riemann_send_failed_transport(self, m_send):
        m_send.side_effect = [transport.RiemannError, True]

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

        # This test simply ensures that even though the metric couldn't be
        # delivered, it didn't make the program crash (1 retry)
        self.assertEqual(m_send.call_count, 2)
