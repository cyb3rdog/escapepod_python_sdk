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
Management of the connection to and from EscapePod Extension Proxy.
"""

# __all__ should order by constants, event classes, other classes, functions.
__all__ = ['Connection']

import asyncio
import aiogrpc
import functools
import inspect
import logging
import grpc
import sys
import threading

from concurrent import futures
from typing import Any, Awaitable, Callable, Coroutine, Dict, List
from google.protobuf.text_format import MessageToString

from . import util

from .exceptions import (connection_error,
                         EscapePodAsyncException,
                         EscapePodNotFoundException)

from .messaging import client, protocol
from .version import __version__


class Connection:
    """Creates and maintains a aiogrpc connection including managing the connection thread.
    The connection thread decouples the actual messaging layer from the user's main thread,
    and requires any network requests to be ran using :func:`asyncio.run_coroutine_threadsafe`
    to make them run on the other thread. Connection provides two helper functions for running
    a function on the connection thread: :func:`~Connection.run_coroutine` and
    :func:`~Connection.run_soon`.

    This class may be used to bypass the structures of the python sdk handled by
    :class:`~escapepod_sdk.extension.Client`, and instead talk to aiogrpc more directly.

    :param host: The IP address and port of Vector in the format "XX.XX.XX.XX:8090".
    """

    def __init__(self, host: str):
        self._loop: asyncio.BaseEventLoop = None
        self._host = host
        self._interface = None
        self._channel = None
        self._logger = util.get_class_logger(__name__, self)
        self._thread: threading.Thread = None
        self._ready_signal: threading.Event = threading.Event()
        self._done_signal: asyncio.Event = None
        self._conn_exception = False
        self.active_commands = []

    @property
    def loop(self) -> asyncio.BaseEventLoop:
        """A direct reference to the loop on the connection thread.
        Can be used to run functions in on thread.

        .. testcode::

            import escapepod_sdk
            import asyncio

            async def connection_function():
                print("I'm running in the connection thread event loop.")

            with escapepod_sdk.extension.Client() as client:
                asyncio.run_coroutine_threadsafe(connection_function(), client.conn.loop)

        :returns: The loop running inside the connection thread
        """
        if self._loop is None:
            raise EscapePodAsyncException("Attempted to access the connection loop before it was ready")
        return self._loop

    @property
    def thread(self) -> threading.Thread:
        """A direct reference to the connection thread. Available to callers to determine if the
        current thread is the connection thread.

        .. testcode::

            import escapepod_sdk
            import threading

            with escapepod_sdk.extension.Client() as client:
                if threading.current_thread() is client.conn.thread:
                    print("This code is running on the connection thread")
                else:
                    print("This code is not running on the connection thread")

        :returns: The connection thread where all of the grpc messages are being processed.
        """
        if self._thread is None:
            raise EscapePodAsyncException("Attempted to access the connection loop before it was ready")
        return self._thread

    @property
    def grpc_interface(self) -> client.CyberVectorProxyServiceStub:
        """A direct reference to the connected aiogrpc interface.

        This may be used to directly call grpc messages bypassing :class:`extension.Client`

        .. code-block:: python

            import escapepod_sdk

            # Connect to your Vector
            conn = escapepod_sdk.connection.Connection("XX.XX.XX.XX:8090")
            conn.connect()
            # Run your commands
            # ...
            # Close the connection
            conn.close()
        """
        return self._interface


    def connect(self, timeout: float = 10.0) -> None:
        """Connect to Vector. This will start the connection thread which handles all messages
        between Vector and Python.

        .. code-block:: python

            import escapepod_sdk

            # Connect to your Vector
            conn = escapepod_sdk.connection.Connection("XX.XX.XX.XX:8090")
            conn.connect()
            # Run your commands
            # ...
            # Close the connection
            conn.close()

        :param timeout: The time allotted to attempt a connection, in seconds.
        """
        if self._thread:
            raise EscapePodAsyncException("\n\nRepeated connections made to open Connection.")
        self._ready_signal.clear()
        self._thread = threading.Thread(target=self._connect, args=(timeout,), daemon=True, name="gRPC Connection Handler Thread")
        self._thread.start()
        ready = self._ready_signal.wait(timeout=4 * timeout)
        if not ready:
            raise EscapePodNotFoundException()
        if hasattr(self._ready_signal, "exception"):
            e = getattr(self._ready_signal, "exception")
            delattr(self._ready_signal, "exception")
            raise e

    def _connect(self, timeout: float) -> None:
        """The function that runs on the connection thread. This will connect to EscapePod Extension Proxy,
        and establish the BehaviorControl stream.
        """
        try:
            if threading.main_thread() is threading.current_thread():
                raise EscapePodAsyncException("\n\nConnection._connect must be run outside of the main thread.")
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._done_signal = asyncio.Event()

            self._logger.info(f"Connecting to Cyb3rVector EscapePod extension proxy at {self._host}")
            self._channel = aiogrpc.insecure_channel(self._host)

            # Verify the connection to EscapePod Extension Proxy is able to be established (client-side)
            try:
                # Explicitly grab _channel._channel to test the underlying grpc channel directly
                grpc.channel_ready_future(self._channel._channel).result(timeout=timeout)  # pylint: disable=protected-access
            except grpc.FutureTimeoutError as e:
                raise EscapePodNotFoundException() from e

            self._interface = client.CyberVectorProxyServiceStub(self._channel)            

        except grpc.RpcError as rpc_error:  # pylint: disable=broad-except
            setattr(self._ready_signal, "exception", connection_error(rpc_error))
            self._loop.close()
            return
        except Exception as e:  # pylint: disable=broad-except
            # Propagate the errors to the calling thread
            setattr(self._ready_signal, "exception", e)
            self._loop.close()
            return
        finally:
            self._ready_signal.set()

        try:
            async def wait_until_done():
                return await self._done_signal.wait()
            self._loop.run_until_complete(wait_until_done())
        finally:
            self._loop.close()

    def _cancel_active(self):
        for fut in self.active_commands:
            if not fut.done():
                fut.cancel()
        self.active_commands = []

    def close(self):
        """Cleanup the connection, and shutdown all the event handlers.
        Usually this should be invoked by the Client class when it closes.
        """
        try:
            if self._channel:
                self.run_coroutine(self._channel.close()).result()
            self.run_coroutine(self._done_signal.set)
            self._thread.join(timeout=5)
        except:
            pass
        finally:
            self._thread = None

    def run_soon(self, coro: Awaitable) -> None:
        """Schedules the given awaitable to run on the event loop for the connection thread.

        .. testcode::

            import escapepod_sdk
            import time

            async def my_coroutine():
                print("Running on the connection thread")

            with escapepod_sdk.extension.Client() as client:
                client.conn.run_soon(my_coroutine())
                time.sleep(1)

        :param coro: The coroutine, task or any awaitable to schedule for execution on the connection thread.
        """
        if coro is None or not inspect.isawaitable(coro):
            raise EscapePodAsyncException(f"\n\n{coro.__name__ if hasattr(coro, '__name__') else coro} is not awaitable, so cannot be ran with run_soon.\n")

        def soon():
            try:
                asyncio.ensure_future(coro)
            except TypeError as e:
                raise EscapePodAsyncException(f"\n\n{coro.__name__ if hasattr(coro, '__name__') else coro} could not be ensured as a future.\n") from e
        if threading.current_thread() is self._thread:
            self._loop.call_soon(soon)
        else:
            self._loop.call_soon_threadsafe(soon)

    def run_coroutine(self, coro: Awaitable) -> Any:
        """Runs a given awaitable on the connection thread's event loop.
        Cannot be called from within the connection thread.

        .. testcode::

            import escapepod_sdk

            async def my_coroutine():
                print("Running on the connection thread")
                return "Finished"

            with escapepod_sdk.extension.Client() as client:
                result = client.conn.run_coroutine(my_coroutine())

        :param coro: The coroutine, task or any other awaitable which should be executed.
        :returns: The result of the awaitable's execution.
        """
        if threading.current_thread() is self._thread:
            raise EscapePodAsyncException("Attempting to invoke async from same thread."
                                       "Instead you may want to use 'run_soon'")
        if asyncio.iscoroutinefunction(coro) or asyncio.iscoroutine(coro):
            return self._run_coroutine(coro)
        if asyncio.isfuture(coro):
            async def future_coro():
                return await coro
            return self._run_coroutine(future_coro())
        if callable(coro):
            async def wrapped_coro():
                return coro()
            return self._run_coroutine(wrapped_coro())
        raise EscapePodAsyncException("\n\nInvalid parameter to run_coroutine: {}\n"
                                   "This function expects a coroutine, task, or awaitable.".format(type(coro)))

    def _run_coroutine(self, coro) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)


def on_connection_thread(log_messaging: bool = True) -> Callable[[Coroutine[util.Component, Any, None]], Any]:
    """A decorator generator used internally to denote which functions will run on
    the connection thread. This unblocks the caller of the wrapped function
    and allows them to continue running while the messages are being processed.

    .. code-block:: python

        import escapepod_sdk

        class MyComponent(escapepod_sdk.util.Component):
            @connection._on_connection_thread()
            async def on_connection_thread(self):
                # Do work on the connection thread

    :param log_messaging: True if the log output should include the entire message or just the size. Recommended for
        large binary return values.
    :param requires_control: True if the function should wait until behavior control is granted before executing.
    :param is_cancellable: use a valid enum of :class:`CancelType` to specify the type of cancellation for the
        function. Defaults to 'None' implying no support for responding to cancellation.
    :returns: A decorator which has 3 possible returns based on context: the result of the decorated function,
        the :class:`concurrent.futures.Future` which points to the decorated function, or the
        :class:`asyncio.Future` which points to the decorated function.        
    """
    def _on_connection_thread_decorator(func: Coroutine) -> Any:
        """A decorator which specifies a function to be executed on the connection thread

        :params func: The function to be decorated
        :returns: There are 3 possible returns based on context: the result of the decorated function,
            the :class:`concurrent.futures.Future` which points to the decorated function, or the
            :class:`asyncio.Future` which points to the decorated function.
        """
        if not asyncio.iscoroutinefunction(func):
            raise EscapePodAsyncException("\n\nCannot define non-coroutine function '{}' to run on connection thread.\n"
                                       "Make sure the function is defined using 'async def'.".format(func.__name__ if hasattr(func, "__name__") else func))

        @functools.wraps(func)
        async def log_handler(conn: Connection, func: Coroutine, logger: logging.Logger, *args: List[Any], **kwargs: Dict[str, Any]) -> Coroutine:
            """Wrap the provided coroutine to better express exceptions as specific :class:`escape_pod.exceptions.EscapePodException`s, and
            adds logging to incoming (from the escapepod extension) and outgoing (to the escapepod extension) messages.
            """
            result = None
            # TODO: only have the request wait for control if we're not done. If done raise an exception.            
            message = args[1:]
            outgoing = message if log_messaging else "size = {} bytes".format(sys.getsizeof(message))
            logger.debug(f'Outgoing {func.__name__}: {outgoing}')
            try:
                result = await func(*args, **kwargs)
            except grpc.RpcError as rpc_error:
                raise connection_error(rpc_error) from rpc_error
            incoming = str(result).strip() if log_messaging else "size = {} bytes".format(sys.getsizeof(result))
            logger.debug(f'Incoming {func.__name__}: {type(result).__name__}  {incoming}')
            return result

        @functools.wraps(func)
        def result(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            """The function that is the result of the decorator. Provides a wrapped function.

            :param _return_future: A hidden parameter which allows the wrapped function to explicitly
                return a future (default for AsyncClient) or not (default for Client).
            :returns: Based on context this can return the result of the decorated function,
                the :class:`concurrent.futures.Future` which points to the decorated function, or the
                :class:`asyncio.Future` which points to the decorated function."""
            self = args[0]  # Get the self reference from the function call
            # if the call supplies a _return_future parameter then override force_async with that.
            _return_future = kwargs.pop('_return_future', self.force_async)

            wrapped_coroutine = log_handler(self.conn, func, self.logger, *args, **kwargs)

            if threading.current_thread() == self.conn.thread:
                if self.conn.loop.is_running():
                    return asyncio.ensure_future(wrapped_coroutine, loop=self.conn.loop)
                raise EscapePodAsyncException("\n\nThe connection thread loop is not running, but a "
                                           "function '{}' is being invoked on that thread.\n".format(func.__name__ if hasattr(func, "__name__") else func))
            future = asyncio.run_coroutine_threadsafe(wrapped_coroutine, self.conn.loop)      

            if _return_future:
                return future
            try:
                return future.result()
            except futures.CancelledError:
                self.logger.warning(f"{func.__name__} cancelled because behavior control was lost")
                return None
        return result
    return _on_connection_thread_decorator 