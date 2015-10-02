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

from stevedore.driver import DriverManager


class DriverLoader(object):
    """Utility base class which allows you to Load an entry point whilst
    validating and injecting its related configuration options.

    Setup
    =====

    Codewise
    --------

    from oslo_config import cfg
    from [...] import Loadable

    class Sample(Loadable):
        @classmethod
        def get_config_opts(cls):
            return [cfg.StrOpt('my_opt1')]
        [...]


    In the setup.cfg file
    ---------------------

    [entry_points]
    sample = my.import.path:Sample

    In your config file (NS being a given namespace)
    ------------------------------------------------

    [NS.sample]
    my_opt1= value1
    ...

    Result
    ------

    By calling:
    >>> loader = DriverLoader(conf=cfg.CONF, namespace='NS', name='sample')
    >>> sample_instance = loader.load()

    You get a `sample_instance` of type `Sample` as if instantiated like this:
    >>> sample_instance = Sample(my_opt1='value1')

    """

    def __init__(self, conf, namespace, name):
        """
        :param conf: Configuration obtained from a configuration file
        :type conf: oslo_config.cfg.ConfigOpts instance
        :param namespace: Namespace of the loadable entry point
        :type namespace: str
        :param name: Name of the loadable entry point
        :type name: str
        """
        self.conf = conf
        self.namespace = namespace
        self.name = name  # loadable entrypoint name

    def load(self):
        driver_manager = DriverManager(
            namespace=self.namespace,
            name=self.name,
            invoke_on_load=False,
        )
        store_client_driver = driver_manager.driver

        internal_options = self._load_internal_config(store_client_driver)
        external_options = self._load_external_config(store_client_driver)

        opts = {}
        opts.update(external_options)
        opts.update(internal_options)

        client = store_client_driver(**opts)

        return client

    def _reload_config(self):
        self.conf()

    def _load_internal_config(self, driver_cls):
        internal_options = {}
        config_opts = driver_cls.get_config_opts()

        if not config_opts:
            return internal_options

        group_name = driver_cls.get_entry_name()
        self.conf.register_opts(config_opts, group=group_name)

        # Finalise the opt import by re-checking the configuration
        # against the provided config files
        self._reload_config()

        internal_options_group = self.conf.get(group_name)
        if not internal_options_group:
            raise LoadingError("Missing/Invalid driver configuration")

        internal_options.update({
            name: value for name, value in internal_options_group.items()
        })

        return internal_options

    def _load_external_config(self, driver_cls):
        for external_opt_config in driver_cls.get_external_opts_configs():
            self.conf.import_opt(
                name=external_opt_config.name,
                module_str=external_opt_config.module_str,
                group=external_opt_config.group,
            )

        # Finalise the opt import by re-checking the configuration
        # against the provided config files
        self._reload_config()

        external_options = {}
        for external_opt_config in driver_cls.get_external_opts_configs():
            if not external_opt_config.group:
                opt_name = external_opt_config.name
                opt = self.conf.get(external_opt_config.name)
            else:
                _opt_group = self.conf.get(external_opt_config.group)
                opt_name = "%s__%s" % (external_opt_config.group,
                                       external_opt_config.name)
                opt = _opt_group.get(external_opt_config.name)

            external_options[opt_name] = opt

        return external_options


class LoadingError(Exception):
    pass
