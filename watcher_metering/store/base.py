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

import six
from watcher_metering.load.loadable import Loadable
from watcher_metering.store.loader import StoreClientLoader


@six.add_metaclass(abc.ABCMeta)
class MetricsStoreClientBase(Loadable):
    """
    Generic abstract class defining the contract to publish to a metrics store
    (i.e. Riemann, Ceilometer, ...)
    """

    @classmethod
    def namespace(cls):
        """
        :return: The namespace of the loadable ("" if default group)
        :rtype: str
        """
        return StoreClientLoader.namespace

    @classmethod
    def get_base_opts(cls):
        return []

    @classmethod
    def get_config_opts(cls):
        """Should return the list of options relative to this store client"""
        return cls.get_base_opts()

    @classmethod
    def get_external_opts_configs(cls):
        return []

    @property
    @abc.abstractmethod
    def store_endpoint(self):
        raise NotImplementedError  # pragma: nocover

    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError  # pragma: nocover

    @abc.abstractmethod
    def disconnect(self):
        raise NotImplementedError  # pragma: nocover

    @abc.abstractmethod
    def send(self, metric):
        raise NotImplementedError  # pragma: nocover


class MetricsStoreError(Exception):
    pass
