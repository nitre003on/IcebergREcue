"""
Demonstriert die Konvertierung von BGR in GRAY
und die anschließende Binarisierung an einem Schwellenwert (aka Maskierung).
Danach werden einzelne Teile der Maske herausgeschnitten und deren
enthaltene Werte aufsummiert.
Die ausgeschnittenen Bereiche sind im Bild mit roten Rechtecken markiert.
Ist die Mehrheit eines Bereichs über schwarz, wird das Rechteck grün dargestellt.

Steuerung:
Pausieren mit p,
bewegen mit w,a,s,d,
rotieren mit q,e,
beenden mit k

Einstellungen:
PIXEL_BREITE, PIXEL_HOEHE: Auflösung des Kamerabilds. Lieber nicht verändern, da alle
Positionen im Kamerabild mit Konstanten gehardcoded sind.
PARCOURS_PFAD: Pfad zum Parcours-Bild. Zur Auswahl stehen momentan:
    - parcours_cold_RESIZED.JPG und
    - parcours_warm_RESIZED.JPG
kamera_position: "Größe des Roboters" - Abstand der Kamera zum Rotationszentrum des Roboters
kamera_hoehe: Skalierung des Parcours und damit Simulation der Montagehöhe der Kamera (schaut senkrecht nach unten)
start_x, start_y: Startposition auf dem Parcours
simulator.ROBOT_WIDTH: Abstand der Fahrketten voneinander
simulator.SPEED_FACTOR: Fahr- und Rotationsgeschwindigkeit des Roboters
simulator.MAXIMUM_ACCELERATION, simulator.MAXIMUM_DECELERATION: Trägheit des Roboters
"""

from Simulator import Simulator
import time
from cv2 import cv2
import numpy

#
# Einstellungen
#
PIXEL_BREITE = 320
PIXEL_HOEHE = 240
PARCOURS_PFAD = './parcours_cold_RESIZED.JPG'

#
# 3...2...1 GO!!
#
try:
    # Abstand der Kamera vom Rotationszentrum des Roboters in Pixel:
    # 500 ist halbwegs realistisch, aber da dieser Parcours wesentlich gedrungener daher-
    # kommt als ein echter, ist es denke ich OK wenn man hier auf 300 runter geht.
    kamera_position = 300
    # Skalierungsfaktor für den Parcours (simuliert die Höhe, in der die Kamera montiert ist):
    # Ich denke 0.7 ist halbwegs realistisch.
    kamera_hoehe = 0.7
    start_x = 260
    start_y = 2850
    simulator = Simulator(PARCOURS_PFAD, start_x, start_y, PIXEL_BREITE, PIXEL_HOEHE, kamera_hoehe, kamera_position)
    # Breite des Roboters anpassen:
    #simulator.ROBOT_WIDTH = 200
    # Geschwindigkeit der simulierten Bewegung anpassen:
    #simulator.SPEED_FACTOR = 5.0
    # Trägheit des Roboters anpassen:
    #simulator.MAXIMUM_ACCELERATION = 0.2
    #simulator.MAXIMUM_DECELERATION = 1

    # wird zum Testen mit dem richtigen Roboter durch die echte PiCam ersetzt
    kamera = simulator

    # wird zum Testen mit dem richtigen Roboter durch das AFMotorShield ersetzt
    motoren = simulator

    # CPU quälen:
    while True:
        # frame lesen
        dieser_frame = kamera.get_frame()

        ####################################
        # Summierung                       #
        ####################################

        # Kopie von dieser_frame in Graustufen konvertieren
        frame_graustufen = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)

        schwelle = 120
        # alle Werte in dieser_frame bei Schwellenwert schwelle in 0 oder 255 zerteilen, Bild invertieren
        _, linien_maske = cv2.threshold(frame_graustufen, schwelle, 255, cv2.THRESH_BINARY_INV)

        h = 50 # Höhe
        b = 50 # Breite
        start1 = (int(100), int(100))
        ende1 = (int(start1[0] + b), int(start1[1] + h))
        start2 = (int(200), int(100))
        ende2 = (int(start2[0] + b), int(start2[1] + h))

        # Rechteck von oben links (x=100, y=100) bis unten rechts (x=150, y=150) ausschneiden:
        roi_links = linien_maske[start1[1]:ende1[1], start1[0]:ende1[0]]
        # Rechteck von oben links (x=200, y=100) bis unten rechts (x=250, y=150) ausschneiden:
        roi_rechts = linien_maske[start2[1]:ende2[1], start2[0]:ende2[0]]

        summe_links = roi_links.sum() / 255
        summe_rechts = roi_rechts.sum() / 255

        # Maximale Pixel, die innerhalb der ROI auslösen können:
        max = h * b
        #print([max, summe_links, summe_rechts])
        # wir erkennen die Linie, wenn mehr als die Hälte im Bild schwarz ist:
        SCHWARZ_FAKTOR = 0.5
        schwarz = max * SCHWARZ_FAKTOR

        ROT = (0, 0, 255)
        GRUEN = (0, 255, 0)
        if summe_links > schwarz:
            cv2.rectangle(dieser_frame, start1, ende1, GRUEN, 2)
        else:
            cv2.rectangle(dieser_frame, start1, ende1, ROT, 2)

        if summe_rechts > schwarz:
            cv2.rectangle(dieser_frame, start2, ende2, GRUEN, 2)
        else:
            cv2.rectangle(dieser_frame, start2, ende2, ROT, 2)

        # Kamerabild anzeigen
        cv2.imshow("Maze Runner", dieser_frame)

        # Motoren ansteuern
        motoren.set_speed(30, 30)

        # Pausieren mit p, bewegen mit w,a,s,d, rotieren mit q,e, beenden mit k
        # wird zum testen mit dem richtigen Roboter ersetzt durch cv2.waitKey(10)
        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
