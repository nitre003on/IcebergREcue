"""
Demonstration der Nutzung von threshold im GRAYSCALE-Farbschema.

Simuliert 2 physische Reflektionssensoren.
Diese werden als 2 schwarze Quadrate dargestellt.
Erkennt einer der beiden "Sensoren" eine Linie, wird das Quadrat rot eingefärbt.

Das Beispielprogramm enthält keine Linienfolgen-Logik.
Es gibt die Zentren der gefundenen Linienstückchen des untersten Schnittes in der
Kommandozeile aus.
Es fährt schnell geradeaus, wenn mindestens 1 Linienfragment gesehen wird,
sonst langsam.

Steuerung:
Pausieren mit p,
bewegen mit w,a,s,d,
rotieren mit q,e,
beenden mit k

Einstellungen:
LINKER_INDEX, RECHTER_INDEX: X-Positionen der beiden "Helligkeitssensoren"
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
PARCOURS_PFAD = './parcours_warm_RESIZED.JPG'

# Position des linken Reflektionssensors
LINKER_INDEX = 4
# Position des rechten Reflektionssensors
RECHTER_INDEX = 10

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

    kamera = simulator
    motoren = simulator

    dir = None
    while True:
        dieser_frame = kamera.get_frame()
        # in Graustufen umwandeln
        gray = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)
        # einen Streifen herausschneiden
        line = gray[-40:-20,:]
        # Maske erstellen (Monochromes Bild: Linie weiß, alles andere schwarz)
        _, binary = cv2.threshold(line, 120, 255, cv2.THRESH_BINARY_INV)
        # Streifen segmentieren ("größere Pixel" erstellen /
        # die Auflösung stark heruntersetzen) und in Boolean umwandeln:
        # Schwarz entspricht 0 und weiß 255. Dividieren durch 255 führt zu
        # Schwarz(keine Linie) entspricht 0 und weiß(Linie) 1.
        teile = [binary[:,i*20:(i+1)*20].sum()/255 for i in range(15)]
        # Einen "Riesenpixel" links und einen rechts auswählen
        links, rechts = teile[LINKER_INDEX],teile[RECHTER_INDEX]

        if links > 200:
            # linker Sensor auf der Linie
            cv2.rectangle(dieser_frame,(20*LINKER_INDEX,200),(20*(LINKER_INDEX+1),180),(0, 0, 255),3)
        else:
            # linker Sensor nicht auf der Linie
            cv2.rectangle(dieser_frame,(20*LINKER_INDEX,200),(20*(LINKER_INDEX+1),180),(0,0,0),3)
        if rechts > 200:
            # rechter Sensor auf der Linie
            cv2.rectangle(dieser_frame,(20*RECHTER_INDEX,200),(20*(RECHTER_INDEX+1),180),(0, 0, 255),3)
        else:
            # rechter Sensor nicht auf der Linie
            cv2.rectangle(dieser_frame,(20*RECHTER_INDEX,200),(20*(RECHTER_INDEX+1),180),(0,0,0),3)

        if links <= 200 and rechts <= 200:
            # keine Linienstückchen gefunden
            print('No line on Sensor')
            motoren.set_speed(30, 30)
        else:
            # Linienstückchen gefunden
            # Helligkeitswerte der beiden "Sensoren" ausgeben, also die Summe aller
            # schwarzen Minipixel in einem Riesenpixel
            print(links, rechts)
            motoren.set_speed(50, 50)

        # Kamerabild anzeigen
        cv2.imshow('Maze Runner', dieser_frame)

        # Pausieren mit p, bewegen mit w,a,s,d, rotieren mit q,e, beenden mit k
        # wird zum testen mit dem richtigen Roboter ersetzt durch cv2.waitKey(10)
        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
