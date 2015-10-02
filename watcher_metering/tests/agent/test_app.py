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

from mock import Mock
from mock import patch
from oslo_config import cfg
from oslotest.base import BaseTestCase
from watcher_metering.agent.agent import Agent
from watcher_metering.agent import app
from watcher_metering.tests.agent.app_fixtures import ConfFixture


class TestAgentApp(BaseTestCase):

    def setUp(self):
        super(TestAgentApp, self).setUp()

        self.conf = cfg.CONF
        self.useFixture(ConfFixture(self.conf))

        def _fake_parse(self, args=[]):
            return cfg.ConfigOpts._parse_cli_opts(self, [])

        _fake_parse_method = types.MethodType(_fake_parse, self.conf)
        self.conf._parse_cli_opts = _fake_parse_method

    @patch.object(Agent, "register_drivers", Mock())
    @patch.object(Agent, "join")
    @patch.object(Agent, "start")
    def test_run_agent_app(self, m_agent_start, m_agent_join):
        app.start_agent()
        self.assertEqual(m_agent_start.call_count, 1)
        self.assertEqual(m_agent_join.call_count, 1)
