from IRotator import IRotator
from ICamera import ICamera
import numpy as np
from cv2 import cv2

"""
Takes an image and performs rotation and translation actions on a cropped out area.
"""
class Rotator(IRotator, ICamera):

    def __init__(self, path, width, height, start_x: int, start_y: int, image_resize_factor = 1.0):
        """
        Initialize the Rotator instance.
        path: Absolute path to the image file.
        width: width of the cropped area in pixels.
        height: height of the cropped area in pixels.
        start_x: start position from left side in pixels.
        start_y: start position from top in pixels.
        image_resize_factor: image resize factor (default: 1.0)
        """
        self.crop_dimension = max(width, height)
        self.aspect_ratio_diff = abs(width - height)

        # Start position on the plane
        self.pos = np.array([(self.crop_dimension / 2 + start_y) * image_resize_factor, (self.crop_dimension / 2 + start_x) * image_resize_factor], dtype=float)
        # Start viewangle on the plane
        self.angle = 0

        # picture to rotate over
        original_picture = cv2.imread(path)
        # choose preferred interpolation method
        if (image_resize_factor > 1.0):
            self.picture = cv2.resize(original_picture, dsize=None, fx=image_resize_factor, fy=image_resize_factor, interpolation = cv2.INTER_CUBIC)
        elif (image_resize_factor < 1.0):
            self.picture = cv2.resize(original_picture, dsize=None, fx=image_resize_factor, fy=image_resize_factor, interpolation=cv2.INTER_AREA)
        else:
            self.picture = original_picture

        # save width (cols) and height (rows) in pixel
        self.rows,self.cols,_ = self.picture.shape

        # Add additional border to avoid index problems when translating close to the edge of the image:
        # new gray image bigger than self.picture by the crop dimensions self.crop_dimension:
        # BGR-color: (128, 128, 128) -> gray
        self.borderd_picture = np.ones((self.rows + 2 * self.crop_dimension, self.cols + 2 * self.crop_dimension, 3), dtype=self.picture.dtype) * 128
        # Place original in the middle of the bigger gray image:
        self.borderd_picture[self.crop_dimension:self.rows+self.crop_dimension, self.crop_dimension:self.cols+self.crop_dimension] = self.picture

    # override
    def get_frame(self) -> np.array:
        # calculate the ROI points around self.pos
        x_0, x_1, y_0, y_1 = self.calculate_ROI()

        # add border to the ROI
        y_0 += int(self.crop_dimension/2)
        x_0 += int(self.crop_dimension/2)
        y_1 += int(self.crop_dimension*3/2)
        x_1 += int(self.crop_dimension*3/2)

        # crop out and copy of the area surrounding self.pos plus a border
        frame_to_rotate = self.borderd_picture[y_0:y_1, x_0:x_1].copy()

        # rotate the frame to the given viewangle and extract the resultframe
        shape = frame_to_rotate.shape
        rotation = cv2.getRotationMatrix2D((shape[0] / 2, shape[1] / 2), self.angle, 1)

        # avoid overflow
        self.avoid_overflow()

        # Perform actual rotation on cropped part of the image using the rotation matrix.
        # This will cut off parts of the image that don't fit a recangular bound (worst case: 45° rotation).
        # This is why we added a border to the cropped out area.
        result = cv2.warpAffine(frame_to_rotate, rotation, (self.cols, self.rows))
        # crop out the actual area of self.crop_dimension, cutting away the border
        return result[int(self.crop_dimension/2 + self.aspect_ratio_diff):int(self.crop_dimension*3/2),int(self.crop_dimension/2):int(self.crop_dimension*3/2)]

    def get_field(self) -> np.array:
        """
        Returns the entire picture.
        """
        return self.picture

    def get_current_position(self) -> np.array:
        """
        Return x from left in pixels, y from top in pixels of current position on the image.
        """
        return self.pos[1], self.pos[0]

    def change_angle(self, offset: float):
        '''
        Turns the viewport by a given angle
        '''
        if offset > 180 or offset < -180:
            raise ValueError('offset out of range [-180, 180]')
        self.angle += offset

    def translate_forward(self, offset: float):
        '''
        Moves forward on the plane from self.pos in the direction of self.angle by offset
        in pixels. Negative values translate backwards.
        '''
        rad_ang = np.deg2rad(self.angle)
        rotation = np.array([[np.cos(rad_ang),-np.sin(rad_ang)],[np.sin(rad_ang),np.cos(rad_ang)]])
        einheits_vektor = np.array([1,0])
        # pos = E1 * ROTATE * scale + pos
        self.pos += (np.dot(einheits_vektor, rotation) * offset)

    def avoid_overflow(self):
        '''
        Avoids overflow when rotating
        -> if you move close to a border in the image you won't be able to move forward any further
        '''
        self.pos[0] = max(1 + self.crop_dimension/2, self.pos[0])
        self.pos[0] = min(self.picture.shape[0] - self.crop_dimension/2 -1, self.pos[0])
        self.pos[1] = max(1 + self.crop_dimension/2 , self.pos[1])
        self.pos[1] = min(self.picture.shape[1] - self.crop_dimension/2 -1, self.pos[1])

    def calculate_ROI(self):
        """
        crop out the area around self.pos
        """
        x_0 = int(self.pos[1] - self.crop_dimension/2)
        x_1 = int(self.pos[1] + self.crop_dimension/2)
        y_0 = int(self.pos[0] - self.crop_dimension/2)
        y_1 = int(self.pos[0] + self.crop_dimension/2)
        return x_0,x_1,y_0,y_1
