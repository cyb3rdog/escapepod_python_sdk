# Copyright (c) 2021 cyb3rdog
# Based on Anki Vector Python SDK
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
Event handler used to make functions subscribe to escapepod proxy events.
"""

__all__ = ['EventHandler', 'Events']

import asyncio
from google.protobuf.text_format import MessageToString
from concurrent.futures import CancelledError
from enum import Enum
import threading
from typing import Callable
import uuid

from .connection import Connection
from .messaging import protocol
from .messages import keep_alive, subscribed, process_intent
from . import util

class Events(Enum):
    """List of available events."""

    # EscapePod Extension Proxy Events
    subscribed = "Subscribed"           # : Event containing the subscription session guid.
    unsubscribed= "UnSubscribed"        # : Event triggered when Client unsubscribes from escapepod extension proxy.
    keep_alive = "KeepAlive"            # : Event triggered when a keep_alive message is sent from escape pod to client
    process_intent = "ProcessIntent"    # : Event triggered when a vector hears an intent registered on escapepod


class _EventCallback:
    def __init__(self, callback, *args, _on_connection_thread: bool = False, **kwargs):
        self._extra_args = args
        self._extra_kwargs = kwargs
        self._callback = callback
        self._on_connection_thread = _on_connection_thread

    @property
    def on_connection_thread(self):
        return self._on_connection_thread

    @property
    def callback(self):
        return self._callback

    @property
    def extra_args(self):
        return self._extra_args

    @property
    def extra_kwargs(self):
        return self._extra_kwargs

    def __eq__(self, other):
        other_cb = other
        if hasattr(other, "callback"):
            other_cb = other.callback
        return other_cb == self.callback

    def __hash__(self):
        return self._callback.__hash__()


class EventHandler:
    """Listen for EscapePod extension proxy events."""

    def __init__(self, client, robot, keep_alive):
        self.logger = util.get_class_logger(__name__, self)
        self._client = client
        self._robot = robot
        self._conn = None
        self._conn_id = None
        self._keepalive = keep_alive
        self._subscriber_uuid = None
        self.listening_for_events = False
        self.event_future = None
        self._thread: threading.Thread = None
        self._loop: asyncio.BaseEventLoop = None
        self.subscribers = {}
        self._done_signal: asyncio.Event = None

    @property
    def subscribed(self) -> bool:
        """A property to determine whether the event stream is subscribed to escapepod extension proxy."""
        return not self._subscriber_uuid == None

    def start(self, connection: Connection):
        """Start listening for events. Automatically called by the :class:`escapepod_sdk.extension.Client` class.

        :param connection: A reference to the connection from the SDK to the escapepod.
        :param loop: The loop to run the event task on.
        """
        self._conn = connection
        self.listening_for_events = True
        self._thread = threading.Thread(target=self._run_thread, daemon=True, name="Event Stream Handler Thread")
        self._thread.start()

    def _run_thread(self):
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._done_signal = asyncio.Event(loop=self._loop)
            # create an event stream handler on the connection thread
            self.event_future = asyncio.run_coroutine_threadsafe(self._handle_event_stream(), self._conn.loop)

            async def wait_until_done():
                return await self._done_signal.wait()
            self._loop.run_until_complete(wait_until_done())
        finally:
            self._loop.close()

    def close(self):
        """Stop listening for events. Automatically called by the :class:`escapepod_sdk.extension.Client` class."""
        self.listening_for_events = False
        try:
            self._handle_stream_closing()
            if self.event_future:
                self.event_future.cancel()
                self.event_future.result()
        except CancelledError:
            pass

        try:
            #self._loop.call_soon_threadsafe(self._done_signal.set)
            if self._thread:
                self._thread.join(timeout=5)
            self._thread = None
        except CancelledError:
            pass


    def _notify(self, event_callback, event_name, event_data):
        loop = self._loop
        thread = self._thread
        # For high priority events that shouldn't be blocked by user callbacks
        # they will run directly on the connection thread. This should typically
        # be used when setting robot properties from events.
        if event_callback.on_connection_thread:
            loop = self._conn.loop
            thread = self._conn.thread

        callback = event_callback.callback
        args = event_callback.extra_args
        kwargs = event_callback.extra_kwargs

        if asyncio.iscoroutinefunction(callback):
            callback = callback(self._robot, event_name, event_data, *args, **kwargs)
        elif not asyncio.iscoroutine(callback):
            async def call_async(fn, *args, **kwargs):
                fn(*args, **kwargs)
            callback = call_async(callback, self._robot, event_name, event_data, *args, **kwargs)

        if threading.current_thread() is thread:
            future = asyncio.ensure_future(callback, loop=loop)
        else:
            future = asyncio.run_coroutine_threadsafe(callback, loop=loop)
        future.add_done_callback(self._done_callback)

    def _done_callback(self, completed_future):
        exc = completed_future.exception()
        if exc:
            self.logger.error("Event callback exception: %s", exc)
            if isinstance(exc, TypeError) and "positional arguments but" in str(exc):
                self.logger.error("The subscribed function may be missing parameters in its definition. Make sure it has robot, event_type and event positional parameters.")

    async def dispatch_event_by_name(self, event_data, event_name: str):
        """Dispatches event to event listeners by name.

        .. testcode::

            import escapepod_sdk

            def event_listener(none, name, msg):
                print(name) # will print 'my_custom_event'
                print(msg) # will print 'my_custom_event dispatched'

            with escapepod_sdk.extension.Client() as client:
                client.events.subscribe_by_name(event_listener, event_name='my_custom_event')
                client.conn.run_coroutine(client.events.dispatch_event_by_name('my_custom_event dispatched', event_name='my_custom_event'))

        :param event_data: Data to accompany the event.
        :param event_name: The name of the event that will result in func being called.
        """
        if not event_name:
            self.logger.error('Bad event_name in dispatch_event.')

        if event_name in self.subscribers.keys():
            subscribers = self.subscribers[event_name].copy()
            for callback in subscribers:
                self._notify(callback, event_name, event_data)

    async def dispatch_event(self, event_data, event_type: Events):
        """Dispatches event to event listeners."""
        if not event_type:
            self.logger.error('Bad event_type in dispatch_event.')

        event_name = event_type.value
        await self.dispatch_event_by_name(event_data, event_name)

    def _unpack_event(self, response):
        event_name = protocol.MessageType.Name(response.message_type)
        event_data = response.message_data
        
        if event_name == 'KeepAlive':
            event_data = keep_alive(response)
        if event_name == "ProcessIntent":
            event_data = process_intent(response)

        return event_name, event_data

    async def _handle_event_stream(self):
        self._conn_id = bytes(uuid.uuid4().hex, "utf-8")
        try:
            req = protocol.SubscribeRequest(keep_alive=self._keepalive)
            async for response in self._conn.grpc_interface.Subscribe(req):
                if not self.listening_for_events:
                    break
                try:
                    self.logger.debug(f"ProxyMessage {MessageToString(response, as_one_line=True)}")
                    if response.message_type == protocol.Subscribed:
                        self._subscriber_uuid = subscribed(response).uuid
                        self.logger.info("Successfully subscribed to Cyb3rVector EscapePod Extension event stream")
                    elif response.message_type == protocol.Unsubscribed:
                        self._subscriber_uuid = None
                        self.logger.info(f"Successfully unsubscribed from Cyb3rVector EscapePod extension event stream")

                    event_name, event_data = self._unpack_event(response)
                    await self.dispatch_event_by_name(event_data, event_name)
                except TypeError:
                    self.logger.warning('Unknown Event type')
        except CancelledError:
            self.logger.info('Disconnecting from Cyb3rVector EscapePod Extension event stream.')
        except Exception as e:
            print(e)

    def _handle_stream_closing(self):
        if self.subscribed:
            request = protocol.UnsubscribeRequest(uuid=self._subscriber_uuid)
            self._conn.run_coroutine(self._conn.grpc_interface.UnSubscribe(request))
            self._subscriber_uuid = None

    def subscribe_by_name(self, func: Callable, event_name: str, *args, **kwargs):
        """Receive a method call when the specified event occurs.

        .. testcode::

            import escapepod_sdk

            def event_listener(none, name, msg):
                print(name) # will print 'my_custom_event'
                print(msg) # will print 'my_custom_event dispatched'

            with escapepod_sdk.extension.Client() as client:
                client.events.subscribe_by_name(event_listener, event_name='my_custom_event')
                client.conn.run_coroutine(client.events.dispatch_event_by_name('my_custom_event dispatched', event_name='my_custom_event'))

        :param func: A method implemented in your code that will be called when the event is fired.
        :param event_name: The name of the event that will result in func being called.
        :param args: Additional positional arguments to this function will be passed through to the callback in the provided order.
        :param kwargs: Additional keyword arguments to this function will be passed through to the callback.
        """
        if not event_name:
            self.logger.error('Bad event_name in subscribe.')

        if event_name not in self.subscribers.keys():
            self.subscribers[event_name] = set()
        self.subscribers[event_name].add(_EventCallback(func, *args, **kwargs))

    def subscribe(self, func: Callable, event_type: Events, *args, **kwargs):
        """Receive a method call when the specified event occurs.

        :param func: A method implemented in your code that will be called when the event is fired.
        :param event_type: The enum type of the event that will result in func being called.
        :param args: Additional positional arguments to this function will be passed through to the callback in the provided order.
        :param kwargs: Additional keyword arguments to this function will be passed through to the callback.
        """
        if not event_type:
            self.logger.error('Bad event_type in subscribe.')

        event_name = event_type.value

        self.subscribe_by_name(func, event_name, *args, **kwargs)

    def unsubscribe_by_name(self, func: Callable, event_name: str):
        """Unregister a previously subscribed method from an event.

        .. testcode::

            import escapepod_sdk

            def event_listener(none, name, msg):
                print(name) # will print 'my_custom_event'
                print(msg) # will print 'my_custom_event dispatched'

            with escapepod_sdk.extension.Client() as client:
                client.events.subscribe_by_name(event_listener, event_name='my_custom_event')
                client.conn.run_coroutine(client.events.dispatch_event_by_name('my_custom_event dispatched', event_name='my_custom_event'))

        :param func: The method you no longer wish to be called when an event fires.
        :param event_name: The name of the event for which you no longer want to receive a method call.
        """
        if not event_name:
            self.logger.error('Bad event_key in unsubscribe.')

        if event_name in self.subscribers.keys():
            event_subscribers = self.subscribers[event_name]
            if func in event_subscribers:
                event_subscribers.remove(func)
                if not event_subscribers:
                    self.subscribers.pop(event_name, None)
            else:
                self.logger.error(f"The function '{func.__name__}' is not subscribed to '{event_name}'")
        else:
            self.logger.error(f"Cannot unsubscribe from event_type '{event_name}'. "
                              "It has no subscribers.")

    def unsubscribe(self, func: Callable, event_type: Events):
        """Unregister a previously subscribed method from an event.

        :param func: The enum type of the event you no longer wish to be called when an event fires.
        :param event_type: The name of the event for which you no longer want to receive a method call.
        """
        if not event_type:
            self.logger.error('Bad event_type in unsubscribe.')

        event_name = event_type.value

        self.unsubscribe_by_name(func, event_name)
