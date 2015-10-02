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
import os

from mock import MagicMock
from mock import patch
from mock import PropertyMock
import msgpack
from nanomsg import Socket
from oslo_config import cfg
from oslotest.base import BaseTestCase
from six.moves.queue import Queue
from watcher_metering.publisher.publisher import Publisher
from watcher_metering.publisher.worker import Worker
from watcher_metering.store.loader import StoreClientLoader
from watcher_metering.tests.publisher.publisher_fixtures import ConfFixture


class TestPublisher(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestPublisher, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.useFixture(ConfFixture(self.conf))

        # Patches the publisher socket class
        self.m_publisher_socket_cls = MagicMock(spec=Socket)
        # Patches the publisher socket instance
        self.m_publisher_socket = MagicMock(spec=Socket, name="nn_socket")
        self.m_publisher_socket_cls.return_value = self.m_publisher_socket

        self.patches.extend([
            # Deactivates the nanomsg socket
            patch(
                "watcher_metering.publisher.base.nanomsg.Socket",
                new=self.m_publisher_socket_cls,
            ),
            patch.object(
                StoreClientLoader, "load", new=MagicMock(),
            ),
        ])

        # Applies all of our patches before each test
        for _patch in self.patches:
            _patch.start()

        self.publisher = Publisher(
            use_nanoconfig_service=False,
            publisher_endpoint="fake://fake_endpoint",
            nanoconfig_service_endpoint="",
            nanoconfig_update_endpoint="",
            nanoconfig_profile="nanoconfig://test_profile",
            metrics_store="riemann",
            max_queue_size=5,
            max_worker=5,
            min_worker=1,
        )

    def tearDown(self):
        super(TestPublisher, self).tearDown()
        for _patch in self.patches:
            _patch.stop()

    @patch.object(Worker, "start", MagicMock())
    @patch.object(Queue, "put")
    @patch.object(Publisher, "terminated", new_callable=PropertyMock)
    def test_on_receive(self, m_terminated, m_put):
        # mock the termination condition to finish after 1 iteration
        # Last value to mock out the stop() call
        m_terminated.side_effect = [False, True, True]
        # mock the recv
        m_recv = self.m_publisher_socket.recv
        fake_metric = OrderedDict(
            name="compute.node.cpu.percent",
            timestamp="2015-08-04T15:15:45.703542",
            unit="%",
            type="gauge",
            value=97.9,
            resource_id="test_node",
            host="test_node",
            resource_metadata=OrderedDict(
                host="test_node",
                title="compute.node.cpu.percent",
            )
        )
        m_recv.return_value = msgpack.dumps(fake_metric)
        # start publisher
        self.publisher.run()

        self.assertEqual(self.m_publisher_socket.bind.call_count, 1)
        m_put.assert_called_once_with({
            'value': 97.9,
            'name': 'compute.node.cpu.percent',
            'host': 'test_node',
            'resource_id': 'test_node',
            'timestamp': '2015-08-04T15:15:45.703542',
            'resource_metadata': {
                'title': 'compute.node.cpu.percent',
                'host': 'test_node'
            },
            'unit': '%',
            'type': 'gauge'
        })

    @patch.object(Publisher, "start_worker")
    def test_adjust_pool_size_expand_pool(self, m_start_worker):
        self.publisher.max_queue_size = 5
        self.publisher.max_worker = 5
        self.publisher.min_worker = 1

        def _fake_start_worker():
            fake_worker = MagicMock(spec=Worker)
            self.publisher.workers.append(fake_worker)

        m_start_worker.side_effect = _fake_start_worker

        self.publisher.start_worker()  # Add a fake worker
        self.publisher.msg_queue.put("Dummy1")  # Add a fake job in the queue
        self.publisher.msg_queue.put("Dummy2")
        self.publisher.msg_queue.put("Dummy3")
        self.publisher.adjust_pool_size()

        self.assertEqual(self.publisher.num_workers, 4)

    @patch.object(Publisher, "start_worker")
    def test_adjust_pool_size_shrink_pool(self, m_start_worker):
        self.publisher.max_queue_size = 5
        self.publisher.max_worker = 5
        self.publisher.min_worker = 1

        def _fake_start_worker():
            fake_worker = MagicMock(spec=Worker)
            self.publisher.workers.append(fake_worker)

        m_start_worker.side_effect = _fake_start_worker

        self.publisher.start_worker()  # Add a fake worker
        self.publisher.start_worker()
        self.publisher.start_worker()
        self.publisher.start_worker()
        self.publisher.start_worker()

        self.publisher.msg_queue.put("Dummy1")  # Add a fake job in the queue
        self.publisher.adjust_pool_size()

        self.assertEqual(self.publisher.num_workers, 2)

    @patch.object(Publisher, "start_worker")
    def test_adjust_pool_size_keep_same_size(self, m_start_worker):
        self.publisher.max_queue_size = 5
        self.publisher.max_worker = 5
        self.publisher.min_worker = 1

        def _fake_start_worker():
            fake_worker = MagicMock(spec=Worker)
            self.publisher.workers.append(fake_worker)

        m_start_worker.side_effect = _fake_start_worker

        self.publisher.start_worker()  # Add a fake worker
        self.publisher.msg_queue.put("Dummy1")  # Add a fake job in the queue
        self.publisher.adjust_pool_size()

        self.assertEqual(self.publisher.num_workers, 1)

    @patch.object(Publisher, "start_worker")
    def test_check_workers_alive(self, m_start_worker):
        self.publisher.max_worker = 1
        self.publisher.min_worker = 1

        fake_worker_dead = MagicMock(spec=Worker, is_alive=lambda: False)
        fake_worker_alive = MagicMock(spec=Worker, is_alive=lambda: True)

        def _fake_start_worker():
            self.publisher.workers.append(fake_worker_dead)
            yield
            self.publisher.workers.append(fake_worker_alive)
            yield

        m_start_worker.side_effect = _fake_start_worker()
        self.publisher.start_worker()

        self.publisher.check_workers_alive()
        self.assertEqual(self.publisher.num_workers, 1)
        self.assertEqual(self.publisher.workers[0].is_alive(), True)

    def test_start_worker(self):
        self.publisher.start_worker()
        self.assertEqual(len(self.publisher.workers), 1)
        self.assertEqual(self.publisher.num_workers, 1)

    def test_stop_worker(self):
        self.publisher.start_worker()
        self.publisher.start_worker()
        self.publisher.stop_worker()
        self.assertEqual(len(self.publisher.workers), 1)
        self.assertEqual(self.publisher.num_workers, 1)

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.publisher.base.os.environ.get")
    def test_setup_nanoconfig_valid_using_default(self, m_env_getter,
                                                  m_env_setter):
        # Override default where it is set to False
        m_env_getter.side_effect = ["FAKE_NN_CONFIG_SERVICE",
                                    "FAKE_NN_CONFIG_UPDATES"]
        self.publisher.use_nanoconfig_service = True
        self.publisher.nanoconfig_service_endpoint = ""
        self.publisher.nanoconfig_update_endpoint = ""
        self.publisher.setup_socket()

        self.assertEqual(m_env_getter.call_count, 2)
        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")  # First call
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")  # Last call
        self.assertEqual(m_env_setter.call_count, 0)
        self.assertEqual(self.publisher.nanoconfig_service_endpoint,
                         "FAKE_NN_CONFIG_SERVICE")
        self.assertEqual(self.publisher.nanoconfig_update_endpoint,
                         "FAKE_NN_CONFIG_UPDATES")

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.publisher.base.os.environ.get")
    def test_setup_nanoconfig_valid_custom_values(self, m_env_getter,
                                                  m_env_setter):
        # Override default where it is set to False
        m_env_getter.side_effect = ["FAKE_NN_CONFIG_SERVICE",
                                    "FAKE_NN_CONFIG_UPDATES"]
        self.publisher.use_nanoconfig_service = True
        self.publisher.nanoconfig_service_endpoint = "CUSTOM_NN_CONFIG_SERVICE"
        self.publisher.nanoconfig_update_endpoint = "CUSTOM_NN_CONFIG_UPDATES"
        self.publisher.setup_socket()

        self.assertEqual(m_env_getter.call_count, 2)
        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")
        m_env_setter.assert_any_call("NN_CONFIG_SERVICE",
                                     "CUSTOM_NN_CONFIG_SERVICE")
        m_env_setter.assert_called_with("NN_CONFIG_UPDATES",
                                        "CUSTOM_NN_CONFIG_UPDATES")
        self.assertEqual(self.publisher.nanoconfig_service_endpoint,
                         "CUSTOM_NN_CONFIG_SERVICE")
        self.assertEqual(self.publisher.nanoconfig_update_endpoint,
                         "CUSTOM_NN_CONFIG_UPDATES")

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.publisher.base.os.environ.get")
    def test_setup_nanoconfig_invalid_service(self, m_env_getter,
                                              m_env_setter):
        # Override default where it is set to False
        m_env_getter.return_value = ""  # Emulates empty ENV vars
        self.publisher.use_nanoconfig_service = True
        self.publisher.nanoconfig_service_endpoint = ""
        self.publisher.nanoconfig_update_endpoint = "CUSTOM_NN_CONFIG_UPDATES"

        self.assertRaises(ValueError, self.publisher.setup_socket)

        m_env_getter.assert_called_once_with("NN_CONFIG_SERVICE")
        self.assertEqual(m_env_setter.call_count, 0)

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.publisher.base.os.environ.get")
    def test_setup_nanoconfig_invalid_update(self, m_env_getter, m_env_setter):
        # Override default where it is set to False
        m_env_getter.return_value = ""  # Emulates empty ENV vars
        self.publisher.use_nanoconfig_service = True
        self.publisher.nanoconfig_service_endpoint = "CUSTOM_NN_CONFIG_SERVICE"
        self.publisher.nanoconfig_update_endpoint = ""

        self.assertRaises(ValueError, self.publisher.setup_socket)

        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")
        m_env_setter.assert_called_once_with("NN_CONFIG_SERVICE",
                                             "CUSTOM_NN_CONFIG_SERVICE")
