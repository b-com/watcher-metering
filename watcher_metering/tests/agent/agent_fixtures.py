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

import fixtures
from oslo_log import _options as log_config
from watcher_metering.agent.opts import AGENT_GROUP_NAME
from watcher_metering.agent.opts import register_agent_opts
from watcher_metering.agent.puller import MetricPuller


class ConfFixture(fixtures.Fixture):
    """Fixture to manage global conf settings."""

    def __init__(self, conf):
        self.conf = conf

    def setUp(self):
        super(ConfFixture, self).setUp()
        register_agent_opts(self.conf)
        self.conf.register_opts(log_config.generic_log_opts)
        self.conf.register_opts(log_config.log_opts)
        self.conf.register_opts(log_config.common_cli_opts)
        self.conf.register_opts(log_config.logging_cli_opts)

        self.conf.set_default(
            'driver_names', ['dummy', 'fake'], group=AGENT_GROUP_NAME
        )

        # Driver 1
        self.conf.register_opts(
            DummyMetricPuller.get_base_opts(),
            group=DummyMetricPuller.get_entry_name())
        self.conf.set_default(
            'title',
            default=DummyMetricPuller.get_entry_name(),
            group=DummyMetricPuller.get_entry_name())
        self.conf.set_default(
            'interval',
            default=DummyMetricPuller.get_default_interval(),
            group=DummyMetricPuller.get_entry_name())
        self.conf.set_default(
            'probe_id',
            default=DummyMetricPuller.get_default_probe_id(),
            group=DummyMetricPuller.get_entry_name())

        # Driver 2
        self.conf.register_opts(
            FakeMetricPuller.get_base_opts(),
            group=FakeMetricPuller.get_entry_name())
        self.conf.set_default(
            'title',
            default=FakeMetricPuller.get_entry_name(),
            group=FakeMetricPuller.get_entry_name())
        self.conf.set_default(
            'interval',
            default=FakeMetricPuller.get_default_interval(),
            group=FakeMetricPuller.get_entry_name())
        self.conf.set_default(
            'probe_id',
            default=FakeMetricPuller.get_default_probe_id(),
            group=FakeMetricPuller.get_entry_name())

        self.conf([], project='watcher_metering', default_config_files=[])
        self.addCleanup(self.conf.reset)


class DummyMetricPuller(MetricPuller):

    @classmethod
    def get_name(cls):
        return 'dummy'

    @classmethod
    def get_default_probe_id(cls):
        return 'data.puller.dummy'

    @classmethod
    def get_default_interval(cls):
        return 0.01

    def do_pull(self):
        return [{"data": "DOES NOT MATTER"}]


class FakeMetricPuller(MetricPuller):

    @classmethod
    def get_name(cls):
        return 'fake'

    @classmethod
    def get_default_probe_id(cls):
        return 'data.puller.fake'

    @classmethod
    def get_default_interval(cls):
        return 0.01

    def do_pull(self):
        return [{"data": "DOES NOT MATTER"}]
