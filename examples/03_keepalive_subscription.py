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

"""Whenever the 'keep connection alive' event is received, display the
timestamp and let Vector say something.

This script demonstrates how to set up a listener for an extension event.
It subscribes to event 'KeepAlive' and when that event is dispatched from
escapepod extension proxy, the 'on_keep_alive' method is called, where the
event's data are displayed on the screen and event's name said by Vector.

This program will run for 30 seconds or until Ctrl+C keys are pressed.

Enjoy!
cyb3rdog
"""

import time
import anki_vector
import escapepod_sdk

from escapepod_sdk.messages import keep_alive

def main():
    def on_keep_alive(robot: anki_vector.Robot, event_name, msg: keep_alive):
        print(f"Event: {event_name}, Timestamp: {msg.timestamp}")
        robot.behavior.say_text(event_name)

    print("\nEscapePod Extension Proxy Basic Example:\nPress Ctrl+C to exit...\n")

    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial, cache_animation_lists=False) as robot:
        # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
        with escapepod_sdk.extension.Client("XX.XX.XX.XX", robot=robot, keep_alive=5) as client:
            # Robot object is passed to extension Client constructor to be forwarded to event handler.
            client.events.subscribe_by_name(on_keep_alive, event_name='KeepAlive')
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                pass
            finally:
                client.disconnect()

if __name__ == '__main__':
    main()
