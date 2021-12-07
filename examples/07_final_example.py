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

"""The Final example script of this SDK.

This script wraps all the previous examples and creates a scenario, where
a new escapepod extension intent is created dynamically from this code,
and demonstrates the capability of this SDK to inmediatelly react to such
dynamically created voice commands.
Besides, it demoes how to query the intent data from database, and delete
them.
When Vector recognizes the specified keywords, the escapepod extension
proxy fires the event back to this script's event handler, where Vector's
behaviour is overriden with Vector's final speech.
Once done, thread is marked as complete and program exits and cleanes
after itself.
This program will run for 120 seconds or until Ctrl+C keys are pressed.

I Hope these examples has provided you with a esential training of how to
use this "EscapePod SDK for Python" and that it will open for you brand
new possibilites of how to enjoy your EscapePod.

Enjoy!
cyb3rdog
"""


import time
import threading

import anki_vector
from anki_vector.connection import ControlPriorityLevel

import escapepod_sdk
from escapepod_sdk.events import Events
from escapepod_sdk.messages import process_intent


def on_intent_heard(robot: anki_vector.Robot, event_name, msg: process_intent, done):
    if msg.intent_name == "final_intent":
        robot.conn.request_control(ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY)
        time.sleep(0.1)
        robot.behavior.say_text(f"Yeah, this is so cool! I've received the {msg.intent_name.replace('_',' ')} command.")
        robot.conn.release_control()
        done.set()

def main():
    print("\nEscapePod Extension Proxy Final Example:\nPress Ctrl+C to exit...\n")
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial, cache_animation_lists=False) as robot:
        # Yes, here too. Replace the IP for wherever you've deployed the extension to
        with escapepod_sdk.extension.Client("127.0.0.1", robot=robot) as client:

            done = threading.Event()
            client.events.subscribe(on_intent_heard, Events.process_intent, done)
            # Delete the final_intent, in case it has been created previously
            client.intents.delete_intent("final_intent")
            # Create new intent with following basic definition
            new_intent = client.intents.create_intent(name="Cool SDK testing intent", intent="final_intent",
                                                      keywords="cool, this is cool, thats cool, so cool, yeah, awesome, thats awesome, this is awesome")
            try:
                # Look up the database if the final_intent has been indeed created
                intents = client.intents.select_intents('{"intent": "final_intent"}')

                if len(intents) == 1:
                    # Lets print some information
                    print(f"\nNew EscapePod Extension intent successfully created!")
                    print("- Data:")
                    print(intents[0]._json)
                    print(f"\n- You can take a look at it here: http://escapepod.local/behaviors/{new_intent}")
                    print(f"- Vector will now listen for all of following keywords:\n\t{intents[0].utterance_list}\n")

                    robot.behavior.say_text("Ready!")
                    robot.conn.release_control()

                    try:
                        done.wait(timeout=120)
                    except KeyboardInterrupt:
                        pass
            finally:
                # Clean. When the script finishes, there is nothing to react to our final_intent...
                client.intents.delete_intent("final_intent")
                client.disconnect()


if __name__ == "__main__":
    main()
