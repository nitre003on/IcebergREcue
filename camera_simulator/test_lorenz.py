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
PATH = './parcours_warm_RESIZED.JPG'

LINKER_INDEX = 4
RECHTER_INDEX = 10

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
    simulator = Simulator(PATH, start_x, start_y, PIXEL_BREITE, PIXEL_HOEHE, kamera_hoehe, kamera_position)
    # Geschwindigkeit der simulierten Bewegung anpassen:
    #simulator.ROTATIOM_FACTOR = 0.01
    #simulator.SPEED_FACTOR = 0.1
    # Trägheit des Roboters anpassen:
    #MAXIMUM_ACCELERATION = 0.2
    #MAXIMUM_DECELERATION = 1

    kamera = simulator
    motoren = simulator

    while True:
        dieser_frame = kamera.get_frame()
        gray = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)
        line = gray[-40:-20,:]
        _,binary = cv2.threshold(line,120,255,cv2.THRESH_BINARY_INV)
        teile = [binary[:,i*20:(i+1)*20].sum()/255 for i in range(15)]

        if sum(teile) == 0:
            print('No line on Sensor')
            motoren.set_speed(30, 30)

        else:
            '''
            summe = sum(teile)
            teile = [i/summe for i in teile]
            richtung = 0
            for i in range(15):
                richtung += i*teile[i]
            richtung = int(richtung)
            print(int(richtung))
            '''

            links, rechts = teile[LINKER_INDEX],teile[RECHTER_INDEX]
            print(links,rechts)
            if links > 200:
                cv2.rectangle(dieser_frame,(20*LINKER_INDEX,200),(20*(LINKER_INDEX+1),180),(0, 0, 255),3)
            else:
                cv2.rectangle(dieser_frame,(20*LINKER_INDEX,200),(20*(LINKER_INDEX+1),180),(0,0,0),3)

            if rechts > 200:
                cv2.rectangle(dieser_frame,(20*RECHTER_INDEX,200),(20*(RECHTER_INDEX+1),180),(0, 0, 255),3)
            else:
                cv2.rectangle(dieser_frame,(20*RECHTER_INDEX,200),(20*(RECHTER_INDEX+1),180),(0,0,0),3)

            if links > 200 and not rechts > 200:
                motoren.set_speed(-100, 100)

            elif not links > 200 and rechts > 200:
                motoren.set_speed(100, -100)

            else:
                motoren.set_speed(70, 70)



            #cv2.line(dieser_frame,(160,200),(20*int(richtung)+7,90),(255,0,0),3)

            '''
            if richtung < 3:
                motoren.set_speed(-50, 50)
            if 3 <= richtung and richtung < 6:
                motoren.set_speed( -15, 50)
            if 8 >= richtung and richtung >= 6:
                motoren.set_speed( 50, 50)
            if 8 < richtung and richtung <= 11:
                motoren.set_speed(50, -15)
            if 11 < richtung:
                motoren.set_speed(50, -50)
            '''

        #cv2.imshow('line', binary)
        cv2.imshow('TEST', dieser_frame)
        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
