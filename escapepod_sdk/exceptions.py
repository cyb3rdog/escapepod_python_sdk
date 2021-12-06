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
SDK-specific exception classes for EscapePod Extension Proxy.
"""

from grpc import RpcError, StatusCode

# __all__ should order by constants, event classes, other classes, functions.
__all__ = ['EscapePodAsyncException',
           'EscapePodInvalidVersionException',
           'EscapePodConnectionException',
           'EscapePodException',
           'EscapePodNotReadyException',
           'EscapePodNotFoundException',
           'EscapePodPropertyValueNotReadyException',
           'EscapePodTimeoutException',
           'EscapePodUnavailableException',
           'EscapePodUnimplementedException',
           'EscapePodUnreliableEventStreamException',
           'connection_error']


class EscapePodException(Exception):
    """Base class of all EscapePod SDK exceptions."""


class EscapePodConnectionException(EscapePodException):
    def __init__(self, cause):
        doc_str = self.__class__.__doc__
        if cause is not None:
            self._status = cause.code()
            self._details = cause.details()
            msg = (f"{self._status}: {self._details}"
                   f"\n\n{doc_str if doc_str else 'Unknown error'}")
            super().__init__(msg)
        else:
            super().__init__(doc_str)

    @property
    def status(self):
        return self._status

    @property
    def details(self):
        return self._details


class EscapePodUnavailableException(EscapePodConnectionException):
    """Unable to reach EscapePod Extension Proxy."""


class EscapePodUnimplementedException(EscapePodConnectionException):
    """EscapePod Extension Proxy does not handle this message."""


class EscapePodTimeoutException(EscapePodConnectionException):
    """Message took too long to complete."""


def connection_error(rpc_error: RpcError) -> EscapePodConnectionException:
    """Translates grpc-specific errors to user-friendly :class:`EscapePodConnectionException`."""
    code = rpc_error.code()
    if code is StatusCode.UNAVAILABLE:
        return EscapePodTimeoutException(rpc_error)
    if code is StatusCode.UNIMPLEMENTED:
        return EscapePodUnimplementedException(rpc_error)
    if code is StatusCode.DEADLINE_EXCEEDED:
        return EscapePodTimeoutException(rpc_error)
    return EscapePodConnectionException(rpc_error)


class _EscapePodGenericException(EscapePodException):
    def __init__(self, _cause=None, *args, **kwargs):  # pylint: disable=keyword-arg-before-vararg
        msg = (f"{self.__class__.__doc__}\n\n{_cause if _cause is not None else ''}")
        super().__init__(msg.format(*args, **kwargs))


class EscapePodAsyncException(_EscapePodGenericException):
    """Invalid asynchronous action attempted."""


class EscapePodNotReadyException(_EscapePodGenericException):
    """The escapepod_sdk.extention.Client not yet fully initialized."""


class EscapePodNotFoundException(_EscapePodGenericException):
    """Unable to establish a connection to Cyb3rVector EscapePod Extension Proxy.

Make sure you're on the same network, and the Extension Proxy is deployed and running."""


class EscapePodPropertyValueNotReadyException(_EscapePodGenericException):
    """Failed to retrieve the value for this property."""


class EscapePodUnreliableEventStreamException(EscapePodException):
    """The escapepod proxy event stream is currently unreliable."""


class EscapePodProxyException(EscapePodException):
    """The Proxy Message returned with a Failure Code."""
    def __init__(self, proxy_exception: str = None):
        super().__init__(proxy_exception)
        self._proxy_exception = proxy_exception

    @property
    def proxy_exception(self) -> Exception:
        return self._proxy_exception
