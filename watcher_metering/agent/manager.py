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
from collections import OrderedDict
from threading import Lock
from threading import Thread
import time

from oslo_log import log
import six
from watcher_metering.agent.loader import MetricsDriverLoader

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class MetricManager(Thread):

    drivers = OrderedDict()
    lock = Lock()

    TICK_INTERVAL = 5  # In seconds

    def __init__(self, conf, driver_names):
        super(MetricManager, self).__init__()
        self.conf = conf
        self.driver_names = driver_names
        self._terminated = False
        self.daemon = True

    @property
    def terminated(self):
        return self._terminated

    @terminated.setter
    def terminated(self, value):
        self._terminated = value

    @abc.abstractproperty
    def namespace(self):
        raise NotImplementedError  # pragma: no cover

    def register_drivers(self):
        self.lock.acquire()
        for driver_name in self.driver_names:
            LOG.info("Registering `%s`", driver_name)
            self._register_driver(driver_name)
        self.lock.release()

    def _register_driver(self, driver_name):
        driver_manager = MetricsDriverLoader(
            conf=self.conf,
            driver_name=driver_name,
        )

        driver = driver_manager.load()

        self.drivers[driver.key] = driver
        driver.register_observer(self)

    def unregister_driver(self, key):
        driver = self.drivers.pop(key)
        driver.unregister_observer(self)

    def run(self):
        while not self.terminated:
            self.check_drivers_alive()
            time.sleep(self.TICK_INTERVAL)

    def check_drivers_alive(self):
        if self.lock.acquire(False):
            # Because we can edit the drivers in this loop, we create a copy
            # --> We could therwise loop onto a restarted driver...
            driver_items = [item for item in self.drivers.items()]
            for driver_name, driver_thread in driver_items:
                if not driver_thread.is_alive():
                    LOG.debug("Starting driver %s", driver_thread.key)
                    try:
                        driver_thread.start()
                    except RuntimeError as exc:
                        LOG.exception(exc)
                        # Case where the driver "died"
                        # -> we need to spawn a new one
                        #    because thread can only be started once
                        self.unregister_driver(driver_name)
                        self._register_driver(driver_thread.get_name())
                        reloaded_driver_thread = self.drivers[driver_name]
                        reloaded_driver_thread.start()

            self.lock.release()

    def stop(self):
        self.terminated = True
        self.lock.acquire()

        join_threads = []
        for key in self.drivers:
            t = Thread(target=self.drivers.get(key).join)
            t.start()
            join_threads.append(t)

        for join_thread in join_threads:
            join_thread.join()

        self.lock.release()
