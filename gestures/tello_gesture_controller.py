from djitellopy import Tello
import keyboard


class TelloGestureController:
    def __init__(self, tello: Tello):
        self.tello = tello
        self._is_landing = False

        # RC control velocities
        self.forw_back_velocity = 0
        self.up_down_velocity = 0
        self.left_right_velocity = 0
        self.yaw_velocity = 0

    def gesture_control(self, gesture_buffer):
        gesture_id = gesture_buffer.get_gesture()
        print("GESTURE", gesture_id)

        if not self._is_landing:

            # If keyboard chars are in conditionals
            # they are for Patrick's special flight behavior

            if gesture_id == 8 and keyboard.is_pressed('z'): # Flip
                self.tello.flip("f")
                print("Flip")

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
                self.forw_back_velocity = self.up_down_velocity = \
                    self.left_right_velocity = self.yaw_velocity = 0
                self.tello.land()

            elif gesture_id == 6: # LEFT
                self.left_right_velocity = 20
                #self.yaw_velocity = 50 # turn left
            elif gesture_id == 7: # RIGHT
                self.left_right_velocity = -20
                #self.yaw_velocity = -50 # turn right

            elif gesture_id == -1:
                self.forw_back_velocity = self.up_down_velocity = \
                    self.left_right_velocity = self.yaw_velocity = 0


            self.tello.send_rc_control(self.left_right_velocity, self.forw_back_velocity,
                                       self.up_down_velocity, self.yaw_velocity)
