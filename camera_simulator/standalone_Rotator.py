import cv2
import numpy as np

def avoid_overflow(pos, max_x, max_y):
    pos[0] = int(max(0 + max_y/2, pos[0]))
    pos[0] = int(min(rows - max_y/2, pos[0]))
    pos[1] = int(max(0 + max_x/2 , pos[1]))
    pos[1] = int(min(cols - max_x/2, pos[1]))
    return pos

def calculate_ROI(pos, max_x, max_y):
    x_0 = int(pos[1] - MAX_X/2)
    x_1 = int(pos[1] + MAX_X/2)

    y_0 = int(pos[0] - MAX_Y/2)
    y_1 = int(pos[0] + MAX_Y/2)
    return x_0,x_1,y_0,y_1

MAX_Y = 200
MAX_X = 200

# Position on the Plane
pos = np.array([MAX_Y / 2, MAX_X / 2], dtype=int)
# Viewangle on the Plane
angle = 0
## Amount of pixels to travel on the Plane
#scale = 10

# Load the Parcour image
parcour = cv2.imread('../Bilder/6.jpg')
rows,cols,_ = parcour.shape

# Create a copy of the parcour and add a grey border
# this copy is used for rotation to avoid indexoverflows 
parcour_with_border = np.ones((rows + 2*MAX_Y, cols + 2*MAX_X,3), dtype=parcour.dtype)*128
parcour_with_border[MAX_Y:rows+MAX_Y, MAX_X:cols+MAX_Y] = parcour.copy()

while 1:
    # calculate the points of the ROI on the X and Y axis
    x_0, x_1, y_0, y_1 = calculate_ROI(pos, MAX_X, MAX_Y)

    # translate ROI points to fith the bordered image
    y_0 += int(MAX_Y/2)
    x_0 += int(MAX_X/2)
    y_1 += int(MAX_Y*3/2)
    x_1 += int(MAX_X*3/2)
    
    
    ROI_for_rotation = parcour_with_border[y_0:y_1, x_0:x_1].copy()  

    # 
    shape = ROI_for_rotation.shape
    rotation = cv2.getRotationMatrix2D((shape[0]/2,shape[1]/2),angle,1)
    ROI_for_rotation = cv2.warpAffine(ROI_for_rotation,rotation,(cols,rows))

    rotated_ROI = ROI_for_rotation[int(MAX_Y/2):int(MAX_Y*3/2),int(MAX_X/2):int(MAX_X*3/2)]

    cv2.imshow('Rotated ausschnitt', rotated_ROI)

    key = cv2.waitKey(1)

    rad_ang = np.deg2rad(angle)
    motor_rotation = np.array([[np.cos(rad_ang),-np.sin(rad_ang)],[np.sin(rad_ang),np.cos(rad_ang)]])

    if key == ord('a'):
        pos += (np.dot(np.array([0,-1],dtype=np.float64),motor_rotation) * scale).astype(int)

    if key == ord('s'):
        pos += (np.dot(np.array([1,0],dtype=np.float64),motor_rotation) * scale).astype(int)

    if key == ord('d'):
        pos += (np.dot(np.array([0,1],dtype=np.float64),motor_rotation) * scale).astype(int)

    if key == ord('w'):
        pos += (np.dot(np.array([-1,0],dtype=np.float64),motor_rotation) * scale).astype(int)

    if key == ord('y'):
        angle += 5

    if key == ord('c'):
        angle -= 5

    if key == ord('q'):
        break

    pos = avoid_overflow(pos, MAX_X, MAX_Y)
