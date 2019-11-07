from ICamera import ICamera
from IDriveControl import IDriveControl
from Rotator import Rotator
import numpy as np
from cv2 import cv2
import os
import time
import math

"""
Simulates movement across a virtual parcours surface where the camera is installed
close to the ground in front of the robot looking down at the ground in 90° angle.

Tweak robot agility using ROBOT_WIDTH (default: 200 pixel)
Tweak translation and rotation speed by setting SPEED_FACTOR in pixel (default: 5.0)
Tweak inertia using MAXIMUM_ACCELERATION and MAXIMUM_DECELERATION in delta_speed in percent per millisecond
"""
class Simulator(ICamera, IDriveControl):
    ROBOT_WIDTH = 200
    SPEED_FACTOR = 5.0
    MAXIMUM_ACCELERATION = 0.1
    MAXIMUM_DECELERATION = 0.5

    __MINIMAP_SCALE_FACTOR = 0.1
    __COLOR_RED = (0, 0, 255)

    __camera_offset = None
    __rotator = None
    __left_speed = 0
    __right_speed = 0
    __last_speed_update_left = None
    __last_speed_update_right = None
    __paused = False
    __minimap = None
    __width = None
    __height = None

    def __init__(self, path: str, start_x: int, start_y: int, pixel_width = 240, pixel_height = 240, camera_height = 1.0, camera_offset = 200):
        """
        Connect drive control to parcours image cropping, translation and rotation.
        path: absolute path to the parcours image
        start_x: start position from left side in pixels.
        start_y: start position from top in pixels.
        pixel_width: width of the camera viewing area in pixel
        pixel_height: height of the camera viewing area in pixel
        camera_height: resize parcours to simulate the installation height of the camera (resize factor of the underlying parcours image)
        camera_offset: distance of the camera from the robot's rotation center in pixels
        """
        if not os.path.exists(path):
            raise ValueError("path not found")
        self.__camera_offset = camera_offset
        self.__width = pixel_width
        self.__height = pixel_height
        self.__rotator = Rotator(path, pixel_width, pixel_height, start_x, start_y, camera_height)
        self.__minimap = cv2.resize(self.__rotator.get_field().copy(), dsize=None, fx=self.__MINIMAP_SCALE_FACTOR, fy=self.__MINIMAP_SCALE_FACTOR, interpolation=cv2.INTER_AREA)

    def __show_minimap(self):
        tmp_minimap = self.__minimap.copy()
        # draw camera view (as a circle so we don't have to rotate anything)
        cx, cy = self.__rotator.get_current_position()
        cv2.circle(tmp_minimap, (int(cx * self.__MINIMAP_SCALE_FACTOR), int(cy * self.__MINIMAP_SCALE_FACTOR)), int(self.__width * self.__MINIMAP_SCALE_FACTOR / 2), self.__COLOR_RED, 0)
        # robot body (as a circle so we don't have to rotate anything)
        self.__rotator.translate_forward(self.__camera_offset)
        cx, cy = self.__rotator.get_current_position()
        cv2.circle(tmp_minimap, (int(cx * self.__MINIMAP_SCALE_FACTOR), int(cy * self.__MINIMAP_SCALE_FACTOR)), int(self.__width / 2 * self.__MINIMAP_SCALE_FACTOR / 2), self.__COLOR_RED, -1)
        self.__rotator.translate_forward(-self.__camera_offset)
        cv2.imshow("Minimap", tmp_minimap)

    def handle_interactive_mode(self, key):
        """
        Process key commands:
        k: Quit
        p: Pause/Unpause simulation
        w,a,s,d: Translate/Move Robot
        q,e: Rotate Robot
        """
        self.__show_minimap()

        if key == ord('k'):
            # quit
            raise KeyboardInterrupt()

        if key == ord('p'):
            # pause and unpause
            self.__paused = not self.__paused
            time.sleep(0.5)

        if self.__paused:
            if key == ord('a'):
                # left
                self.__translate_right(-50)

            if key == ord('s'):
                # backwards
                self.__rotator.translate_forward(50)

            if key == ord('d'):
                # right
                self.__translate_right(50)

            if key == ord('w'):
                # forward
                self.__rotator.translate_forward(-50)

            if key == ord('q'):
                # rotate left
                self.__rotate(-10.0, 0)

            if key == ord('e'):
                # rotate right
                self.__rotate(10.0, 0)

    def __translate_right(self, offset):
        self.__rotator.change_angle(90.0)
        self.__rotator.translate_forward(-offset)
        self.__rotator.change_angle(-90.0)

    def __rotate(self, angle_offset, angle_x_pos):
        # avoid rotation at the center of the camera view, but instead rotate at the robot center
        self.__rotator.translate_forward(self.__camera_offset)
        self.__translate_right(angle_x_pos)
        self.__rotator.change_angle(angle_offset)
        self.__translate_right(-angle_x_pos)
        self.__rotator.translate_forward(-self.__camera_offset)

    def __move(self):
        # delta_x_normiert: delta X Position zwischen Zentrum des Roboters und Rotationszentrum der Lenkbewegung normiert auf Maximalgeschwindigkeit:
        # delta_x_normiert = ((|v_left| - |v_right|) / V_MAX) * (w_robot / 2)
        delta_x_normiert = (abs(self.__left_speed) - abs(self.__right_speed)) / 100 * self.ROBOT_WIDTH / 2
        if abs(self.__left_speed) < abs(self.__right_speed):
            delta_x_normiert = -abs(delta_x_normiert)
        if delta_x_normiert > self.ROBOT_WIDTH / 2:
            delta_x_normiert = self.ROBOT_WIDTH / 2
        if delta_x_normiert < -self.ROBOT_WIDTH / 2:
            delta_x_normiert = -self.ROBOT_WIDTH / 2

        # phi: Drehwinkel pro delta_t (geht als frei gewählter SPEED_FACTOR ein):
        # phi = ((v_left - v_right) * SPEED_FACTOR) / w_robot
        phi = ((self.__left_speed - self.__right_speed) * self.SPEED_FACTOR) / self.ROBOT_WIDTH
        if phi > 180.0:
            phi = 180.0
        if phi < -180.0:
            phi = -180.0

        # Rotationszentrum um delta_x_normiert in x-Richtung (rechts) verschieben und um phi Grad im Uhrzeigersinn rotieren:
        self.__rotate(phi, delta_x_normiert)

        # Rotieren würde eigentlich ausreichen. Für gerade Bewegungen (keine Kreisbahn) läge allerdings das Rotationszentrum unendlich weit weg
        # (delta_x = unendlich). Des Weiteren erlaubt Rotator.py nicht das Verlassen des Parcours, wodurch wir auch keine Rotationszentren außerhalb
        # des Parcours wählen können. Aus diesem Grund wird die Translationskomponente einzeln angewendet:

        # max_phi: Drehwinkel, ab dem es keine Translationskomponente mehr gibt:
        # max_phi = (V_MAX * SPEED_FACTOR) / w_robot
        max_phi = (100 * self.SPEED_FACTOR) / self.ROBOT_WIDTH

        # total_v: Geschwindigkeit ohne Rotationskomponente
        # total_v = ((v_left + v_right) / 2) / V_MAX * SPEED_FACTOR
        total_v = (self.__left_speed + self.__right_speed) / 2 / 100 * self.SPEED_FACTOR
        max_v = 100 * self.SPEED_FACTOR
        if total_v > max_v:
            total_v = max_v
        if total_v < -max_v:
            total_v = -max_v

        # speed: Translationskomponente abzüglich der Rotationskomponente
        # speed = total_v * (max_phi - |phi|)
        speed = total_v * (max_phi - abs(phi))

        # Translation in -y-Richtung (nach oben) um speed Pixel
        self.__rotator.translate_forward(-speed)

    def get_frame(self) -> np.array:
        """
        returns 3d numpy array with color space bgr
        """
        if not self.__paused:
            self.__move()
        return self.__rotator.get_frame()

    def __get_speed_with_intertia(self, last_update_millis, previous_speed, actual_speed):
        previous_update = last_update_millis
        now = time.time() * 1000
        time_diff_ms = 1 + now - previous_update
        if previous_speed < actual_speed:
            if abs(previous_speed - actual_speed) / time_diff_ms > self.MAXIMUM_ACCELERATION:
                return previous_speed + self.MAXIMUM_ACCELERATION * time_diff_ms
            else:
                return actual_speed
        else:
            if abs(previous_speed - actual_speed) / time_diff_ms > self.MAXIMUM_DECELERATION:
                return previous_speed - self.MAXIMUM_DECELERATION * time_diff_ms
            else:
                return actual_speed

    def set_left_speed(self, speed: int):
        """
        Set the speed and direction of the left motor.
        speed: -100..100 in percent, where 100 is the maximum default "FORWARD" speed,
            -100 is the maximum default "BACKWARD" speed and 0 is the minimum speed.
        """
        if speed is None:
            raise ValueError('left_speed must be set')
        if type(speed) is not int:
            raise TypeError('left_speed must be an instance of int')
        if self.__last_speed_update_left is None:
            self.__last_speed_update_left = time.time() * 1000
        self.__left_speed = self.__get_speed_with_intertia(self.__last_speed_update_left, self.__left_speed, speed)
        self.__last_speed_update_left = time.time() * 1000

    def set_right_speed(self, speed: int):
        """
        Set the speed and direction of the right motor.
        speed: -100..100 in percent, where 100 is the maximum default "FORWARD" speed,
            -100 is the maximum default "BACKWARD" speed and 0 is the minimum speed.
        """
        if speed is None:
            raise ValueError('right_speed must be set')
        if type(speed) is not int:
            raise TypeError('right_speed must be an instance of int')
        if self.__last_speed_update_right is None:
            self.__last_speed_update_right = time.time() * 1000
        self.__right_speed = self.__get_speed_with_intertia(self.__last_speed_update_right, self.__right_speed, speed)
        self.__last_speed_update_right = time.time() * 1000

    def close(self):
        """
        Clean up system resources.
        """
        cv2.destroyAllWindows()
