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

from threading import Thread

from oslo_config import cfg
from oslo_log import log
from watcher_metering.store.loader import StoreClientLoader

LOG = log.getLogger(__name__)


class Worker(Thread):

    def __init__(self, queue, client_name):
        super(Worker, self).__init__()
        self.queue = queue
        self._terminated = False
        self.setDaemon(True)

        self._client_name = client_name
        self._client_loader = StoreClientLoader(cfg.CONF, client_name)
        self.client = self._client_loader.load()

    @property
    def terminated(self):
        return self._terminated

    @terminated.setter
    def terminated(self, value):
        self._terminated = value

    def run(self):
        LOG.info("[Worker] Worker `%r` is now running", self)
        try:
            self.client.connect()
        except Exception as exc:
            LOG.exception(exc)
        LOG.info("[Worker] Worker `%r` is now connected to the store", self)

        while not self.terminated:
            try:
                LOG.info("[Worker] Waiting for a message...")
                msg = self.queue.get()
                LOG.info("[Worker] Sending the message to the store: %r", msg)
                self.client.send(msg)
            except Exception as exc:
                # Error ignored not to keep our worker running
                LOG.exception(exc)
            else:
                LOG.info("[Worker] Message sent successfully!")

        try:
            self.client.disconnect()
        except Exception as exc:
            LOG.exception(exc)

    def stop(self):
        self.terminated = True
