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

"""React to escapepod extension voice commands given to Vector

This script demonstrates the capability of reacting to escape pod
voice commands and extending Vector's behaviours with this Python SDK.

The ProcessIntent event is only dispatched when the escape pod intent
is marked for "Extenral Parsing" and Vector gets matching voice command.

You can create such intents on the http://escapepod.local/behaviors/new
or use this SDK's IntentFactory class to create custom intents from code.
(Note: There is possibly a Bug in EscapePod v1.0 and the reponse parameter's
'final_intent' value have to match the intent_name - the 'Behavior' field).

After the robot hears "Hey Vector!..." and a valid voice command is given
(for example "...whats the wheater?") the event will be dispatched and
its data will be spoken by Vector and also displayed on the screen.

This program will run for 120 seconds or until Ctrl+C keys are pressed.

Enjoy!
cyb3rdog
"""

import time

import anki_vector
from anki_vector.connection import ControlPriorityLevel

import escapepod_sdk
from escapepod_sdk.messages import process_intent


def main():
    def on_intent_heard(robot: anki_vector.Robot, event_name, msg: process_intent):
        print(f"{event_name} event received: '{msg.intent_name}'")
        robot.conn.request_control(ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY)
        time.sleep(0.1)
        if msg.intent_name == "intent_weather_extend":
            robot.behavior.say_text(f"I dont know! Look out from the window!")
        else:
            robot.behavior.say_text(f"{msg.message}: {msg.intent_name}")
        robot.conn.release_control()


    print("\nEscapePod Extension Proxy Basic Example:\nPress Ctrl+C to exit...\n")

    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial, cache_animation_lists=False) as robot:
        # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
        with escapepod_sdk.extension.Client("XX.XX.XX.XX", robot=robot) as client:
            # Robot object is passed to extension Client constructor to be forwarded to event handler.
            client.events.subscribe_by_name(on_intent_heard, event_name='ProcessIntent')
            robot.behavior.say_text("Ready. Waiting for Hey Vector, whats the wheater?")
            try:
                time.sleep(120)     # program will run for 2 minutes, or until Crtl+C
            except KeyboardInterrupt:
                pass
            finally:
                client.disconnect()

if __name__ == '__main__':
    main()
