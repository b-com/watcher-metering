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

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from stevedore.extension import ExtensionManager
from watcher_metering.version import version_info


class StoreDriversDoc(Directive):

    def add_line(self, line, *lineno):
        """Append one line of generated reST to the output."""
        self.result.append(line, directives.unchanged, *lineno)

    def run(self):
        self.result = ViewList()

        ext_manager = ExtensionManager(namespace='metrics_store')

        for extension in ext_manager.extensions:
            driver_class = extension.plugin
            self.add_extension(driver_class)

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
        return node.children

    def add_extension(self, driver_class):
        self.add_line('.. automodule:: %s' % driver_class.__module__)
        self.add_line('\n')
        self.add_line('.. autoclass:: %s' % driver_class.__name__)
        self.add_line('    :members:')
        self.add_line('\n')
        self.add_line('    .. autoattribute::')
        self.add_line('\n')


def setup(app):
    app.add_directive('store-doc', StoreDriversDoc)

    return {'version': version_info.version_string()}
