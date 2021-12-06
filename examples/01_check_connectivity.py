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

"""Basic Connectiion Check Example script

Check the connectivity to the EscapePod Extension Proxy with this simple SDK script.

In case you'll face issues with connecting to Cyb3rVector's EscapePod Extension Proxy,
please check the github deployment guide: https://github.com/cyb3rdog/escapepod_python_sdk
and make sure all - Vector, EscapePod and Extension Proxy are on the same network and
can reach other
--- ---------------------------------------------------------------------- ---
--- In order for the EscapePod itself to be able to connect to this proxy, ---
--- and push its events here, it needs to know where this proxy is hosted. ---
--- Set following variables in /etc/escape-pod.conf file corresondingly:   ---
---                                                                        ---
--- ENABLE_EXTENSIONS=true                                                 ---
--- ESCAPEPOD_EXTENDER_TARGET=XX.XX.XX.XX:8089                             ---
--- ESCAPEPOD_EXTENDER_DISABLE_TLS=true                                    ---
--- ---------------------------------------------------------------------- ---
"""

import escapepod_sdk

def main():
    # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
    # By default its usually deployed on the escapepod itself, so its same as your escapepod ip.
    with escapepod_sdk.extension.Client("XX.XX.XX.XX") as client:
        client.wait_for_eventstream()
        if client.events.subscribed:
            print("GREAT! EscapePod extension proxy is connected and ready!")
        else:
            print("ERROR: Something went wrong! Event stream not connected!")
        client.disconnect()

if __name__ == "__main__":
    main()
