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
from oslo_config import cfg
from oslo_log import _options as log_config
from watcher_metering.load.loadable import ExternalOptConfig
from watcher_metering.load.loadable import Loadable


class ConfFixture(fixtures.Fixture):
    """Fixture to manage global conf settings."""

    def __init__(self):
        cfg.CONF = cfg.ConfigOpts()  # resets the global config
        self.conf = cfg.CONF

    def setUp(self):
        super(ConfFixture, self).setUp()

        self.conf.register_opts(log_config.generic_log_opts)
        self.conf.register_opts(log_config.log_opts)
        self.conf.register_opts(log_config.common_cli_opts)
        self.conf.register_opts(log_config.logging_cli_opts)

        # Driver 1
        self.conf.register_opts(
            FakeDriverNoGroup.get_config_opts(),
            group=FakeDriverNoGroup.get_entry_name())

        # Driver 2
        self.conf.register_opts(
            FakeDriverWithOpts.get_config_opts(),
            group=FakeDriverWithOpts.get_entry_name())

        # Driver 3
        self.conf.register_opts(
            FakeDriverWithExternalOpts.get_config_opts(),
            group=FakeDriverWithExternalOpts.get_entry_name())

        self.conf([], project='watcher_metering', default_config_files=[])
        self.addCleanup(self.conf.reset)


class FakeDriverNoOpt(Loadable):

    @classmethod
    def namespace(cls):
        return "TESTING"

    @classmethod
    def get_name(cls):
        return 'fake_no_opt'

    @classmethod
    def get_config_opts(cls):
        return []

    @classmethod
    def get_external_opts_configs(cls):
        return []


class FakeDriverNoGroup(Loadable):

    def __init__(self, test_opt):
        self.test_opt = test_opt

    @classmethod
    def namespace(cls):
        return ""  # Default namespace

    @classmethod
    def get_name(cls):
        return 'fake_no_group'

    @classmethod
    def get_config_opts(cls):
        return [
            cfg.StrOpt('test_opt', default="fake_no_group", required=True)
        ]

    @classmethod
    def get_external_opts_configs(cls):
        return []


class FakeDriverWithOpts(Loadable):

    def __init__(self, test_opt):
        self.test_opt = test_opt

    @classmethod
    def namespace(cls):
        return "testing"

    @classmethod
    def get_name(cls):
        return 'fake_with_opts'

    @classmethod
    def get_config_opts(cls):
        return [
            cfg.StrOpt('test_opt', default="fake_with_opts", required=True)
        ]

    @classmethod
    def get_external_opts_configs(cls):
        return []


class FakeDriverWithExternalOpts(Loadable):

    def __init__(self, fake__test_external_opt):
        self.fake__test_external_opt = fake__test_external_opt

    @classmethod
    def namespace(cls):
        return "testing"

    @classmethod
    def get_name(cls):
        return 'fake_with_ext_opts'

    @classmethod
    def get_config_opts(cls):
        return []

    @classmethod
    def get_external_opts_configs(cls):
        return [
            ExternalOptConfig(
                name='test_external_opt',
                module_str='watcher_metering.tests.loader.importable_opts',
                group='fake',
            ),
        ]
