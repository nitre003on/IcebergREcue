from ICamera import ICamera
import numpy as np

"""
Pseudo interface for an image rotator and translator.
"""
class IRotator(ICamera):

    def __init__(self, path: str, width: int, height: int):
        """
        Initialize the Rotator instance.
        path: Absolute path to the image file.
        width: width of the cropped area in pixels.
        height: height of the cropped area in pixels.
        """
        pass

    def change_angle(self, offset: float):
        '''
        Changes the view angle
        expects a float between -180 and 180
        '''
        pass

    def translate_forward(self, offset: float):
        '''
        Changes the translation in view-direction
        expects a float
        '''
        pass

    def get_field(self) -> np.array:
        """
        return self.picture
        """
        pass

    def get_current_position(self) -> np.array:
        """
        Return x from left in pixels, y from top in pixels of current position on the image.
        """
        pass
