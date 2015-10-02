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

from collections import OrderedDict
from unittest import TestCase

from mock import patch
import msgpack
from watcher_metering.agent.measurement import Measurement
from watcher_metering.agent.puller import MetricPuller


class FakeMetricPuller(MetricPuller):

    @classmethod
    def get_name(cls):
        return 'dummy'

    @classmethod
    def get_default_probe_id(cls):
        return 'dummy.data.puller'

    @classmethod
    def get_default_interval(cls):
        return 1

    def do_pull(self):
        return


class TestMetricPuller(TestCase):

    @patch.object(Measurement, "as_dict")
    def test_puller_send_measurements(self, m_as_dict):
        data_puller = FakeMetricPuller(
            title=FakeMetricPuller.get_entry_name(),
            probe_id=FakeMetricPuller.get_default_probe_id(),
            interval=FakeMetricPuller.get_default_interval(),
        )
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

        with patch.object(MetricPuller, 'notify') as m_notify:
            data_puller.send_measurements([measurement])

        expected_encoded_msg = msgpack.dumps(measurement_dict)

        self.assertTrue(m_notify.called)
        m_notify.assert_called_once_with(expected_encoded_msg)
