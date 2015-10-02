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

from oslo_config import cfg
from oslo_log import log
from watcher_metering.publisher.opts import register_publisher_opts
from watcher_metering.publisher.publisher import Publisher
from watcher_metering import version

LOG = log.getLogger(__name__)


def load_config(conf):
    log.register_options(conf)
    register_publisher_opts(conf)

    conf(
        version=version.version_info.release_string(),
        project='watcher_metering'
    )
    return conf


def start_publisher():
    conf = load_config(cfg.CONF)
    log.set_defaults()
    log.setup(conf, "watcher_metering")

    publisher_server = Publisher(**conf.publisher)
    publisher_server.start()

    publisher_server.join()


if __name__ == '__main__':
    start_publisher()  # pragma: no cover
