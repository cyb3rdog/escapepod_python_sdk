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
SDK by Cyb3rdog for programming with Cyb3rVector EscapePod Extension Proxy.
"""

import sys
import logging

from . import messages
from . import messaging
from .extension import Client
from .version import __version__

logger = logging.getLogger('escapepod_sdk')  # pylint: disable=invalid-name

if sys.version_info < (3, 6, 1):
    sys.exit('escapepod_sdk requires Python 3.6.1 or later')

__all__ = ['Client', 'logger', 'messages', 'messaging', '__version__']
