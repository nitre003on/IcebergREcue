"""
Leere Simulationsumgebung.
Instanziiert ein Objekt der Simulator-Klasse.
kamera und motoren sind Referenzen auf dieses eine Objekt.

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
from enum import Enum
from operator import itemgetter

#
# Einstellungen
#
PIXEL_BREITE = 320
PIXEL_HOEHE = 240
PARCOURS_PFAD = './parcours_warm_RESIZED.JPG'

#
# Farben
#
GRUEN = (0, 255, 0)
GELB = (0,255,255)
ROT = (0, 0, 255)
BLAU = (255, 0, 0)

#
# Kalibrierung
#
helligkeits_schwelle = 110
#                                    H   S   V
gruen_untere_schwelle = numpy.uint8([40, 80, 20])
gruen_obere_schwelle = numpy.uint8([80, 255, 255])
SLICE_HOEHE_FUER_GRUEN = 120
SLICE_HOEHE_FUER_SCHWARZ = 30
LENKEN_IGNORIEREN = 5
FAHRGESCHWINDIGKEIT = 60

#
# Laufzeitvariablen
#
praeferierte_linie = (False, 0)

def center_line(dieser_frame):
    cv2.line(dieser_frame,(int((PIXEL_BREITE-1)/2),0),(int((PIXEL_BREITE-1)/2),PIXEL_HOEHE-1),GELB,1)

def rechteck_zentrum(x, y, w, h):
    return (x+w/2, y+h/2)

def kreuzungen_erkennen(dieser_frame, gruene_maske):
    markierungen = []
    _, konturen, _ = cv2.findContours(gruene_maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for kontur in konturen:
        if cv2.contourArea(kontur) > 2000:
            x, y, w, h = cv2.boundingRect(kontur)
            if y > PIXEL_HOEHE - SLICE_HOEHE_FUER_GRUEN:
                farbe = ROT
                markierungen.append(rechteck_zentrum(x, y, w, h))
            else:
                farbe = BLAU
            cv2.rectangle(dieser_frame, (x, y), (x + w, y + h), farbe, 2)
    return markierungen

class Richtung(Enum):
    GERADEAUS = 1
    LINKS = 2
    RECHTS = 3
    WENDEN = 4

def kreuzung_abbiegen(markierungen):
    if len(markierungen) is 1:
        if markierungen[0][0] < PIXEL_BREITE / 2:
            print("kreuzung is Richtung.LINKS2")
            return Richtung.LINKS
        else:
            print("kreuzung is Richtung.RECHTS(LINKS)2")
            return Richtung.RECHTS
    elif len(markierungen) is 2:
        print("kreuzung is Richtung.WENDEN2")
        return Richtung.WENDEN
    else:
        print("kreuzubg is Richtung.GERADE2")
        return Richtung.GERADEAUS     

def linie_erkennen(dieser_frame, schwarze_maske, offset):
    yoffset = PIXEL_HOEHE - SLICE_HOEHE_FUER_SCHWARZ - offset - 1
    roi_line = schwarze_maske[yoffset: yoffset + SLICE_HOEHE_FUER_SCHWARZ, 0: PIXEL_BREITE - 1]
    _, konturen, _ = cv2.findContours(roi_line, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cx = 0
    cy = yoffset + SLICE_HOEHE_FUER_SCHWARZ/2
    cnt = 0
    farbe = GRUEN
    linien = []
    for kontur in konturen:
        x, y, w, h = cv2.boundingRect(kontur)
        if w > 50:
            if w >= PIXEL_BREITE-50:
                farbe = ROT
                ist_kreuzung = True
            else:
                farbe = GELB
                ist_kreuzung = False
            cv2.rectangle(dieser_frame, (x, y + yoffset), (x + w, y + yoffset + h), farbe, 2)
            cx = cx + int(x + w / 2)
            cnt = cnt + 1
            if ist_kreuzung:
                linien.append((True, cx - PIXEL_BREITE / 2))
            else:
                linien.append((False, cx - PIXEL_BREITE / 2))
    if cx is 0:
        cx = (PIXEL_BREITE - 1) / 2
    else:
        cx = cx / cnt
    cv2.circle(dieser_frame, (int(cx), int(cy)), 5, farbe, -1)
    return linien

def linie_aussuchen(dieser_frame, offset, linien_positionen):
    global praeferierte_linie
    if len(linien_positionen) is 0:
        praeferierte_linie = (False, 0)
    elif len(linien_positionen) is 1:
        praeferierte_linie = linien_positionen[0]
    else:
        abstaende = []
        for linie in linien_positionen:
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)
    return praeferierte_linie


#
# 3...2...1 GO!!
#
try:
    kamera_position = 300
    kamera_hoehe = 0.7
    start_x = 260
    start_y = 2850
    simulator = Simulator(PARCOURS_PFAD, start_x, start_y, PIXEL_BREITE, PIXEL_HOEHE, kamera_hoehe, kamera_position)
    #simulator.ROBOT_WIDTH = 200
    #simulator.SPEED_FACTOR = 5.0
    #simulator.MAXIMUM_ACCELERATION = 0.2
    #simulator.MAXIMUM_DECELERATION = 1

    kamera = simulator
    motoren = simulator

    while True:
        dieser_frame = kamera.get_frame()
        gray = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2HSV)

        _, schwarze_maske = cv2.threshold(gray, helligkeits_schwelle, 255, cv2.THRESH_BINARY_INV)
        gruene_maske = cv2.inRange(hsv, gruen_untere_schwelle, gruen_obere_schwelle)
        schwarze_maske = schwarze_maske - gruene_maske

        kreuzung = kreuzung_abbiegen(kreuzungen_erkennen(dieser_frame, gruene_maske))
        #print(kreuzung)
        linien_positionen = linie_erkennen(dieser_frame, schwarze_maske, 0)
        linien_position = linie_aussuchen(dieser_frame, 0, linien_positionen)
        #print(linien)
        center_line(dieser_frame)
        cv2.imshow("Maze Runner", dieser_frame)

        if linien_position[1] < -LENKEN_IGNORIEREN:
            motoren.set_speed(0, FAHRGESCHWINDIGKEIT)
        elif linien_position[1] > LENKEN_IGNORIEREN:
            motoren.set_speed(FAHRGESCHWINDIGKEIT, 0)
        else:
            if kreuzung is Richtung.LINKS:
                motoren.set_speed(0, FAHRGESCHWINDIGKEIT)
                print("kreuzung is Richtung.LINKS")
            elif kreuzung is Richtung.RECHTS:
                #müsste es nicht Richtung.RECHTS sein?                                                                                          ?
                motoren.set_speed(FAHRGESCHWINDIGKEIT, 0)
                print("kreuzung is Richtung.RECHTS(LINKS)")
            elif kreuzung is Richtung.WENDEN:
                motoren.set_speed(FAHRGESCHWINDIGKEIT, -FAHRGESCHWINDIGKEIT)
                print("kreuzung is Richtung.WENDEN")
            else:
                motoren.set_speed(FAHRGESCHWINDIGKEIT, FAHRGESCHWINDIGKEIT)
                print("kreuzubg is Richtung.GERADE")

        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
    