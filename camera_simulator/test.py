from Simulator import Simulator
import time
from cv2 import cv2
import numpy
import collections

#
# Einstellungen
#
PIXEL_BREITE = 320
PIXEL_HOEHE = 240
FRAMERATE = 32 # Bilder/Sekunde
PARCOURS_PFAD = './parcours_cold_RESIZED.JPG'

#                                H  S  V
black_lower_limit = numpy.uint8([0, 0, 0])
black_upper_limit = numpy.uint8([255, 50, 100])
#                                R  G  B
#black_lower_limit = numpy.uint8([0, 0, 0])
#black_upper_limit = numpy.uint8([50, 50, 50])
#                                H  S  V
green_lower_limit = numpy.uint8([40, 80, 20])
green_upper_limit = numpy.uint8([80, 255, 255])
#bla
GRUEN = (0, 255, 0)
GELB = (0,255,255)
ROT = (0, 0, 255)

def line_slice(roi_kreuzung, dieser_frame, offset):
    yoffset = PIXEL_HOEHE-(PIXEL_HOEHE-200)-20 - offset
    roi_line = dieser_frame[PIXEL_HOEHE - 20 - offset:PIXEL_HOEHE - 1 - offset, 0:PIXEL_BREITE - 1]
    hsv = cv2.cvtColor(roi_line, cv2.COLOR_BGR2HSV)
    black_mask = cv2.inRange(hsv, black_lower_limit, black_upper_limit)
    _, konturen, _ = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cx = 0
    cy = yoffset+5
    cnt = 0
    farbe = GRUEN
    ret = []
    is_kreuzung = False
    for kontur in konturen:
        x, y, w, h = cv2.boundingRect(kontur)
        if w > 10:
            if w > 150:
                farbe = ROT
                is_kreuzung = True
            else:
                farbe = GRUEN
            cv2.rectangle(roi_kreuzung, (x, y+yoffset), (x + w, y+yoffset + h), farbe, 2)
            cx = cx + int(x + w / 2)
            cnt = cnt+1
            if is_kreuzung:
                ret.append(0)
            else:
                ret.append(cx - PIXEL_BREITE / 2)
    if cx is 0:
        cx = (PIXEL_BREITE - 1) / 2
    else:
        cx = cx / cnt
    cv2.circle(roi_kreuzung, (int(cx), int(cy)), 5, farbe, -1)
    return ret

def center_line(roi_kreuzung):
    cv2.line(roi_kreuzung,(int((PIXEL_BREITE-1)/2),0),(int((PIXEL_BREITE-1)/2),PIXEL_HOEHE-1),GELB,1)

def green_squares(roi_kreuzung):
    hsv2 = cv2.cvtColor(roi_kreuzung, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv2, green_lower_limit, green_upper_limit)

    _, konturen, _ = cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for kontur in konturen:
        if cv2.contourArea(kontur) > 4000:
            x, y, w, h = cv2.boundingRect(kontur)
            cv2.rectangle(roi_kreuzung, (x, y), (x + w, y + h), (255, 0, 0), 2)

#
# 3...2...1 GO!!
#
try:
    # Abstand der Kamera vom Rotationszentrum des Roboters in Pixel:
    # 500 ist halbwegs realistisch, aber da dieser Parcours wesentlich gedrungener daher-
    # kommt als ein echter, ist es denke ich OK wenn man hier auf 300 runter geht.
    kamera_position = 500
    # Skalierungsfaktor für den Parcours (simuliert die Höhe, in der die Kamera montiert ist):
    # Ich denke 0.7 ist halbwegs realistisch.
    kamera_hoehe = 0.7
    start_x = 260
    start_y = 2850
    simulator = Simulator(PARCOURS_PFAD, start_x, start_y, PIXEL_BREITE, PIXEL_HOEHE, kamera_hoehe, kamera_position)
    # Geschwindigkeit der simulierten Bewegung anpassen:
    #simulator.ROTATIOM_FACTOR = 0.01
    #simulator.SPEED_FACTOR = 0.1
    # Trägheit des Roboters anpassen:
    #MAXIMUM_ACCELERATION = 0.2
    #MAXIMUM_DECELERATION = 1

    # wird zum Testen mit dem richtigen Roboter durch die echte PiCam ersetzt
    kamera = simulator

    # wird zum Testen mit dem richtigen Roboter durch das AFMotorShield ersetzt
    motoren = simulator

    # CPU quälen:
    while True:
        # frame lesen
        dieser_frame = kamera.get_frame()
        roi_kreuzung = dieser_frame[PIXEL_HOEHE - 200:PIXEL_HOEHE - 1, 0:PIXEL_BREITE - 1]
        green_squares(roi_kreuzung)
        line_slice(roi_kreuzung, dieser_frame, 30)
        line_slice(roi_kreuzung, dieser_frame, 90)
        lines = line_slice(roi_kreuzung, dieser_frame, 150)
        center_line(roi_kreuzung)

        the_line = 1000
        for a_line in lines:
            if abs(a_line) < the_line:
                the_line = a_line
        if the_line is 1000:
            the_line = 0
        if the_line > 0:
            left_speed = 100
            right_speed = 0
        elif the_line < 0:
            left_speed = 0
            right_speed = 100
        else:
            left_speed = 50
            right_speed = 50

        if left_speed > 100:
            left_speed = 100
        if left_speed < -100:
            left_speed = -100
        if right_speed > 100:
            right_speed = 100
        if right_speed < -100:
            right_speed = -100
        #print([left_speed, right_speed])

        # Kamerabild anzeigen
        cv2.imshow("Maze Runner", roi_kreuzung)

        # Motoren ansteuern
        motoren.set_speed(left_speed, right_speed)

        # Pausieren mit p, bewegen mit w,a,s,d, rotieren mit q,e, beenden mit k
        # wird zum testen mit dem richtigen Roboter ersetzt durch cv2.waitKey(10)
        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
