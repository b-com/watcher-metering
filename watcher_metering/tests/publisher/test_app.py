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

import types

from mock import MagicMock
from mock import patch
from oslo_config import cfg
from oslotest.base import BaseTestCase
from watcher_metering.publisher import app
from watcher_metering.publisher.publisher import Publisher
from watcher_metering.tests.publisher.app_fixtures import ConfFixture


class TestPublisherApp(BaseTestCase):

    def setUp(self):
        super(TestPublisherApp, self).setUp()

        self.conf = cfg.CONF
        self.useFixture(ConfFixture(self.conf))

        def _fake_parse(self, args=[]):
            return cfg.ConfigOpts._parse_cli_opts(self, [])

        _fake_parse_method = types.MethodType(_fake_parse, self.conf)
        self.conf._parse_cli_opts = _fake_parse_method

    @patch("watcher_metering.publisher.worker.StoreClientLoader", MagicMock())
    @patch.object(Publisher, "join")
    @patch.object(Publisher, "start")
    def test_run_publisher_app(self, m_start, m_join):
        app.start_publisher()
        self.assertEqual(m_start.call_count, 1)
        self.assertEqual(m_join.call_count, 1)
