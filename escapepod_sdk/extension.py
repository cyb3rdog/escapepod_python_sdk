###!/usr/bin/env python3

# Copyright (c) 2021 cyb3rdog
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
Management of the connection to and from Cyb3rVector EscapePod Extension Proxy.
"""

# __all__ should order by constants, event classes, other classes, functions.
__all__ = ['Client', 'AsyncClient']

import time
import functools

from . import intents
from . import events
from . import util

from .messaging import protocol
from .exceptions import EscapePodNotReadyException
from .connection import (Connection, on_connection_thread)


class Client:

    def __init__(self,
                 ip: str = None,
                 port: str = None,                 
                 robot: object = None,
                 keep_alive: int = 60,
                 default_logging: bool = True):

        if default_logging:
            util.setup_basic_logging()
        self.logger = util.get_class_logger(__name__, self)

        self._ip = ip
        self._port = port or "8090"
        self._force_async = False

        if (self._ip is None):
            raise ValueError("The escapepod_sdk.extension.Client object requires Cyb3rVector EscapePod Extension Proxy IP address.")
                             
        #: :class:`escapepod_sdk.connection.Connection`: The active connection to the escapepod extension proxy.
        self._conn = Connection(':'.join([self._ip, self._port]))
        self._events = events.EventHandler(self, robot, keep_alive)

        self._intents: intents.IntentFactory = None


    @property
    def conn(self) -> Connection:
        """A reference to the :class:`~escapepod_sdk.connection.Connection` instance."""
        return self._conn

    @property
    def events(self) -> events.EventHandler:
        """A reference to the :class:`~escapepod_sdk.events.EventHandler` instance."""
        return self._events

    @property
    def force_async(self) -> bool:
        """A flag used to determine if this is a :class:`Client` or :class:`AsyncClient`."""
        return self._force_async

    @property
    def intents(self) -> intents.IntentFactory:
        """A reference to the :class:`~escapepod_sdk.intents.IntentFactory` instance."""
        if self._intents is None:
            raise EscapePodNotReadyException("IntentFactory is not yet initialized")
        return self._intents


    @on_connection_thread()
    async def get_status(self) -> protocol.StatusResponse:
        """Returns the state of subsription to EscapePod Intents and Extension Proxy version
        """
        get_status_request = protocol.StatusRequest()
        return await self.conn.grpc_interface.GetStatus(get_status_request)


    def connect(self, timeout: int = 10) -> None:
        """Start the connection to EscapePod Proxy.

        .. testcode::

            import escapepod_sdk

            client = escapepod_sdk.extension.Client()
            client....
            client.disconnect()

        :param timeout: The time to allow for a connection before a
            :class:`escapepod_sdk.exceptions.EscapePodTimeoutException` is raised.
        """
        self.conn.connect(timeout=timeout)
        self.events.start(self.conn)

        self.logger.info(f"Successfully connected to Cyb3rVector EscapePod extension proxy (version: {self.get_status().Version})")

        self._intents = intents.IntentFactory(self)

    def disconnect(self) -> None:
        """Close the connection with EscapePod Extension Proxy.

        .. testcode::

            import escapepod_sdk

            client = escapepod_sdk.extension.Client()
            client....
            client.disconnect()
        """

        self.events.close()
        self.conn.close()

    def wait_for_eventstream(self):
        """Blocks the main thread until the event stream is subscribed to escapepod extension proxy event stream.
        """
        while not self.events.subscribed:
            time.sleep(0.1)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class AsyncClient(Client):
    """The AsyncClient object is just like the Client object, but allows multiple commands
    to be executed at the same time. To achieve this, all grpc function calls also
    return a :class:`concurrent.futures.Future`.
    """

    @functools.wraps(Client.__init__)
    def __init__(self, *args, **kwargs):
        super(AsyncClient, self).__init__(*args, **kwargs)
        self._force_async = True

