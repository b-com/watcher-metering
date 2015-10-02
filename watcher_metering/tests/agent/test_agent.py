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
import types

from mock import MagicMock
from mock import Mock
from mock import patch
from mock import PropertyMock
import msgpack
import operator
from oslo_config import cfg
from oslotest.base import BaseTestCase
from stevedore.driver import DriverManager
from stevedore.extension import Extension
from watcher_metering.agent.agent import Agent
from watcher_metering.agent.measurement import Measurement
from watcher_metering.tests.agent.agent_fixtures import ConfFixture
from watcher_metering.tests.agent.agent_fixtures import DummyMetricPuller
from watcher_metering.tests.agent.agent_fixtures import FakeMetricPuller


class TestAgent(BaseTestCase):

    # patches to be applied for each test in this test suite
    patches = []

    def setUp(self):
        super(TestAgent, self).setUp()
        self.conf = cfg.ConfigOpts()
        # To load the drivers without using the config file
        self.useFixture(ConfFixture(self.conf))

        def _fake_parse(self, args=[]):
            return cfg.ConfigOpts._parse_cli_opts(self, [])

        _fake_parse_method = types.MethodType(_fake_parse, self.conf)
        self.conf._parse_cli_opts = _fake_parse_method

        # First dependency to be returned
        self.dummy_driver_manager = DriverManager.make_test_instance(
            extension=Extension(
                name=DummyMetricPuller.get_name(),
                entry_point='fake.entry.point',
                plugin=DummyMetricPuller,
                obj=None,
            ),
            namespace='TESTING',
        )
        # 2nd dependency to be returned
        self.fake_driver_manager = DriverManager.make_test_instance(
            extension=Extension(
                name=FakeMetricPuller.get_name(),
                entry_point='fake.entry.point',
                plugin=FakeMetricPuller,
                obj=None,
            ),
            namespace='TESTING',
        )
        self.defaults_drivers = {
            DummyMetricPuller.get_name(): self.dummy_driver_manager,
            FakeMetricPuller.get_name(): self.fake_driver_manager,
        }

        def _fake_loader(name, **kw):
            return self.defaults_drivers[name]

        # Patches the agent socket
        self.m_agent_socket = MagicMock(autospec=True)

        self.patches.extend([
            # Deactivates the nanomsg socket
            patch(
                "watcher_metering.agent.agent.nanomsg.Socket",
                new=self.m_agent_socket,
            ),
            # Sets the test namespace to 'TESTING'
            patch.object(
                Agent,
                "namespace",
                PropertyMock(return_value='TESTING'),
            ),
            # Patches the driver manager to retourn our test drivers
            # instead of the real ones
            patch(
                "watcher_metering.load.loader.DriverManager",
                MagicMock(side_effect=_fake_loader),
            ),
        ])

        # Applies all of our patches before each test
        for _patch in self.patches:
            _patch.start()

        self.agent = Agent(
            conf=self.conf,
            driver_names=self.conf.agent.driver_names,
            use_nanoconfig_service=False,
            publisher_endpoint="fake",
            nanoconfig_service_endpoint="",
            nanoconfig_update_endpoint="",
            nanoconfig_profile="nanoconfig://test_profile"
        )
        # Default ticking is set to 0 to reduce test execution time
        self.agent.TICK_INTERVAL = 0

    def tearDown(self):
        super(TestAgent, self).tearDown()
        # The drivers are stored at the class level so we need to clear
        # it after each test
        self.agent.drivers.clear()
        for _patch in self.patches:
            _patch.stop()

    def test_register_driver(self):
        expected_driver1_key = "metrics_driver.dummy_data.puller.dummy"
        expected_driver2_key = "metrics_driver.fake_data.puller.fake"

        self.agent.register_drivers()

        self.assertEqual(
            sorted(self.agent.drivers.keys()),
            [expected_driver1_key, expected_driver2_key]
        )
        sorted_drivers = OrderedDict(
            sorted(self.agent.drivers.items(), key=operator.itemgetter(0))
        )
        self.assertEqual(len(sorted_drivers), 2)
        driver1 = self.agent.drivers[expected_driver1_key]
        driver2 = self.agent.drivers[expected_driver2_key]

        self.assertEqual(driver1.title, "metrics_driver.dummy")
        self.assertEqual(driver1.probe_id, "data.puller.dummy")
        self.assertEqual(driver1.interval, 0.01)

        self.assertEqual(driver2.title, "metrics_driver.fake")
        self.assertEqual(driver2.probe_id, "data.puller.fake")
        self.assertEqual(driver2.interval, 0.01)

        self.assertIn(self.agent, driver1._observers)
        self.assertIn(self.agent, driver2._observers)

    def test_unregister_driver(self):
        driver_key = "metrics_driver.dummy_data.puller.dummy"
        self.agent.register_drivers()
        self.agent.unregister_driver(driver_key)

        # Initial is 2 drivers => 2 - 1 == 1
        self.assertEqual(len(self.agent.drivers), 1)

    @patch.object(Measurement, "as_dict")
    def test_send_measurements(self, m_as_dict):
        self.agent.register_drivers()

        measurement_dict = OrderedDict(
            name="dummy.data.puller",
            unit="",
            type_="",
            value=13.37,
            resource_id="test_hostname",
            host="test_hostname",
            timestamp="2015-08-04T15:15:45.703542",
        )
        m_as_dict.return_value = measurement_dict

        measurement = Measurement(**measurement_dict)

        for driver in self.agent.drivers.values():
            driver.send_measurements([measurement])
            break  # only the first one
        expected_encoded_msg = msgpack.dumps(measurement_dict)
        self.m_agent_socket.return_value.send.assert_called_once_with(
            expected_encoded_msg
        )

    @patch.object(DummyMetricPuller, "is_alive")
    @patch.object(DummyMetricPuller, "start")
    @patch("watcher_metering.agent.manager.MetricManager.lock")
    def test_check_drivers_alive(self, m_lock, m_start, m_is_alive):
        m_lock.acquire = Mock(return_value=True)  # Emulates a thread behavior
        m_lock.release = Mock(return_value=True)  # Emulates a thread behavior
        m_is_alive.return_value = True  # Emulates a thread that is running
        m_start.return_value = None

        self.agent.register_drivers()
        self.agent.check_drivers_alive()

        self.assertTrue(m_is_alive.called)
        self.assertFalse(m_start.called)

    @patch.object(DummyMetricPuller, "is_alive")
    @patch.object(DummyMetricPuller, "start")
    @patch("watcher_metering.agent.manager.MetricManager.lock")
    def test_check_drivers_alive_with_driver_stopped(self, m_lock, m_start,
                                                     m_is_alive):
        m_lock.acquire = Mock(return_value=True)  # Emulates a thread behavior
        m_lock.release = Mock(return_value=True)  # Emulates a thread behavior
        m_is_alive.side_effect = [False, True]
        m_start.side_effect = [RuntimeError, True, True]  # Fails once

        self.agent.register_drivers()
        # should re-run the driver
        self.agent.check_drivers_alive()

        self.assertEqual(m_is_alive.call_count, 1)
        self.assertEqual(m_start.call_count, 2)

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.agent.agent.os.environ.get")
    def test_setup_nanoconfig_valid_using_default(self, m_env_getter,
                                                  m_env_setter):
        # Override default where it is set to False
        m_env_getter.side_effect = ["FAKE_NN_CONFIG_SERVICE",
                                    "FAKE_NN_CONFIG_UPDATES"]
        self.agent.use_nanoconfig_service = True
        self.agent.nanoconfig_service_endpoint = ""
        self.agent.nanoconfig_update_endpoint = ""
        self.agent.set_nanoconfig_endpoints()

        self.assertEqual(m_env_getter.call_count, 2)
        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")  # First call
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")  # Last call
        self.assertEqual(m_env_setter.call_count, 0)
        self.assertEqual(self.agent.nanoconfig_service_endpoint,
                         "FAKE_NN_CONFIG_SERVICE")
        self.assertEqual(self.agent.nanoconfig_update_endpoint,
                         "FAKE_NN_CONFIG_UPDATES")

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.agent.agent.os.environ.get")
    def test_setup_nanoconfig_valid_custom_values(self, m_env_getter,
                                                  m_env_setter):
        # Override default where it is set to False
        m_env_getter.side_effect = ["FAKE_NN_CONFIG_SERVICE",
                                    "FAKE_NN_CONFIG_UPDATES"]
        self.agent.use_nanoconfig_service = True
        self.agent.nanoconfig_service_endpoint = "CUSTOM_NN_CONFIG_SERVICE"
        self.agent.nanoconfig_update_endpoint = "CUSTOM_NN_CONFIG_UPDATES"
        self.agent.set_nanoconfig_endpoints()

        self.assertEqual(m_env_getter.call_count, 2)
        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")
        m_env_setter.assert_any_call("NN_CONFIG_SERVICE",
                                     "CUSTOM_NN_CONFIG_SERVICE")
        m_env_setter.assert_called_with("NN_CONFIG_UPDATES",
                                        "CUSTOM_NN_CONFIG_UPDATES")
        self.assertEqual(self.agent.nanoconfig_service_endpoint,
                         "CUSTOM_NN_CONFIG_SERVICE")
        self.assertEqual(self.agent.nanoconfig_update_endpoint,
                         "CUSTOM_NN_CONFIG_UPDATES")

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.agent.agent.os.environ.get")
    def test_setup_nanoconfig_invalid_service(self, m_env_getter,
                                              m_env_setter):
        # Override default where it is set to False
        m_env_getter.return_value = ""  # Emulates empty ENV vars
        self.agent.use_nanoconfig_service = True
        self.agent.nanoconfig_service_endpoint = ""
        self.agent.nanoconfig_update_endpoint = "CUSTOM_NN_CONFIG_UPDATES"

        self.assertRaises(ValueError, self.agent.set_nanoconfig_endpoints)

        m_env_getter.assert_called_once_with("NN_CONFIG_SERVICE")
        self.assertEqual(m_env_setter.call_count, 0)

    @patch.object(os._Environ, "__setitem__")
    @patch("watcher_metering.agent.agent.os.environ.get")
    def test_setup_nanoconfig_invalid_update(self, m_env_getter, m_env_setter):
        # Override default where it is set to False
        m_env_getter.return_value = ""  # Emulates empty ENV vars
        self.agent.use_nanoconfig_service = True
        self.agent.nanoconfig_service_endpoint = "CUSTOM_NN_CONFIG_SERVICE"
        self.agent.nanoconfig_update_endpoint = ""

        self.assertRaises(ValueError, self.agent.set_nanoconfig_endpoints)

        m_env_getter.assert_any_call("NN_CONFIG_SERVICE")
        m_env_getter.assert_called_with("NN_CONFIG_UPDATES")
        m_env_setter.assert_called_once_with("NN_CONFIG_SERVICE",
                                             "CUSTOM_NN_CONFIG_SERVICE")

    @patch.object(Agent, 'check_drivers_alive', MagicMock())
    @patch("watcher_metering.agent.manager."
           "MetricManager.terminated",
           new_callable=PropertyMock)
    def test_run_agent(self, m_terminated):
        # Patches the guard/exit condition of the thread periodic event loop
        # -> 1st time = False (carry on) and 2nd = True (Should terminate)
        m_terminated.side_effect = [False, True]

        self.agent.run()

        self.assertEqual(m_terminated.call_count, 2)

    @patch.object(DummyMetricPuller, 'send_measurements', MagicMock())
    def test_stop_agent(self):
        self.agent.register_drivers()

        self.agent.start()
        self.agent.join(timeout=.01)
        self.agent.stop()

        self.assertEqual(len(self.agent.drivers.values()), 2)
        self.assertTrue(
            all([driver.terminated for driver in self.agent.drivers.values()])
        )
        self.assertTrue(self.agent.terminated)
        self.assertFalse(self.agent.is_alive())
