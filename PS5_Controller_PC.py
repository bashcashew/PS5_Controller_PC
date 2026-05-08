#############################################################################
#############################################################################
##                                                                         ##
##                                                                         ##
## Title:            PS5-to-PC Controller and Re-mapper                    ##
## Description:      This should allow for your PC to intercept the        ##
##                   bluetooth signal from your PS5 controller. This will  ##
##                   then be remapped to your own liking.                  ##
## Features:         - Custom rumble per key press                         ##
##                   - Re-mappable button, trigger presses                 ##
##                   - Telemetric data in .csv (stored in a sub-folder)    ##
##                   - mouse movement, single-click, and scrolling         ##
## Version:          1.0.0                                                 ##
##                                                                         ##
##                                                                         ##
#############################################################################
#############################################################################



## Imports
import sys
import pygame
import pyautogui
from pynput.mouse import Controller as MouseController, Button
import csv
from datetime import datetime
import os

from pygame.locals import *
###########################




# Initialize pygame and joystick support
pygame.init()
pygame.joystick.init()

# Initialize mouse controller
mouse = MouseController()

# Sensitivity settings for mouse movement and scrolling
MOUSE_SENSITIVITY = 75  # Adjusts speed of mouse movement
SCROLL_SENSITIVITY = 10  # Adjusts speed of scrolling
JOYSTICK_DEADZONE = 0.1  # Deadzone threshold for joystick axes (ignore small inputs)

# Rumble settings
RUMBLE_STRENGTH = 0.1  # (Should set 0.0 to 1.0)
RUMBLE_DURATION = 500  # milisecond timings 
KEEP_AWAKE_INTERVAL = 5  # seconds

# Checks if joysticks are connected
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for joystick in joysticks:
    joystick.init()
    print(f"Joystick {joystick.get_name()} connected")

# Custom mappings for buttons and axes
button_mapping = {
    "L1": 9,  # L1 Button
    "R1": 10, # R1 Button
    "L3": 7,  # L3 Press
}

axis_mapping = {
    "left_stick_x": 0,  # Left stick horizontal movement
    "left_stick_y": 1,  # Left stick vertical movement
    "right_stick_y": 3, # Right stick vertical for scrolling
}

# Initialize CSV file with unique filename in the script's directory
def get_unique_csv_filename(base_name):
    """Generate a unique filename by appending a numeric suffix if the file exists."""
    #' Finds directory where the script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_directory + '/TELEM', base_name)
    counter = 1
    while os.path.exists(filename):
        filename = os.path.join(script_directory, f"{base_name.split('.')[0]}_{counter}.csv")
        counter += 1
    return filename

# Get the CSV file path for the Telemetry
CSV_FILE = get_unique_csv_filename("TELEM.csv")

# Write header to the new CSV file
with open(CSV_FILE, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Event", "Value"])
print(f"Logging telemetry to {CSV_FILE}")

#' log data to CSV
def log_to_csv(event, value):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, event, value])

#' trigger rumble
def trigger_rumble(joystick, strength, duration):
    if joystick:
        joystick.rumble(strength, strength, duration)

#' Function for awake
def keep_controller_awake(joystick):
    if joystick:
        joystick.rumble(0.01, 0.01, 100)  # Light rumble to keep the controller active

#' The Loopty Loop
try:
    print("Listening for controller input. Press Ctrl+C to quit.")
    last_awake_time = pygame.time.get_ticks()  # Tracks time to send keep-alive signals
    while True:
        current_time = pygame.time.get_ticks()

        #' Send a light rumble periodically to keep the controller awake --> This ofc can be changed but good for tactile awareness/ presence
        if current_time - last_awake_time > KEEP_AWAKE_INTERVAL * 1000:
            keep_controller_awake(joysticks[0])
            last_awake_time = current_time

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # Handle button presses
            if event.type == JOYBUTTONDOWN:
                for action, button in button_mapping.items():
                    if event.button == button:
                        log_to_csv(f"{action} pressed", f"Button {button}")
                        print(f"TELEMETRY: {action} pressed (Button {button})")
                        
                        #' Simulate desktop switching with L1 and R1
                        if action == "R1":
                            pyautogui.hotkey('ctrl', 'right')  #' CTRL + RIGHT
                            trigger_rumble(joysticks[0], RUMBLE_STRENGTH, RUMBLE_DURATION)
                        elif action == "L1":
                            pyautogui.hotkey('ctrl', 'left')   #' CTRL + LEFT
                            trigger_rumble(joysticks[0], RUMBLE_STRENGTH, RUMBLE_DURATION)

                        #' Simulate left mouse click on L3 press
                        if action == "L3":
                            log_to_csv("Left mouse click triggered", "")
                            print("TELEMETRY: Left mouse click triggered")
                            mouse.click(Button.left, 1)  #' Left mouse click
                            trigger_rumble(joysticks[0], RUMBLE_STRENGTH, RUMBLE_DURATION)

            #'   joystick movements for mouse and scrolling
            if event.type == JOYAXISMOTION:
                axis_value = event.value
                if abs(axis_value) > JOYSTICK_DEADZONE:
                    if event.axis == axis_mapping["left_stick_x"]:
                        log_to_csv("Left stick X moved", f"{axis_value:.3f}")
                        print(f"TELEMETRY: Left stick X moved: {axis_value:.3f}")
                        mouse.move(axis_value * MOUSE_SENSITIVITY, 0)
                    elif event.axis == axis_mapping["left_stick_y"]:
                        log_to_csv("Left stick Y moved", f"{axis_value:.3f}")
                        print(f"TELEMETRY: Left stick Y moved: {axis_value:.3f}")
                        mouse.move(0, axis_value * MOUSE_SENSITIVITY)  # Inverted for natural feel
                    elif event.axis == axis_mapping["right_stick_y"]:
                        log_to_csv("Right stick Y scrolled", f"{axis_value:.3f}")
                        print(f"TELEMETRY: Right stick Y scrolled: {axis_value:.3f}")
                        mouse.scroll(0, axis_value * SCROLL_SENSITIVITY)

                        #' Adds optional rumble feedback for scrolling
                        if abs(axis_value) > 0.5:  # Rumble only if joystick pushed significantly
                            trigger_rumble(joysticks[0], RUMBLE_STRENGTH * abs(axis_value), 100)

except KeyboardInterrupt:
    print("\nExiting...")
    pygame.quit()
    sys.exit()
