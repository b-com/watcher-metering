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

from watcher_metering.load.loader import DriverLoader


class MetricsDriverLoader(DriverLoader):

    namespace = "watcher_metering.drivers"

    def __init__(self, conf, driver_name):
        super(MetricsDriverLoader, self).__init__(
            conf=conf,
            namespace=self.namespace,
            name=driver_name,
        )
