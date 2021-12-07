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

"""Basic Example with DEBUG log level

Sets the SDK_LOG_LEVEL enviroment variable to DEBUG to display some debug events from the SDK.
The program will run for 15 seconds or until Ctrl+C keys are pressed.
"""

import os
import time
import escapepod_sdk

def main():
    print("\nEscapePod Extension Proxy Basic Example:\nPress Ctrl+C to quit...\n")
    os.environ.setdefault('SDK_LOG_LEVEL', "DEBUG")
    # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
    # By default its usually deployed on the escapepod itself, so its same as your escapepod ip.
    with escapepod_sdk.extension.Client("XX.XX.XX.XX", keep_alive=3) as client:
        try:
            time.sleep(15)
        except KeyboardInterrupt:
            pass
        finally:
            client.disconnect()

if __name__ == "__main__":
    main()
