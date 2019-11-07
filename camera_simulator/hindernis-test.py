from picamera import PiCamera
import time
import cv2
import numpy
from enum import Enum
from operator import itemgetter
import board
import busio
import adafruit_lsm303
import adafruit_l3gd20
from kkos.afmotorshield import *
import math
import adafruit_vl53l0x

TOF_SENSOR_ADDRRESSE = 0x29
i2c_bus = busio.I2C(board.SCL, board.SDA)
tof_sensor = adafruit_vl53l0x.VL53L0X(i2c_bus, address=TOF_SENSOR_ADDRRESSE)
tof_sensor.measurement_timing_budget = 20000
abstand = tof_sensor.range

def HINDERNIS():
    if abstand > 300:
        print("Abstand=%smm" % (abstand))
    else:
        pass

try:
    while True:
        HINDERNIS()
finally:
    pass