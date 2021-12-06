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
A class providing with extension proxy's intent manipulation rpc calls 
"""

# __all__ should order by constants, event classes, other classes, functions.
__all__ = ['IntentFactory']


from enum import Enum
from typing import List

from . import connection, util
from .messaging import protocol
from .messages import escapepod_intent
from .exceptions import EscapePodProxyException


class ResponseCode(Enum):
    """Specifies the Response Message Code."""
    SUCCESS = 0
    FAILURE = 1 

class IntentFactory(util.Component):
    """Handles communication and provides with factory for EscapePod Intents"""

    @connection.on_connection_thread()
    async def create_intent(self, name: str, keywords: str, description: str = None, intent: str = None) -> protocol.InsertIntentResponse:
        """
        """
        if name == None or name == "":
            raise EscapePodProxyException("Intent name is mandatory")        

        if intent == None: intent = f"intent_{name}"
        new_intent = escapepod_intent(name=name, intent=intent, utterance_list=keywords, description=description)
        response = await self.insert_intent(new_intent.to_json())
        return response.inserted_oid


    @connection.on_connection_thread()
    async def insert_intent(self, intent_json: str) -> protocol.InsertIntentResponse:
        """
        """
        request = protocol.InsertIntentRequest(intent_data = intent_json)
        response = await self.grpc_interface.InsertIntent(request)
        if (response.response.code == ResponseCode.FAILURE):
            raise EscapePodProxyException(response.response.message)
        return response


    @connection.on_connection_thread()
    async def select_intents(self, filter_json: str = '{}') -> List[escapepod_intent]:
        """
        """
        request = protocol.SelectIntentRequest(filter_json = filter_json)
        response = await self.grpc_interface.SelectIntents(request)
        if (response.response.code == ResponseCode.FAILURE):
            raise EscapePodProxyException(response.response.message)
        return escapepod_intent.from_response(response)


    @connection.on_connection_thread()
    async def delete_intent_by_id(self, intent_id: str) -> protocol.DeleteIntentResponse:
        """
        """
        request = protocol.DeleteIntentRequest(intent_id = intent_id)
        response = await self.grpc_interface.DeleteIntent(request)
        if (response.response.code == ResponseCode.FAILURE):
            raise EscapePodProxyException(response.response.message)
        return response

    @connection.on_connection_thread()
    async def delete_intent(self, intent: str):
        """
        """
        intents = await self.select_intents('{"intent": "' + intent + '"}')
        for item in intents:
            await self.delete_intent_by_id(item.id.oid)
