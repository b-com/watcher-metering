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

import calendar
import struct

from dateutil import parser
from oslo_config import cfg
from oslo_log import log
from riemann_client.client import Client
from riemann_client.riemann_pb2 import Event
from riemann_client import transport
from six.moves.urllib.parse import urlparse
from watcher_metering.store.base import MetricsStoreClientBase
from watcher_metering.store.base import MetricsStoreError

LOG = log.getLogger(__name__)


class RiemannClient(MetricsStoreClientBase):
    """Riemann client"""

    def __init__(self, store_endpoint, datacenter, default_metric_host,
                 default_metric_ttl, default_metric_state):
        """
        :param store_endpoint: Riemann server endpoint
        :type store_endpoint: str
        :param datacenter: The current datacenter name
        :type datacenter: str
        :param default_metric_host: The default host value used when no other
            host has been provided from the metric resource_metadata.
        :type default_metric_host: str
        :param default_metric_ttl: The amount of time in seconds that events
            sent to Riemann are retained in its index.
        :type default_metric_ttl: int
        :param default_metric_state: The default state value used when no other
            state has been provided from the metric resource_metadata.
        :type default_metric_state: str
        """
        super(RiemannClient, self).__init__()
        self._store_endpoint = store_endpoint
        self.store_uri = urlparse(self.store_endpoint)

        self.default_metric_host = default_metric_host
        self.default_metric_ttl = default_metric_ttl
        self.default_metric_state = default_metric_state
        self.datacenter = datacenter

        self._transport = self._create_transport(self.store_uri.scheme)
        self.client = Client(
            transport=self._transport,
        )

    def _create_transport(self, scheme):
        transport_types = dict(
            tcp=transport.TCPTransport,
            udp=transport.UDPTransport,
        )
        _transport_cls = transport_types[scheme]
        return _transport_cls(
            host=self.store_uri.hostname,
            port=self.store_uri.port
        )

    @classmethod
    def get_name(cls):
        return "riemann"

    @classmethod
    def get_config_opts(cls):
        return super(RiemannClient, cls).get_config_opts() + [
            cfg.StrOpt(
                'store_endpoint',
                help="Complete Riemann endpoint, e.g. tcp://localhost:5555.",
                default=None, required=True),
            cfg.StrOpt(
                'default_metric_host',
                default='openstack',
                help='The default host value used when no other host value is '
                     'determined, such as from the metric resource_metadata.'
            ),
            cfg.IntOpt(
                'default_metric_ttl',
                default=86400,
                help='The default amount of time in seconds that events sent '
                     'to Riemann are retained in its index.'
            ),
            cfg.StrOpt(
                'default_metric_state',
                default='ok',
                help='The default state value used when no other state value '
                     'is determined, such as from the metric '
                     'resource_metadata.'
            ),
            cfg.StrOpt(
                'datacenter',
                required=True,
                help='The current datacenter name',
            ),
        ]

    @property
    def store_endpoint(self):
        return self._store_endpoint

    def connect(self):
        try:
            self._transport.connect()
        except (OSError, RuntimeError) as exc:
            raise MetricsStoreError(exc)
        LOG.info("[Riemann] Client connected")

    def disconnect(self):
        try:
            self._transport.disconnect()
        except (OSError, RuntimeError) as exc:
            raise MetricsStoreError(exc)
        LOG.info("[Riemann] Client disconnected")

    def reconnect(self):
        try:
            LOG.debug("[Riemann] ==> Reconnecting...")
            self.disconnect()
        except MetricsStoreError as exc:
            LOG.exception(exc)
        try:
            self.connect()
        except MetricsStoreError as exc:
            LOG.exception(exc)
            LOG.debug("[Riemann] Socket connection re-established")

    def _send(self, event):
        try:
            self.client.send_event(event)
        except (transport.RiemannError, struct.error,
                OSError, RuntimeError) as exc:
            LOG.warn("Could not deliver the message "
                     "to the Riemann server! Trying again...")
            LOG.exception(exc)
            raise MetricsStoreError("Could not deliver the message "
                                    "to the Riemann server.")
        except TypeError as exc:
            LOG.debug("Message formatting issue with %r",
                      Client.create_dict(event))
            LOG.exception(exc)
            raise MetricsStoreError(
                "Message formatting issue => "
                "%r: '%r'" % (Client.create_dict(event), exc)
            )

    def send(self, metric):
        LOG.debug('Publishing metrics to `%s:%d`',
                  self.store_uri.hostname, self.store_uri.port)

        try:
            event_msg = self.create_event(metric)
        except (MetricsStoreError, KeyError) as exc:
            LOG.exception(exc)
            raise MetricsStoreError(exc)

        for _ in range(2):  # 2 attempts
            try:
                self._send(event_msg)
                break
            except Exception as exc:
                LOG.warn('Unable to send metric `%r`', metric)
                LOG.exception(exc)
                LOG.error("Connection issue --> try again...")
                self.reconnect()

    def create_event(self, metric):
        """Translates a dictionary of event attributes to an Event object

        :param dict metric: The attributes to be set on the event
        :returns: A protocol buffer ``Event`` object
        """
        description = ""  # Needs to be specified if any
        tags = []  # Needs to be specified if any

        metadata = metric.get("resource_metadata", {})
        host = metadata.get("host", self.default_metric_host)
        ttl = metadata.get("ttl", self.default_metric_ttl)
        state = metadata.get("state", self.default_metric_state)

        try:
            timestamp = metric.get("timestamp", "")
            parsed = parser.parse(timestamp)
            epoch_seconds = calendar.timegm(parsed.timetuple())
        except ValueError:
            error_message = "Could not parse the `%r` timestamp! " % timestamp
            LOG.exception(error_message)
            raise MetricsStoreError(error_message)

        event_dict = dict(
            time=epoch_seconds,
            ttl=int(ttl),
            host=host,
            service=metric["name"],
            state=state,
            metric_f=metric["value"],
            description=description,
            tags=tags,
            attributes=self._build_attributes(metric),
        )
        try:
            return self.event_factory(event_dict)
        except TypeError as exc:
            LOG.exception(exc)
            raise MetricsStoreError(exc)

    def event_factory(self, data):
        event = Event()
        event.tags.extend(data.pop('tags', []))

        for key, value in data.pop('attributes', {}).items():
            attribute = event.attributes.add()
            attribute.key, attribute.value = key, value

        for name, value in data.items():
            if value is not None:
                setattr(event, name, value)

        return event

    def _build_attributes(self, metric):
        ignored_metadata = ["host", "ttl"]

        metadata = metric.get("resource_metadata", {})
        attributes = {
            key: val for key, val in metadata.items()
            if key not in ignored_metadata
            }
        attributes["datacenter"] = self.datacenter or ""
        attributes["resource_id"] = metric.get("resource_id", "")
        attributes["unit"] = metric.get("unit", "")

        return attributes
