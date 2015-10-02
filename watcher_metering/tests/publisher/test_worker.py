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

from collections import OrderedDict

from mock import MagicMock
from mock import patch
from mock import PropertyMock
from oslo_config import cfg
from oslotest.base import BaseTestCase
from six.moves.queue import Queue
from watcher_metering.publisher.worker import Worker
from watcher_metering.store.base import MetricsStoreClientBase
from watcher_metering.store.loader import StoreClientLoader
from watcher_metering.tests.publisher.publisher_fixtures import ConfFixture


class TestWorker(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestWorker, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.useFixture(ConfFixture(self.conf))

        self.m_client = MagicMock(spec=MetricsStoreClientBase)

        self.patches.extend([
            patch.object(
                StoreClientLoader,
                "load",
                new=MagicMock(  # The manager instance
                    return_value=self.m_client
                )
            ),

        ])

        for _patch in self.patches:
            _patch.start()

    def tearDown(self):
        super(TestWorker, self).tearDown()
        for _patch in self.patches:
            _patch.stop()

    @patch.object(Worker, "terminated", new_callable=PropertyMock)
    def test_send_metric(self, m_terminated):
        # mock the termination condition to finish after 1 iteration
        m_terminated.side_effect = [False, True]

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

        queue = Queue()
        queue.put(fake_metric)
        worker = Worker(queue, client_name="riemann")
        worker.run()

        # Should check that the data send over via the Riemann client are OK
        self.m_client.send.assert_called_once_with(fake_metric)
