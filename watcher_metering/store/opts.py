# -*- encoding: utf-8 -*-
# Copyright 2014
# The Cloudscaling Group, Inc.
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

from oslo_config import cfg
from watcher_metering.store.ceilometer import CeilometerClient
from watcher_metering.store.riemann import RiemannClient


STORES = (
    RiemannClient,
    CeilometerClient,
)


def _get_external_opts(cls):
    ext_opts = []
    for opt in cls.get_external_opts_configs():
        __import__(opt.module_str)
        opt_group = cfg.CONF.get(opt.group)._group
        config_opt = opt_group._opts[opt.name]['opt']
        ext_opts.append((opt.group, [config_opt]))

    return ext_opts


def list_opts():
    opts = []

    for store_cls in STORES:
        _internal_opts = [
            store_cls.get_entry_name(),
            store_cls.get_config_opts(),
        ]

        _external_opts = _get_external_opts(store_cls)
        opts.append(_internal_opts)
        opts.extend(_external_opts)

    return opts
