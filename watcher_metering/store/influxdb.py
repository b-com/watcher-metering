# -*- encoding: utf-8 -*-
# Copyright (c) 2015 b<>com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import unicode_literals

from influxdb import InfluxDBClient

from oslo_config import cfg
from oslo_log import log

from watcher_metering.store.base import MetricsStoreClientBase
from watcher_metering.store.base import MetricsStoreError

LOG = log.getLogger(__name__)


class InfluxClient(MetricsStoreClientBase):
    """InfluxDBClient client"""

    def __init__(self, default_host, default_port, default_database,
                 default_username, default_password, create_database):
        """
        :param default_host: InfluxDB host
        :type default_host: str
        :param default_port: InfluxDB port
        :type default_port: int
        :param default_database: The name of the default database.
        :type default_database: str
        :param default_username: User to connect to InfluxDB.
        :type default_username: str
        :param default_password: The password of the user.
        :type default_password: str
        :param create_database: If true, the database is created.
        :type create_database: bool
        """
        super(InfluxClient, self).__init__()

        self.default_host = default_host
        self.default_port = default_port
        self.default_database = default_database
        self.default_username = default_username
        self.default_password = default_password
        self.create_database = create_database

        self._client = InfluxDBClient(
            host=self.default_host,
            port=self.default_port,
            username=self.default_username,
            password=self.default_password,
            database=self.default_database
        )

        try:
            if create_database and self._is_need_to_create_database:
                self._client.create_database(self.default_database)
        except Exception as exc:
            LOG.warn('Unable to create database %s' % self.default_database)
            LOG.exception(exc)

    @property
    def _is_need_to_create_database(self):
        database = list(filter(lambda database:
                               database['name'] == self.default_database,
                               self._client.get_list_database()))
        return not database

    @classmethod
    def get_name(cls):
        return "influxdb"

    @classmethod
    def get_config_opts(cls):
        return super(InfluxClient, cls).get_config_opts() + [
            cfg.StrOpt(
                'default_host',
                help="InfluxDB host, e.g. localhost.",
                default="localhost", required=True),
            cfg.IntOpt(
                'default_port',
                default=8086,
                help='InfluxDB port, e.g. 8086', required=True,
            ),
            cfg.StrOpt(
                'default_database',
                default="my_data", required=True,
                help='The default database where data are stored.'
            ),
            cfg.StrOpt(
                'default_username',
                default="root", required=True,
                help='user to connect to InfluxDB.'
            ),
            cfg.StrOpt(
                'default_password',
                default="root", required=True,
                help='The password of the user',
            ),
            cfg.BoolOpt(
                'create_database',
                default=False, required=False,
                help='Create database on startup',
            ),
        ]

    @property
    def store_endpoint(self):
        return self._client

    def connect(self):
        LOG.info("[InfluxDB] Client connected")

    def disconnect(self):
        LOG.info("[InfluxDB] Client disconnected")

    def _send(self, point):
        try:
            self.store_endpoint.write_points([point])
        except Exception as exc:
            raise MetricsStoreError(
                "Message formatting issue => "
                "%r: '%r'" % (point, exc)
            )

    def send(self, metric):
        LOG.debug('Publishing metrics to `%s:%d`',
                  self.default_host, self.default_port)

        try:
            point = self.create_point(metric)
        except (MetricsStoreError, KeyError) as exc:
            LOG.exception(exc)
            raise MetricsStoreError(exc)

        for _ in range(2):  # 2 attempts
            try:
                self._send(point)
                break
            except Exception as exc:
                LOG.warn('Unable to send metric `%r`', point)
                LOG.exception(exc)

    def create_point(self, metric):
        """Translates a dictionary of event attributes to an JSON Point object

        :param dict metric: The attributes to be set on the point
        :returns: A json object which represent a point to store
        """

        try:
            if not isinstance(metric, dict):
                raise MetricsStoreError("Invalid dictionary")

            mandatory_fields = ("name", "unit", "type", "value",
                                "resource_id", "host", "timestamp")

            if not set(mandatory_fields).issubset(metric.keys()):
                raise MetricsStoreError("Missing mandatory fields")

            measurement = metric.get('name')
            time = metric.get('timestamp')
            value = metric.get('value')
            tags = self._build_tags(metric)
            point = {
                "measurement": measurement,
                "tags": tags,
                "time": time,
                "fields": {
                    "value": value
                }
            }
            return point

        except TypeError as exc:
            LOG.exception(exc)
            raise MetricsStoreError(exc)

    def _build_tags(self, metric):
        tags = {
            'counter_name': metric['name'],
            'counter_unit': metric['unit'],
            'counter_type': metric['type'],
            'counter_volume': metric['value'],
            'host': metric['host'],
            'resource_id': metric['resource_id']
        }
        return tags
