#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configargparse

import cv2 as cv

from gestures.tello_gesture_controller import TelloGestureController
from gestures.swarm_gesture_controller import SwarmGestureController
from utils import CvFpsCalc

from djitellopy import Tello
from djitellopy import TelloSwarm
from gestures import *

import threading


def get_args():
    print('## Reading configuration ##')
    parser = configargparse.ArgParser(default_config_files=['config.txt'])

    parser.add('-c', '--my-config', required=False, is_config_file=True, help='config file path')
    parser.add("--device", type=int)
    parser.add("--width", help='cap width', type=int)
    parser.add("--height", help='cap height', type=int)
    parser.add("--is_keyboard", help='To use Keyboard control by default', type=bool)
    parser.add('--use_static_image_mode', action='store_true', help='True if running on photos')
    parser.add("--min_detection_confidence",
               help='min_detection_confidence',
               type=float)
    parser.add("--min_tracking_confidence",
               help='min_tracking_confidence',
               type=float)
    parser.add("--buffer_len",
               help='Length of gesture buffer',
               type=int)

    args = parser.parse_args()

    return args

def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode


def main():
    # init global vars
    global gesture_buffer
    global gesture_id
    global battery_status
    global swarm_behavior # If program will command swarm or individual tello

    swarm_behavior = True
    if swarm_behavior:
        global swarm_bat_stat # PATRICK
        swarm_bat_stat = [] # PATRICK

    # Argument parsing
    args = get_args()
    KEYBOARD_CONTROL = args.is_keyboard
    WRITE_CONTROL = False
    in_flight = False

    
    # Camera preparation
    if not swarm_behavior: # ORIGINAL (used for single drone)
        tello = Tello()
        tello.connect()

        # Use tello's camera - ORIGINAL
        cap = tello.get_frame_read() 
        tello.streamon()

        # Init Tello Controllers
        gesture_controller = TelloGestureController(tello) # ORIGINAL
        keyboard_controller = TelloKeyboardController(tello) # ORIGINAL
    else:
        # Multi Drone Control - PATRICK 
        Tello1_IP = "192.168.1.100"
        Tello2_IP = "192.168.1.200"
        drone1 = Tello(Tello1_IP)
        drone2 = Tello(Tello2_IP)
        swarm = TelloSwarm([drone1,drone2])
        swarm.connect()

        # Use computer's camera - PATRICK
        cap = cv.VideoCapture(0)

        # Init Swarm Controller
        gesture_controller = SwarmGestureController(swarm) # PATRICK

    
    gesture_detector = GestureRecognition(args.use_static_image_mode, args.min_detection_confidence,
                                          args.min_tracking_confidence)
    gesture_buffer = GestureBuffer(buffer_len=args.buffer_len)

    def tello_control(key, keyboard_controller, gesture_controller): # ORIGINAL
        global gesture_buffer

        if KEYBOARD_CONTROL:
            keyboard_controller.control(key)
        else:
            gesture_controller.gesture_control(gesture_buffer)

    def swarm_control(gesture_controller): # PATRICK 
        global gesture_buffer
        if not KEYBOARD_CONTROL: # Wait to press G key
            gesture_controller.gesture_control(gesture_buffer)

    def tello_battery(tello): # ORIGINAL
        global battery_status
        try:
            battery_status = tello.get_battery() # had [:-2] at end that caused type error 
        except:
            battery_status = -1

    def swarm_battery(swarm): # PATRICK
        global swarm_bat_stat
        try:
            for count,tello in enumerate(swarm):
                swarm_bat_stat[count] = tello.get_battery()
        except:
            for count,tello in enumerate(swarm):
                swarm_bat_stat[count] = -1          

    # FPS Measurement
    cv_fps_calc = CvFpsCalc(buffer_len=10)

    mode = 0
    number = -1

    if not swarm_behavior:
        battery_status = -1 # ORIGINAL
    else:
        for tello in swarm:    # PATRICK        
            swarm_bat_stat.append(-2) # Set to -2 here to be different from error value in swarm_battery()


    while True:

        fps = cv_fps_calc.get()

        # Process Key (ESC: end)
        key = cv.waitKey(1) & 0xff
        if key == 27:  # ESC
            break
        elif key == 32:  # Space
            if not in_flight:
                if not swarm_behavior:
                    tello.takeoff() # Take-off drone ORIGINAL
                else:
                    swarm.takeoff() # Take-off drone PATRICK
                in_flight = True

            elif in_flight:
                if not swarm_behavior:
                    tello.land() # Land tello ORIGINAL
                else:
                    swarm.land() # Land tello PATRICK
                in_flight = False

        elif key == ord('k'): # Keyboard Control
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            # Stop moving
            if not swarm_behavior:
                tello.send_rc_control(0, 0, 0, 0)  
            else:
                swarm.parallel(lambda i, tello: tello.send_rc_control(0,0,0,0) )
        elif key == ord('g'): # Gesture Control
            KEYBOARD_CONTROL = False
        elif key == ord('n'): # Save Key Points
            mode = 1
            WRITE_CONTROL = True
            KEYBOARD_CONTROL = True

        if WRITE_CONTROL: # Generate Training Data For Gesture
            number = -1
            if 48 <= key <= 57:  # 0 ~ 9
                number = key - 48

        # Camera capture
        if not swarm_behavior:
            image = cap.frame # ORIGINAL - Use tello's camera 
        else:
            success, image = cap.read() # PATRICK - Use computer's camera
            if not success:
                continue # try to capture another frame successfully 


        debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        gesture_buffer.add_gesture(gesture_id)

        # Start control threads
        if not swarm_behavior:
            threading.Thread(target=tello_control, args=(key, keyboard_controller, gesture_controller,)).start() # ORIGINAL
            threading.Thread(target=tello_battery, args=(tello,)).start() # ORIGINAL
        else:
            threading.Thread(target=swarm_control, args=(gesture_controller,)).start() # PATRICK
            threading.Thread(target=swarm_battery, args=(swarm,)).start() # PATRICK

        debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        # Battery status and image rendering
        if not swarm_behavior:
            cv.putText(debug_image, "Battery: {}".format(battery_status), (5, 720 - 5), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2) # ORIGINAL
        else:
            cv.putText(debug_image, "Allow Flip: {}".format(gesture_controller.AllowF), (5, 480 - 5), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2) # PATRICK
            for count,tello in enumerate(swarm):
                cv.putText(debug_image, f"tello {count+1} Battery: {swarm_bat_stat[count]}", (5, 400 - count * 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2) # PATRICK
        
        cv.imshow('Tello Gesture Recognition', debug_image)

    if not swarm:
        tello.land()
        tello.end()
    else:
        swarm.parallel(lambda i, tello: tello.land() )
        swarm.end()
    
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
