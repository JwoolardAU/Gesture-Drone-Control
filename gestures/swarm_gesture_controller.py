from cgitb import reset

from djitellopy import Tello
from djitellopy import TelloSwarm
import keyboard
import time


class SwarmGestureController:
    def __init__(self, swarm: TelloSwarm):
        self.swarm = swarm
        self._is_landing = False
        

        # Controller to wether or not we want to allow flips. 
        # Needs to be reset after ever flip by pressing 'z' key
        self.AllowF = False

        # RC control velocities (speed varies from 0,10-100)
        self.forw_back_velocity = 0
        self.up_down_velocity = 0
        self.left_right_velocity = 0
        self.yaw_velocity = 0

    def gesture_control(self, gesture_buffer):
        gesture_id = gesture_buffer.get_gesture()
        # print("GESTURE", gesture_id) # PAT (uncomment to see gesture num in cmd)

        if not self._is_landing:
            
            
            
            if keyboard.is_pressed('z'): # Reset flip permissions
                self.AllowF = True

            if gesture_id == 8 and self.AllowF: # Flip
                for tello in self.swarm:
                    tello.send_command_without_return("flip f")
                print("Flips! Weeeee")
                self.AllowF = False

            if gesture_id == 0 and keyboard.is_pressed('f'):  # Left Circle
                self.yaw_velocity = 30 # turn left
                self.forw_back_velocity = 20 # go forward at same speed of turn
            elif gesture_id == 0:
                self.forw_back_velocity = 30
            elif gesture_id == 1:  # STOP
                self.forw_back_velocity = self.up_down_velocity = \
                    self.left_right_velocity = self.yaw_velocity = 0
            if gesture_id == 5:  # Back
                self.forw_back_velocity = -30

            elif gesture_id == 2:  # UP
                self.up_down_velocity = 25
            elif gesture_id == 4:  # DOWN
                self.up_down_velocity = -25

            elif gesture_id == 3:  # LAND
                self._is_landing = True
                self.forw_back_velocity = 0
                self.up_down_velocity = 0
                self.left_right_velocity = 0
                self.yaw_velocity = 0
                for tello in self.swarm:
                   tello.send_command_without_return("land")

            elif gesture_id == 6: # LEFT
                self.left_right_velocity = 20
                #self.yaw_velocity = 50 # turn left
            elif gesture_id == 7: # RIGHT
                self.left_right_velocity = -20
                #self.yaw_velocity = -50 # turn right

            elif gesture_id == -1:
                self.forw_back_velocity = self.up_down_velocity = \
                    self.left_right_velocity = self.yaw_velocity = 0

            self.swarm.parallel(lambda i, tello: tello.send_rc_control(self.left_right_velocity, self.forw_back_velocity, self.up_down_velocity, self.yaw_velocity) )
