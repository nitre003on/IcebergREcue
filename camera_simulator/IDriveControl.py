"""
Pseudo interface for motor control.
Function stubs may be implemented by a real motor driver or a simulator.
"""
class IDriveControl:

    def __init__(self):
        """
        Initialize drive control using a left and a right motor.
        """
        pass

    def set_left_speed(self, speed: int):
        """
        Set the speed and direction of the left motor.
        speed: -100..100 in percent, where 100 is the maximum default "FORWARD" speed,
            -100 is the maximum default "BACKWARD" speed and 0 is the minimum speed.
        """
        pass

    def set_right_speed(self, speed: int):
        """
        Set the speed and direction of the right motor.
        speed: -100..100 in percent, where 100 is the maximum default "FORWARD" speed,
            -100 is the maximum default "BACKWARD" speed and 0 is the minimum speed.
        """
        pass

    def set_speed(self, left_speed: int, right_speed: int):
        """
        Set the speed and direction of the left and right motor.
        speed: -100..100 in percent, where 100 is the maximum default "FORWARD" speed,
            -100 is the maximum default "BACKWARD" speed and 0 is the minimum speed.
        """
        self.set_left_speed(left_speed)
        self.set_right_speed(right_speed)

    def close(self):
        """
        Clean up system resources.
        """
        pass
