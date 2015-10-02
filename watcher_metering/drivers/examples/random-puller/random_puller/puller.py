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

import datetime
import platform
import random

from oslo_config import cfg
from watcher_metering.agent.measurement import Measurement
from watcher_metering.agent.puller import MetricPuller


class RandomDataPuller(MetricPuller):
    """
    This is a demo drivers which shows how a driver should be implemented in
    order to gather data from a source
    """
    def __init__(self, title, probe_id, interval, static_data):
        super(RandomDataPuller, self).__init__(title, probe_id, interval)
        self.static_data = static_data

    @classmethod
    def get_config_opts(cls):
        return cls.get_base_opts() + [
            cfg.StrOpt('static_data', default="static_data", required=True),
        ]

    @classmethod
    def get_name(cls):
        return "random"

    @classmethod
    def get_default_probe_id(cls):
        return "data.puller.random"

    @classmethod
    def get_default_interval(cls):
        return 5  # In seconds

    def do_pull(self):
        random_value = random.Random().randint(1, 10)
        random_message = "[%s] random data generated on %s" % (
            random_value, datetime.datetime.now()
        )
        measurement = Measurement(
            name=self.probe_id,
            unit="",
            type_="",
            value=random_value,
            resource_id=platform.node(),
            resource_metadata={
                "state": "ok",
                "static_data": self.static_data,
                "description": random_message
            },
        )
        return [measurement]
