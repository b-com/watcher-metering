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

from threading import Thread

from oslo_log import log
from six.moves.queue import Queue
from watcher_metering.publisher.base import PublisherServerBase
from watcher_metering.publisher.worker import Worker

LOG = log.getLogger(__name__)


class Publisher(PublisherServerBase):

    def __init__(self, use_nanoconfig_service, publisher_endpoint,
                 nanoconfig_service_endpoint, nanoconfig_update_endpoint,
                 nanoconfig_profile, metrics_store, max_queue_size,
                 max_worker, min_worker=5):
        """
        :param use_nanoconfig_service: Indicates whether or not it should use a
            nanoconfig service
        :type use_nanoconfig_service: bool
        :param publisher_endpoint: Publisher server URI
        :type publisher_endpoint: str
        :param nanoconfig_service_endpoint: Nanoconfig service URI
        :type nanoconfig_service_endpoint: str
        :param nanoconfig_update_endpoint: Nanoconfig update service URI
        :type nanoconfig_update_endpoint: str
        :param nanoconfig_profile: Nanoconfig profile URI
        :type nanoconfig_profile: str
        :param max_queue_size: Max size for the message queue
        :type max_queue_size: int
        :param max_worker: Max number of worker to be spawned at a given time
        :type max_worker: int
        :param min_worker: Min number of worker to be spawned at a given time
        :type min_worker: int
        """
        super(Publisher, self).__init__(
            use_nanoconfig_service, publisher_endpoint,
            nanoconfig_service_endpoint, nanoconfig_update_endpoint,
            nanoconfig_profile
        )
        self.max_queue_size = max_queue_size
        self.metrics_store = metrics_store
        self.min_worker = min_worker
        self.max_worker = max_worker

        self.msg_queue = Queue(self.max_queue_size)
        self.workers = []

    @property
    def num_workers(self):
        return len(self.workers)

    def on_receive(self, msg):
        LOG.debug('[Publisher] Queue msg size = %s | workers = %s',
                  self.msg_queue.qsize(), self.num_workers)
        try:
            self.check_workers_alive()
            self.adjust_pool_size()
        except OSError as exc:
            LOG.exception(exc)
            LOG.error("[Publisher] Error upon receiving a message")

        self.msg_queue.put(msg)

    def check_workers_alive(self):
        # Because we can create new workers in this loop, we create a copy
        # --> We could otherwise loop onto a new workers...
        worker_items = self.workers[:]
        for worker_thread in worker_items:
            if not worker_thread.is_alive():
                self.workers.pop(self.workers.index(worker_thread))
                self.start_worker()

    def adjust_pool_size(self):
        needed_size = self.msg_queue.qsize() + self.min_worker
        if abs(needed_size - self.num_workers) > self.min_worker * 2:
            LOG.debug(("[Publisher] Auto adjust pool size needed size is `%s` "
                       "and the current size is `%s`"),
                      needed_size, self.num_workers)
            while self.num_workers > min(self.min_worker, needed_size):
                self.stop_worker()
            # Create enough, but not too many
            while self.num_workers < min(self.max_worker, needed_size):
                self.start_worker()

    def start_worker(self):
        LOG.debug("[Publisher] starting worker")
        worker = Worker(self.msg_queue, self.metrics_store)
        worker.start()
        self.workers.append(worker)

    def stop_worker(self):
        if self.num_workers:
            LOG.debug("[Publisher] stopping worker")
            worker = self.workers.pop(-1)  # Pops the last worker
            worker.stop()

    def stop(self):
        super(Publisher, self).stop()
        join_threads = []
        for key in self.workers:
            t = Thread(target=self.workers.get(key).stop)
            t.start()
            join_threads.append(t)
        for join_thread in join_threads:
            join_thread.join()
