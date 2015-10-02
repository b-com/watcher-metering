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

import abc
import datetime
from threading import Lock
from threading import Thread
import time

import msgpack
from oslo_config import cfg
from oslo_log import log
import six
from watcher_metering.agent.measurement import Measurement
from watcher_metering.agent.utils.observable import Observable
from watcher_metering.load.loadable import Loadable

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class MetricPuller(Observable, Thread, Loadable):

    lock = Lock()

    # the title will be display on the dashboard via logstash
    # the probe_id is used in internal for ceilometer
    def __init__(self, title, probe_id, interval):
        super(MetricPuller, self).__init__()
        self.title = title
        self.probe_id = probe_id
        self.interval = interval
        self.setDaemon(True)
        self._terminated = False

    @classmethod
    def get_base_opts(cls):
        return [
            cfg.StrOpt(
                'title', help="Title of the data puller",
                default=cls.get_entry_name(), required=True),
            cfg.StrOpt(
                'probe_id', help="Probe ID of the data puller",
                default=cls.get_default_probe_id(), required=True),
            cfg.FloatOpt(
                'interval',
                help="Time interval (in seconds) between each data pulling",

                default=cls.get_default_interval(), required=True),
        ]

    @classmethod
    def namespace(cls):
        return "metrics_driver"

    @classmethod
    def get_config_opts(cls):
        """Should return the list of options relative to this data puller
           IMPORTANT: this is class method, overload it with @classmethod!
        """
        return cls.get_base_opts()

    @classmethod
    def get_external_opts_configs(cls):
        """
        :return: A list of external import config instances ready to be
                 used by the loader manager
        :rtype: a list of ExternalOptConfig instances
        """
        return []

    @classmethod
    @abc.abstractmethod
    def get_default_probe_id(cls):
        """Should return the entry point name given in the setup file
           IMPORTANT: this is class method, overload it with @classmethod!
        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    @abc.abstractmethod
    def get_default_interval(cls):
        """Should return the entry point name given in the setup file
           IMPORTANT: this is class method, overload it with @classmethod!
        """
        raise NotImplementedError  # pragma: nocover

    @property
    def terminated(self):
        return self._terminated

    @terminated.setter
    def terminated(self, value):
        self._terminated = value

    @property
    def key(self):
        return "%s_%s" % (self.title, self.probe_id)

    def join(self, timeout=None):
        self.stop()
        super(MetricPuller, self).join(timeout)

    def send_measurements(self, measurements):
        """
        Send the measurements acquired by the data puller to the publisher

        :param measurements: List of measurements to be sent over
        :type measurements: list of :class:`Measurement` instances
        """
        if not self.terminated:
            LOG.debug("[%s] Sending measurements", self.key)
            for measurement in measurements:
                try:
                    encoded_msg = msgpack.dumps(measurement.as_dict())
                    self.notify(encoded_msg)
                except Exception as exc:
                    LOG.error("==>[Exception] %s", exc.args[0])
                LOG.debug("[%s] Measurement sent!", self.key)

    def stop(self):
        self.terminated = True

    def run(self):
        while not self.terminated:
            exec_start_time = datetime.datetime.now()
            try:
                # Maybe we can use 'yield' to pull our metrics
                # without having to buffer them
                measurements = self.pull_data()
                if isinstance(measurements, Measurement):
                    # If sending a single measure at a time
                    # -> handles the missing brackets
                    measurements = [measurements]
                self.send_measurements(measurements)
            except Exception as exc:
                LOG.error("[%s] Unexpected error during pulling: %s",
                          unicode(self),
                          exc.args[0])
            time.sleep(self._adjust_sleep_interval(exec_start_time))

    def _adjust_sleep_interval(self, start_time):
        td = datetime.datetime.now() - start_time
        duration_to_sleep = self.interval - td.total_seconds()
        return 0 if duration_to_sleep < 0 else duration_to_sleep

    def pull_data(self):
        """do_pull proxy:
        Left there in case we need to add an execution timeout
        """
        return self.do_pull()

    @abc.abstractmethod
    def do_pull(self):
        """This method is responsible for pulling/collecting the data
        :returns: The list of measurements to be pushed to the manager
        :rtype: list of Measurement objects
        """
        raise NotImplementedError

    def __unicode__(self):
        return self.key
