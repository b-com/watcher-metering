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

from mock import patch
from oslo_config import cfg
from oslotest.base import BaseTestCase
from stevedore.driver import DriverManager
from stevedore.extension import Extension
from watcher_metering.load.loader import DriverLoader
from watcher_metering.tests.loader._fixtures import ConfFixture
from watcher_metering.tests.loader._fixtures import FakeDriverNoGroup
from watcher_metering.tests.loader._fixtures import FakeDriverNoOpt
from watcher_metering.tests.loader._fixtures import FakeDriverWithExternalOpts
from watcher_metering.tests.loader._fixtures import FakeDriverWithOpts


class TestDriverLoader(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestDriverLoader, self).setUp()
        # To load the drivers without using the config file
        self.useFixture(ConfFixture())

        def _fake_parse(self, *args, **kw):
            return cfg.ConfigOpts._parse_cli_opts(cfg.CONF, [])

        cfg.CONF._parse_cli_opts = _fake_parse

        # First dependency to be returned
        self.no_group_driver_manager = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverNoGroup.get_name(),
                entry_point="%s:%s" % (FakeDriverNoGroup.__module__,
                                       FakeDriverNoGroup.__name__),
                plugin=FakeDriverNoGroup,
                obj=None,
            ),
            namespace=FakeDriverNoGroup.namespace(),
        )

        # 2nd dependency to be returned
        self.with_ext_opts_driver_manager = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverWithExternalOpts.get_name(),
                entry_point="%s:%s" % (FakeDriverWithExternalOpts.__module__,
                                       FakeDriverWithExternalOpts.__name__),
                plugin=FakeDriverWithExternalOpts,
                obj=None,
            ),
            namespace=FakeDriverWithExternalOpts.namespace(),
        )

        self.patches.extend([
            # patch.object(cfg, "ConfigOpts", ),
        ])

        # Applies all of our patches before each test
        for _patch in self.patches:
            _patch.start()

    def tearDown(self):
        super(TestDriverLoader, self).tearDown()

        for _patch in self.patches:
            _patch.stop()

    @patch("watcher_metering.load.loader.DriverManager")
    def test_load_driver_no_opt(self, m_driver_manager):
        m_driver_manager.return_value = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverNoOpt.get_name(),
                entry_point="%s:%s" % (FakeDriverNoOpt.__module__,
                                       FakeDriverNoOpt.__name__),
                plugin=FakeDriverNoOpt,
                obj=None,
            ),
            namespace=FakeDriverNoOpt.namespace(),
        )

        loader_manager = DriverLoader(
            conf=cfg.CONF,
            namespace='TESTING',
            name='fake_no_opt'
        )
        loaded_driver = loader_manager.load()

        self.assertEqual(
            isinstance(loaded_driver, FakeDriverNoOpt),
            True
        )

    @patch("watcher_metering.load.loader.DriverManager")
    def test_load_driver_no_group(self, m_driver_manager):
        m_driver_manager.return_value = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverNoGroup.get_name(),
                entry_point="%s:%s" % (FakeDriverNoGroup.__module__,
                                       FakeDriverNoGroup.__name__),
                plugin=FakeDriverNoGroup,
                obj=None,
            ),
            namespace=FakeDriverNoGroup.namespace(),
        )

        loader_manager = DriverLoader(
            conf=cfg.CONF,
            namespace='',
            name='fake_no_group'
        )
        loaded_driver = loader_manager.load()

        self.assertEqual(hasattr(loaded_driver, "test_opt"), True)
        self.assertEqual(loaded_driver.test_opt, "fake_no_group")

    @patch("watcher_metering.load.loader.DriverManager")
    def test_load_driver_with_opts(self, m_driver_manager):
        m_driver_manager.return_value = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverWithOpts.get_name(),
                entry_point="%s:%s" % (FakeDriverWithOpts.__module__,
                                       FakeDriverWithOpts.__name__),
                plugin=FakeDriverWithOpts,
                obj=None,
            ),
            namespace=FakeDriverWithOpts.namespace(),
        )

        loader_manager = DriverLoader(
            conf=cfg.CONF,
            namespace='TESTING',
            name='fake_with_opts'
        )
        loaded_driver = loader_manager.load()

        self.assertEqual(hasattr(loaded_driver, "test_opt"), True)
        self.assertEqual(loaded_driver.test_opt, "fake_with_opts")

    @patch("watcher_metering.load.loader.DriverManager")
    def test_load_driver_with_external_opts(self, m_driver_manager):
        m_driver_manager.return_value = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeDriverWithExternalOpts.get_name(),
                entry_point="%s:%s" % (FakeDriverWithExternalOpts.__module__,
                                       FakeDriverWithExternalOpts.__name__),
                plugin=FakeDriverWithExternalOpts,
                obj=None,
            ),
            namespace=FakeDriverWithExternalOpts.namespace(),
        )

        loader_manager = DriverLoader(
            conf=cfg.CONF,
            namespace='TESTING',
            name='fake_with_ext_opts'
        )
        loaded_driver = loader_manager.load()

        self.assertEqual(
            hasattr(loaded_driver, "fake__test_external_opt"),
            True
        )
        self.assertEqual(
            loaded_driver.fake__test_external_opt,
            "fake_with_ext_opts"
        )
