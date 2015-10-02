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

from oslo_log import log

LOG = log.getLogger(__name__)


class Observable(object):

    def __init__(self):
        super(Observable, self).__init__()
        self._observers = []

    def register_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister_observer(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            LOG.warning("Observer `%r` was not registered against "
                        "this observable `%r`", observer, self)

    def notify(self, data=None, modifier=None):
        for observer in self._observers:
            if modifier != observer:
                observer.update(self, data)
