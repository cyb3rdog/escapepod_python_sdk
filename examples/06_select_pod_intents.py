#!/usr/bin/env python3

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

"""Select and display escapepod intents

This script demonstrates the EscapePod extension capabilities to query the intents
from EscapePod's MongoDB database and use of mongoDB unmarshal json2bson filter.

It will print two blocks of intents - first, all of the intents configured on your
escapepod, and as second, all the intents which are configured for "external parsing"
"""

import escapepod_sdk

def select_intents(client: escapepod_sdk.extension.Client, filter: str = '{}'):
    print(f"Selecing escapepod intents using filter: {filter}:")
    intents = client.intents.select_intents(filter)
    for intent in intents:
        print(f" - {intent.intent}")
    print(f" Total of {len(intents)} intents found.\n")

def main():
    # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
    with escapepod_sdk.extension.Client("XX.XX.XX.XX") as client:
        print("\nEscapePod Extension Select Intents Example:\n")
        select_intents(client, '{}')
        select_intents(client, '{"extended_options": {"external_parser": true}}')
        client.disconnect()


if __name__ == "__main__":
    main()
