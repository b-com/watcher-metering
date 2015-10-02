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
from watcher_metering.publisher.opts import register_publisher_opts


class ConfFixture(fixtures.Fixture):
    """Fixture to manage global conf settings."""

    def __init__(self, conf):
        self.conf = conf

    def setUp(self):
        super(ConfFixture, self).setUp()
        register_publisher_opts(self.conf)
        self.conf.register_opts(log_config.generic_log_opts)
        self.conf.register_opts(log_config.log_opts)
        self.conf.register_opts(log_config.common_cli_opts)
        self.conf.register_opts(log_config.logging_cli_opts)
        self.conf([], project='watcher_metering', default_config_files=[])
        self.conf.set_override('debug', True)
        self.addCleanup(self.conf.reset)
