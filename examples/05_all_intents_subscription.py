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

"""Override all voice commands given to Vector

This script demonstrates how to override Vector's default behaviours and
react to all possible voice commands regardless of whether they're received
from EscapePod or whether the robot is under behavioral control or not.

After the robot hears "Hey Vector!..." and a any voice command is given
the event will be dispatched and the intent name will be spoken by Vector.

This program will run for 120 seconds or until Ctrl+C keys are pressed.

Enjoy!
cyb3rdog
"""

import json
import time

import anki_vector
from anki_vector.events import Events
from anki_vector.connection import ControlPriorityLevel
from anki_vector.user_intent import UserIntent

import escapepod_sdk
from escapepod_sdk.messages import process_intent


def main():    
    class event_processor():            
        def on_voice_command(robot: anki_vector.Robot, source: str, intent_name: str):
            """This event handler gathers the voice commands from all the sources, and processes them"""
            print(f"{source} voice command heard: '{intent_name}'")
            robot.conn.request_control(ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY)
            time.sleep(0.1)
            robot.behavior.say_text(f"I've heard a {source} command: {intent_name.replace('_',' ')}")            
            robot.conn.release_control()
        
        def on_intent_heard(robot: anki_vector.Robot, event_name, msg: process_intent):
            """This event handler provides with intents received trough escapepod extension"""
            event_processor.on_voice_command(robot, "Escape Pod Extension", msg.intent_name)

        def on_user_intent(robot: anki_vector.Robot, event_type, event):
            """This event handler provides with intents received from 'user_intent' event"""
            event_processor.on_voice_command(robot, "User Intent", UserIntent(event).intent_event.name)

        def on_wake_word_end(robot: anki_vector.Robot, event_type, event):
            """This event handler provides intents received from 'wake_word_end' event"""
            if event.wake_word_end.intent_heard and not event.wake_word_end.intent_json == '':
                jsonData = json.loads(event.wake_word_end.intent_json)
                event_processor.on_voice_command(robot, "Wake Word End", jsonData["type"])


    print("\nEscapePod Extension Proxy Basic Example:\nPress Ctrl+C to exit...\n")
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial, cache_animation_lists=False) as robot:
        robot.events.subscribe(event_processor.on_user_intent, Events.user_intent)
        robot.events.subscribe(event_processor.on_wake_word_end, Events.wake_word)
        # Replace the "XX.XX.XX.XX" with and ip where the escapepod extension proxy is deployed.
        with escapepod_sdk.extension.Client("XX.XX.XX.XX", robot=robot) as client:
            # Robot object is passed to extension Client constructor to be forwarded to event handler.
            client.events.subscribe_by_name(event_processor.on_intent_heard, event_name='ProcessIntent')
            robot.behavior.say_text("Ready. Hit me with a voice command.")
            #robot.conn.release_control()
            try:
                time.sleep(120)     # program will run for 2 minutes, or until Crtl+C
            except KeyboardInterrupt:
                pass
            finally:
                client.disconnect()

if __name__ == '__main__':
    main()
