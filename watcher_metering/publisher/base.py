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

"""In charge of collecting data from agent(s) and push to openstack_common"""
import abc
import os
import threading

import msgpack
import nanomsg
from oslo_log import log
import six

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class PublisherServerBase(threading.Thread):

    def __init__(self, use_nanoconfig_service, publisher_endpoint,
                 nanoconfig_service_endpoint, nanoconfig_update_endpoint,
                 nanoconfig_profile):
        super(PublisherServerBase, self).__init__()
        self.socket = nanomsg.Socket(nanomsg.PULL)
        self.use_nanoconfig_service = use_nanoconfig_service
        self.publisher_endpoint = publisher_endpoint
        self.nanoconfig_service_endpoint = nanoconfig_service_endpoint
        self.nanoconfig_update_endpoint = nanoconfig_update_endpoint
        self.nanoconfig_profile = nanoconfig_profile

        self.daemon = True
        self._terminated = False
        if os.path.isfile(publisher_endpoint):
            LOG.debug(
                "[Publisher] cleanup socket file `%s`",
                publisher_endpoint
            )
            os.remove(publisher_endpoint)

    @property
    def terminated(self):
        return self._terminated

    @terminated.setter
    def terminated(self, value):
        self._terminated = value

    @abc.abstractmethod
    def on_receive(self, msg):
        """
        Action to be carried upon receiving a message from an agent
        :param msg: The serialized message
        :type msg: str
        """
        raise NotImplementedError

    def setup_socket(self):
        if self.use_nanoconfig_service:
            self.set_nanoconfig_endpoints()
            self.socket.configure(self.nanoconfig_profile)
            LOG.info("[Publisher] Publisher configured using "
                     "nanoconfig `%s` profile", self.nanoconfig_profile)
        else:
            self.socket.bind(self.publisher_endpoint)
            LOG.info("[Publisher] Publisher bound to: `%s`",
                     self.publisher_endpoint)

    def set_nanoconfig_endpoints(self):
        """This methods sets both the `NN_CONFIG_SERVICE` and
        `NN_CONFIG_UPDATES` environment variable as nanoconfig uses it to
        access the nanoconfig service
        """
        # NN_CONFIG_SERVICE:
        nn_config_service = os.environ.get("NN_CONFIG_SERVICE")
        if not self.nanoconfig_service_endpoint and not nn_config_service:
            raise ValueError(
                "Invalid configuration! No NN_CONFIG_SERVICE set. You need to "
                "configure your `nanoconfig_service_endpoint`.")
        if self.nanoconfig_service_endpoint:
            os.environ["NN_CONFIG_SERVICE"] = self.nanoconfig_service_endpoint
        else:
            self.nanoconfig_service_endpoint = nn_config_service

        # NN_CONFIG_UPDATES
        nn_config_updates = os.environ.get("NN_CONFIG_UPDATES")
        if not self.nanoconfig_update_endpoint and not nn_config_updates:
            raise ValueError(
                "Invalid configuration! No NN_CONFIG_UPDATES set. You need to "
                "configure your `nanoconfig_update_endpoint`.")
        if self.nanoconfig_update_endpoint:
            os.environ["NN_CONFIG_UPDATES"] = self.nanoconfig_update_endpoint
        else:
            self.nanoconfig_update_endpoint = nn_config_updates

    def stop(self):
        super(PublisherServerBase, self).stop()
        self.socket.close()
        self.terminated = True

    def run(self):
        try:
            self.setup_socket()
        except nanomsg.NanoMsgError as exc:
            LOG.error("[Publisher] Unable to bind to `%s`\nException<%s>",
                      self.publisher_endpoint, exc.args[0])
            self.stop()

        while not self.terminated:
            try:
                LOG.debug("[Publisher] Waiting for message")
                raw = self.socket.recv()
                msg = msgpack.loads(raw, encoding='utf-8')
                LOG.debug("[Publisher] Received message --> `%r`", msg)
                self.on_receive(msg)
            except (ValueError,
                    msgpack.ExtraData,
                    nanomsg.NanoMsgError) as exc:
                LOG.error(
                    "Exception upon receiving message from agent `%s`",
                    exc.args[0]
                )
