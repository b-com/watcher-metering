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

from __future__ import unicode_literals

from oslo_config import cfg


PUBLISHER_OPTS = (
    cfg.StrOpt(
        'metrics_store',
        default="riemann",
        required=True,
        help='The name of the store backend to which the metrics will be '
             'sent over (riemann or ceilometer).',
    ),
    cfg.BoolOpt(
        'use_nanoconfig_service',
        default=False,
        required=True,
        help='Whether it should configure the socket using nanoconfig '
             'or itself.',
    ),
    cfg.StrOpt(
        'nanoconfig_profile',
        default="nanoconfig://watcher-metering-publisher",
        required=False,
        help='Profile name to be requested to the nanoconfig service. '
             'Should always take the form: nanoconfig://{PROFILE_NAME}',
    ),
    cfg.StrOpt(
        'nanoconfig_service_endpoint',
        default=None,  # Extracts it from the environment variable by default
        required=False,
        help='Nanoconfig service endpoint URI. By default, extracted from the '
             '"NN_CONFIG_SERVICE" environment variable',
    ),
    cfg.StrOpt(
        'nanoconfig_update_endpoint',  # see NN_CONFIG_UPDATES
        default=None,  # Extracts it from the environment variable by default
        required=False,
        help='Nanoconfig update service endpoint URI. By default, extracted '
             'from the "NN_CONFIG_UPDATES" environment variable',
    ),
    cfg.StrOpt(
        'publisher_endpoint',
        default="tcp://0.0.0.0:12345",
        required=False,
        help='Publisher endpoint URI which is used to pull the data '
             'from the agents. Only used when the `use_nanoconfig_service` '
             'option is not activated',
    ),
    cfg.IntOpt(
        'max_queue_size',
        default=8,
        required=True,
        help='Maximum size of the metric queue',
    ),
    cfg.IntOpt(
        'max_worker',
        default=8,
        required=True,
        help='Maximum size for the worker pool',
    ),
    cfg.IntOpt(
        'min_worker',
        default=2,
        required=True,
        help='Minimum size for the worker pool',
    ),
)

PUBLISHER_GROUP_NAME = "publisher"


def register_publisher_opts(conf):
    conf.register_opts(PUBLISHER_OPTS, group=PUBLISHER_GROUP_NAME)


def list_opts():
    return [
        (PUBLISHER_GROUP_NAME, PUBLISHER_OPTS),
    ]
