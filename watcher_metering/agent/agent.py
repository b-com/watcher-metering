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

"""In charge of collecting data from drivers and push it to the publisher."""

import os

import msgpack
import nanomsg
from oslo_log import log
from watcher_metering.agent.manager import MetricManager

LOG = log.getLogger(__name__)


class Agent(MetricManager):

    def __init__(self, conf, driver_names, use_nanoconfig_service,
                 publisher_endpoint, nanoconfig_service_endpoint,
                 nanoconfig_update_endpoint, nanoconfig_profile):
        """
        :param conf: Configuration obtained from a configuration file
        :type conf: oslo_config.cfg.ConfigOpts instance
        :param driver_names: The list of driver names to register
        :type driver_names: list of str
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
        """
        super(Agent, self).__init__(conf, driver_names)
        self.socket = nanomsg.Socket(nanomsg.PUSH)
        self.use_nanoconfig_service = use_nanoconfig_service
        self.publisher_endpoint = publisher_endpoint
        self.nanoconfig_service_endpoint = nanoconfig_service_endpoint
        self.nanoconfig_update_endpoint = nanoconfig_update_endpoint
        self.nanoconfig_profile = nanoconfig_profile

    @property
    def namespace(self):
        return "watcher_metering.drivers"

    def start(self):
        LOG.info("[Agent] Starting main thread...")
        super(Agent, self).start()

    def setup_socket(self):
        if self.use_nanoconfig_service:
            self.set_nanoconfig_endpoints()
            self.socket.configure(self.nanoconfig_profile)
            LOG.info("[Agent] Agent nanomsg's profile `%s`",
                     self.nanoconfig_profile)
        else:
            LOG.debug("[Agent] Agent connected to: `%s`",
                      self.publisher_endpoint)
            self.socket.connect(self.publisher_endpoint)
        LOG.info("[Agent] Ready for pushing to Publisher node")

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

    def run(self):
        self.setup_socket()
        super(Agent, self).run()

    def stop(self):
        self.socket.close()
        super(Agent, self).stop()
        LOG.debug("[Agent] Stopped")

    def update(self, notifier, data):
        LOG.debug("[Agent] Updated by: %s", notifier)
        LOG.debug("[Agent] Preparing to send message %s", msgpack.loads(data))
        try:
            LOG.debug("[Agent] Sending message...")
            # The agent will wait for the publisher server to be listening on
            # the related publisher_endpoint before continuing
            # In which case, you should start the publisher to make it work!
            self.socket.send(data)
            LOG.debug("[Agent] Message sent successfully!")
        except nanomsg.NanoMsgError as exc:
            LOG.error("Exception during sending the message to controller %s",
                      exc.args[0])
