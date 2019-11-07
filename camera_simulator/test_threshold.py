"""
Demonstriert die Konvertierung von BGR in GRAY
und die anschließende Binarisierung an einem Schwellenwert (aka Maskierung).

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

        #########################################
        # Konvertierung in Binary mit threshold #
        #########################################
        # Kopie von dieser_frame in Graustufen konvertieren
        frame_graustufen = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)
        # alle Werte in dieser_frame bei Schwellenwert 120 in 0 oder 255 zerteilen, Bild invertieren
        _, frame_schwarz_weiss = cv2.threshold(frame_graustufen, 120, 255, cv2.THRESH_BINARY_INV)
        # alle Werte in dieser_frame bei Schwellenwert 120 in 0 oder 1 zerteilen, Bild invertieren
        _, frame_schwarz_weiss2 = cv2.threshold(frame_graustufen, 120, 1, cv2.THRESH_BINARY_INV)
        # alle Werte in dieser_frame bei Schwellenwert 120 in 0 oder 255 zerteilen
        _, frame_schwarz_weiss3 = cv2.threshold(frame_graustufen, 120, 255, cv2.THRESH_BINARY)
        # alle Werte in dieser_frame bei Schwellenwert 120 in 0 oder 1 zerteilen
        _, frame_schwarz_weiss4 = cv2.threshold(frame_graustufen, 120, 1, cv2.THRESH_BINARY)

        # Kamerabild anzeigen
        cv2.imshow("Maze Runner", frame_schwarz_weiss)

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
