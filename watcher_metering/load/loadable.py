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


@six.add_metaclass(abc.ABCMeta)
class Loadable(object):
    """Generic interface for dynamically loading a driver/entry point.
    This defines the contract in order to let the loader manager inject
    the configuration parameters during the loading.
    Note: Should be used alongside the DriverLoader to make it work.
    """

    @classmethod
    @abc.abstractmethod
    def namespace(cls):
        """
        :return: The namespace of the loadable ("" if default group)
        :rtype: str
        """
        return NotImplementedError  # pragma: nocover

    @classmethod
    def get_entry_name(cls):
        """
        :return: The entry point name given in the setup file
        :rtype: str
        """
        return ".".join([cls.namespace(), cls.get_name()])

    @classmethod
    @abc.abstractmethod
    def get_name(cls):
        """Name to identify the loadable within the config file.
        Will be prefixed by a group name (namespacing) to avoid any section
        name clash.
        IMPORTANT: this is class method, overload it with @classmethod !

        :return: loadable name (should be unique)
        :rtype: str
        """
        return "base"  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def get_config_opts(cls):
        """
        :return: A list of configuration options relative to this Loadable
        :rtype: list of :class:`oslo_config.cfg.Opt` instances
        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    @abc.abstractmethod
    def get_external_opts_configs(cls):
        """
        :return:
            A list of external import config instances ready to be
            used by the loader manager
        :rtype: A list of :class:`ExternalOptConfig` instances
        """
        raise NotImplementedError  # pragma: nocover


class ExternalOptConfig(object):
    """
    Configuration needed to import a configuration option from an external
    package.

    :param name: The name of the configuration option
    :type name: str
    :param module_str: The import path of the configuration option
    :type module_str: str
    :param group: The group of the configuration option
    :type group: str
    """

    def __init__(self, name, module_str, group):
        self.name = name
        self.module_str = module_str
        self.group = group
