import numpy as np

"""
Pseudo interface for a camera.
Function stubs may be implemented by either a real camera driver or a simulator.
"""
class ICamera:

    def __init__(self):
        """
        Initialize camera for capturing frames.
        """
        pass

    def get_frame(self) -> np.array:
        """
        returns 3d numpy array with color space bgr
        """
        pass

    def close(self):
        """
        Clean up system resources.
        """
        pass
