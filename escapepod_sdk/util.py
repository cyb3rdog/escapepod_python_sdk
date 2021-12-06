# Copyright (c) 2018 Anki, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utility functions and classes for the EscapePod Extension SDK.
"""

# __all__ should order by constants, event classes, other classes, functions.
__all__ = ['get_class_logger',
           'setup_basic_logging']

import logging
import os


def setup_basic_logging(custom_handler: logging.Handler = None,
                        general_log_level: str = None,
                        target: object = None):
    """Helper to perform basic setup of the Python logger.

    :param custom_handler: provide an external logger for custom logging locations
    :param general_log_level: 'DEBUG', 'INFO', 'WARN', 'ERROR' or an equivalent
            constant from the :mod:`logging` module. If None then a
            value will be read from the SDK_LOG_LEVEL environment variable.
    :param target: The stream to send the log data to; defaults to stderr
    """
    if general_log_level is None:
        general_log_level = os.environ.get('SDK_LOG_LEVEL', logging.INFO)

    handler = custom_handler
    if handler is None:
        handler = logging.StreamHandler(stream=target)
        formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(name)+25s %(levelname)+7s  %(message)s",
                                      "%H:%M:%S")
        handler.setFormatter(formatter)

        class LogCleanup(logging.Filter):  # pylint: disable=too-few-public-methods
            def filter(self, record):
                # Drop 'escapepod_sdk' from log messages
                record.name = '.'.join(record.name.split('.')[1:])
                # Indent past informational chunk
                record.msg = record.msg.replace("\n", f"\n{'':48}")
                return True
        handler.addFilter(LogCleanup())

    logger = logging.getLogger('escapepod_sdk')
    if not logger.handlers:
        logger.addHandler(handler)
        logger.setLevel(general_log_level)


def get_class_logger(module: str, obj: object) -> logging.Logger:
    """Helper to create logger for a given class (and module).

    .. testcode::

        import escapepod_sdk

        logger = escapepod_sdk.util.get_class_logger("module_name", "object_name")

    :param module: The name of the module to which the object belongs.
    :param obj: the object that owns the logger.
    """
    return logging.getLogger(".".join([module, type(obj).__name__]))


class Component:
    """ Base class for all components."""

    def __init__(self, client):
        self.logger = get_class_logger(__name__, self)
        self._client = client

    @property
    def client(self):
        return self._client

    @property
    def conn(self):
        return self._client.conn

    @property
    def force_async(self):
        return self._client.force_async

    @property
    def grpc_interface(self):
        """A direct reference to the connected aiogrpc interface.
        """
        return self._client.conn.grpc_interface
