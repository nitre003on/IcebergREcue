
from picamera import PiCamera                                                                                                       #Libraries werden importiert
import time                                                                                                                         #
import cv2                                                                                                                          #
import numpy                                                                                                                        # 
from enum import Enum                                                                                                               #
from operator import itemgetter                                                                                                     #
import board                                                                                                                        #
import busio                                                                                                                        #
import adafruit_lsm303                                                                                                              #
import adafruit_l3gd20                                                                                                              #
import math                                                                                                                         #
import adafruit_vl53l0x                                                                                                             #

TOF_SENSOR_ADDRRESSE = 0x29                                                                                                         #TOF-stuff
i2c_bus = busio.I2C(board.SCL, board.SDA)                                                                                           #
tof_sensor = adafruit_vl53l0x.VL53L0X(i2c_bus, address=TOF_SENSOR_ADDRRESSE)                                                        #
tof_sensor.measurement_timing_budget = 20000                                                                                        #

PIXEL_BREITE = 320                                                                                                                  # Anzahl der Pixel auf der "x-Achse"
PIXEL_HOEHE = 240                                                                                                                   # Anzahl der Pixel auf der "y-Achse"

GRUEN = (0, 255, 0)                                                                                                                 # Farbe Grün wird definiert
GELB = (0,255,255)                                                                                                                  # Farbe Gelb wird definiert
ROT = (0, 0, 255)                                                                                                                   # Farbe Rot wird definiert
BLAU = (255, 0, 0)                                                                                                                  # Farbe Blau wird definiert

helligkeits_schwelle = 50                                                                                                           # Schwellwert für Schwarz wird gewählt
gruen_untere_schwelle = numpy.uint8([5, 80, 20])                                                                                   # unterer Schwellwert für Grün wird gewählt
gruen_obere_schwelle = numpy.uint8([89, 255, 200])                                                                                  # oberer Schwellwert für Grün wird gewählt
SLICE_HOEHE = 30                                                                                                                    # Höhe einer "Schicht"

SLICE_HOEHE_FUER_GRUEN = 180                                                                                                        # Höhe der "Schicht" für Grün                   !!!
SLICE_HOEHE_FUER_GRUEN_1 = 120

SLICE_HOEHE_FUER_SCHWARZ = 30                                                                                                       # Höhe der "Schicht" für linie_erkennen_unten
SLICE_HOEHE_FUER_SCHWARZ_1 = 30                                                                                                     # Höhe der "Schicht" für linie_erkennen_oben
SLICE_BREITE_FUER_SCHWARZ = 30                                                                                                      # Breite der "Schicht" für linie_erkennen_links
SLICE_BREITE_FUER_SCHWARZ_1 = 30                                                                                                    # Breite der "Schicht" für linie_erkennen_rechts

LENKEN_IGNORIEREN = 20                                                                                                              # Die Größe des Winkels, bei dem noch nicht gelenkt wird, wird gewählt

VOLLGAS = 100                                                                                                                       # Maximalgeschwindigkeit vorwärts wird gewählt 
VOLLGAS_R = -100                                                                                                                    # Maximalgeschwindigkeit rückwärts wird gewählt

MIN_FLAECHE = 400                                                                                                                   # Minimalfläche der Linie wird gewählt
MIN_HOEHE_VON_SCHWARZ = 50                                                                                                          # minimale Höhe der Linie wird festgelegt


global cx,cy,cx1,cy1,cx2,cy2,cx3,cy3, FAHRGESCHWINDIGKEIT                                                                           # Globale Variablen werden definiert (für Zentralpunkte, das Vorhandensein der Linie(unten, oben, rechts, und links) und die Fahrgeschwindigkeit)
cy,cx,cx1,cy1,cx2,cy2,cx3,cy3, FAHRGESCHWINDIGKEIT = 0,0,0,0,0,0,0,0, 60                                                            #
global US,OS,LS,RS                                                                                                                  #
US = True                                                                                                                           #
OS = True                                                                                                                           #
LS = True                                                                                                                           #
RS = True                                                                                                                           #

praeferierte_linie = (False, 0)                                                                                                     # EGAL - FUNKTIONIERT NOCH NICHT

class Richtung(Enum):                                                                                                               # Klasse für die Richtung, die eingelegt werden soll
    GERADEAUS = 1                                                                                                                   # d.h. man soll geradeaus fahren
    LINKS = 2                                                                                                                       # d.h. man soll links fahren
    RECHTS = 3                                                                                                                      # d.h. man soll rechts fahren
    WENDEN = 4                                                                                                                      # d.h.e man soll wenden

class Hindernis(Enum):
    Links = 1
    Rechts = 2

def center_line(dieser_frame):                                                                                                      # Funktion für eine senkrechte Linie in der Mitte
    cv2.line(dieser_frame,(int((PIXEL_BREITE-1)/2),0),(int((PIXEL_BREITE-1)/2),PIXEL_HOEHE-1),GELB,1)                               # -(Bild, 1. Punkt(~), 2. Punkt(~), Farbe, Breite)

def rechteck_zentrum(x, y, w, h):                                                                                                   # Funktion für die Bestimmungs eines Mittelpunktes eines Rechtecks bzw. einer Koordinate
    return (x+w/2, y+h/2)                                                                                                           #

def kreuzungen_erkennen(dieser_frame, gruene_maske):                                                                                # Funktion um grüne Punkte zu erkennen 
    markierungen = []                                                                                                               # erstmal leere Variable für die Koordinaten der grünen Punkte
    _, konturen, _ = cv2.findContours(gruene_maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)                                         # die (noch "fizzligen" Konturen von den grünen Punkten werden gesucht)
    for kontur in konturen:                                                                                                         # für jede dieser Konturen:
        if cv2.contourArea(kontur) > 2000:                                                                                          # und nur wenn die Fläche der Kontur größer als 2000 Quadratpixel ist
            x, y, w, h = cv2.boundingRect(kontur)                                                                                   # ein Rechteck wird um die Kontur wird gezogen und die Werte gespeichert
            if y > PIXEL_HOEHE - SLICE_HOEHE_FUER_GRUEN and y < PIXEL_HOEHE - SLICE_HOEHE_FUER_GRUEN_1:
                farbe = ROT
            else:
                farbe = BLAU
            cv2.rectangle(dieser_frame, (x, y), (x + w, y + h), farbe, 2)                                                                    # der Mittelpunkte von Grün wird gemerkt
            markierungen.append(rechteck_zentrum(x, y, w, h))
    return markierungen                                                                                                             # "markiereungen" wird zurückgegeben

def kreuzung_abbiegen(markierungen):                                                                                                # Funktion für die Bewältigung der grünen Flächen
    if len(markierungen) is 1:                                                                                                      # Wenn es nur eine grüne Fläche gibt:
  #      if LS:                                                                                                                      #   und es links eine Linie gibt:
   #         if POINT_2[1] >= markierungen[0][1]:                                          #oder?                                     #       und wenn die Linie unter dem Grün ist:
    #            print("kreuzung is Richtung.GERADEAUS")                                                                             #           sagt: "musst vorwärts" (~)
     #           motor_links.setSpeed(VOLLGAS)                                                                                       #           linker Motor: VOLLGAS!!
      #          motor_rechts.setSpeed(VOLLGAS)                                                                                      #           rechter Motor: VOLLGAS!!
       #         time.sleep(1)                                                                                                       #           für eine Sekunde
        #        linienparkour_bewältigen_US_OS()                                                                                    #           Linie, die oben und unten ist, wird gefolgt
         #       return Richtung.GERADEAUS                                                                                           #
          #  else:
           #     if markierungen[0][0] < POINT[0]:                                                                                           #   und wenn das Grün vor der Linie in der linken Hälfte ist: 
            #        print("kreuzung is Richtung.LINKS")                                                                                     #       sagt er: "muss nach links" (~)
             #       time.sleep(0.5)
              #      motor_links.setSpeed(VOLLGAS_R)                                                                                         #       linker Motor: VOLLGAS RÜCKWÄRTS!!
               #     motor_rechts.setSpeed(VOLLGAS)                                                                                          #       rechter Motor: VOLLGAS!!
                #    time.sleep(1)                                                                                                         #       für eine halbe Sekunde
                 #   linienparkour_bewältigen_US_LS()                                                                                        #       Linie, die unten und links ist, wird gefolgt
                  #  return Richtung.LINKS                                                                                                   #
#                else:                                                                                                                       #   und wenn das Grün vor der linie in der rechten Hälfte ist
 #                   print("kreuzung is Richtung.RECHTS")                                                                                    #       sagt: "muss nach rechts"
  #                  time.sleep(0.5)
   #                 motor_links.setSpeed(VOLLGAS)                                                                                           #       linker Motor: VOLLGAS!!
    #                motor_rechts.setSpeed(VOLLGAS_R)                                                                                        #       rechter Motor: VOLLGAS RÜCKWÄRTS!!
     #               time.sleep(1)                                                                                                         #       für eine halbe Sekunde
      #              linienparkour_bewältigen_US_RS()                                                                                        #       Linie, die unten und rechts ist, wird gefolgt
       #             return Richtung.RECHTS                                                                                                  #
#        elif RS:                                                                                                                    #   und wenn Rechts eine Linie ist:
 #           if POINT_3[1] >= markierungen[0][1]:                                          #oder?                                     #       und wenn die Linie unter dem Grün ist:
  #              print("kreuzung is Richtung.GERADEAUS")                                                                             #       sagt er: "musst vorwärts" (~)
   #             motor_links.setSpeed(VOLLGAS)                                                                                       #          linker Motor: VOLLGAS!!
    #            motor_rechts.setSpeed(VOLLGAS)                                                                                      #           rechter Motor: VOLLGAS!!
     #           time.sleep(1)                                                                                                       #           für eine Sekunde
      #          linienparkour_bewältigen_US_OS()                                                                                    #           Linie, die oben und unten ist, wird gefolgt
       #         return Richtung.GERADEAUS                                                                                           #
        #    else:
         #       if markierungen[0][0] < POINT[0]:                                                                                           #   und wenn das Grün vor der Linie in der linken Hälfte ist: 
          #          print("kreuzung is Richtung.LINKS")                                                                                     #       sagt er: "muss nach links" (~)
           #         time.sleep(0.5)
            #        motor_links.setSpeed(VOLLGAS_R)                                                                                         #       linker Motor: VOLLGAS RÜCKWÄRTS!!
             #       motor_rechts.setSpeed(VOLLGAS)                                                                                          #       rechter Motor: VOLLGAS!!
              #      time.sleep(1)                                                                                                         #       für eine halbe Sekunde
               #     linienparkour_bewältigen_US_LS()                                                                                        #       Linie, die unten und links ist, wird gefolgt
                #    return Richtung.LINKS                                                                                                   #
#                else:                                                                                                                       #   und wenn das Grün vor der linie in der rechten Hälfte ist
 #                   print("kreuzung is Richtung.RECHTS")                                                                                    #       sagt: "muss nach rechts"
  #                  time.sleep(0.5)
   #                 motor_links.setSpeed(VOLLGAS)                                                                                           #       linker Motor: VOLLGAS!!
    #                motor_rechts.setSpeed(VOLLGAS_R)                                                                                        #       rechter Motor: VOLLGAS RÜCKWÄRTS!!
     #               time.sleep(1)                                                                                                         #       für eine halbe Sekunde
      #              linienparkour_bewältigen_US_RS()                                                                                        #       Linie, die unten und rechts ist, wird gefolgt
       #         return Richtung.RECHTS                                                                                                  #
        #motor_links.setSpeed(0)
        #motor_rechts.setSpeed(0)
        time.sleep(1)
        if LS and RS:
            D = (POINT_2[1] + POINT_3[1])//2 
            if D > markierungen[0][1]:
                print("kreuzung is Richtung.GERADEAUS")                                                                                     #       sagt er: "muss nach links" (~)
                #motor_links.setSpeed(VOLLGAS)                                                                                         #       linker Motor: VOLLGAS RÜCKWÄRTS!!
                #motor_rechts.setSpeed(VOLLGAS)                                                                                          #       rechter Motor: VOLLGAS!!
                time.sleep(1)                                                                                                         #       für eine halbe Sekunde
                return Richtung.GERADEAUS
            else:
                if markierungen[0][0] < POINT[0]:
                    #motor_links.setSpeed(VOLLGAS_R)
                    #motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(1)
        elif LS:
            if POINT_2[1] > markierungen[0][1]:
                print("kreuzung is Richtung.GERADEAUS")
                print("LS")                                                                                     #       sagt er: "muss nach links" (~)
                #motor_links.setSpeed(VOLLGAS)                                                                                         #       linker Motor: VOLLGAS RÜCKWÄRTS!!
                #motor_rechts.setSpeed(VOLLGAS)                                                                                          #       rechter Motor: VOLLGAS!!
                time.sleep(1)                                                                                                         #       für eine halbe Sekunde
                return Richtung.GERADEAUS
            else:
                if markierungen[0][0] < POINT[0]:
                    print(links)
                    #motor_links.setSpeed(VOLLGAS)
                    #motor_rechts.setSpeed(VOLLGAS_R)
                    time.sleep(0.8)
                else:
                    #motor_links.setSpeed(VOLLGAS_R)
                    #motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(0.8)
        else:
            if POINT_3[1] > markierungen[0][1]:
                #motor_links.setSpeed(VOLLGAS)                                                                                         #       linker Motor: VOLLGAS RÜCKWÄRTS!!
                #motor_rechts.setSpeed(VOLLGAS)                                                                                          #       rechter Motor: VOLLGAS!!
                time.sleep(1)                                                                                                         #       für eine halbe Sekunde
                return Richtung.GERADEAUS
            else:
                if markierungen[0][0] < POINT[0]:
                    #motor_links.setSpeed(VOLLGAS)
                    #motor_rechts.setSpeed(VOLLGAS_R)
                    time.sleep(0.8)
                else:
                    #motor_links.setSpeed(VOLLGAS_R)
                    #motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(0.8)
    elif len(markierungen) is 2:                                                                                                    # Wenn es 2 grüne Flächen gibt:
        if markierungen[0][0] < POINT[0] and markierungen[1][0] < POINT[0]:                                                         #   und wenn die x-Koordinate des 1. Grün links von der Linie und das ander auch:
            print("kreuzung is Richtung.LINKS2")                                                                                    #       sagt: "muss links"
            #motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            #motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
            time.sleep(1)
            #motor_rechts.setSpeed(90)                                                                                               #       rechter Motor: 90%
            #motor_links.setSpeed(-40)                                                                                               #       linker Motor: -40%
            time.sleep(0.5)
            return Richtung.LINKS                                                                                                   #
        elif markierungen[0][0] > POINT[0] and markierungen[1][0] > POINT[0]:                                                       #   und wenn die x Koordinate des 1. Grün rechts von der Linie ist und das andere auch:
            print("kreuzung is Richtung.RECHTS2")                                                                                   #       sagt: "muss rechts"
            #motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            #motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
            time.sleep(1)
            #motor_rechts.setSpeed(-40)                                                                                              #       rechter Motor: -40%
            #motor_links.setSpeed(90)                                                                                                #       linker Motor:   90%
            time.sleep(1)
            return Richtung.RECHTS                                                                                                  #
        elif LS and RS:                                                                                                             #   und wenn es links und rechts eine Linie gibt:
            LS_RS_DURCHSCHNITT = (POINT_2[1]+POINT_3[1])/2                                                                         #       durchschnittliche Höhe der Linie wird berechnet
            MARKIERUNGEN_DURCHSCHNITT = (markierungen[0][1]+markierungen[1][1])/2                                                   #       durchschnittliche Höhe der grünen Punkte wird berechnet
            if LS_RS_DURCHSCHNITT < MARKIERUNGEN_DURCHSCHNITT:                                                                      #       und wenn die Linien über den Markierungen sind
                print("kreuzung is Richtung.WENDEN")                                                                                #           sagt er: "muss wenden"
                #motor_links.setSpeed(VOLLGAS)                                                                                       #           linker Motor: VOLLGAS!!
                #motor_rechts.setSpeed(VOLLGAS_R)                                                                                    #           rechter Motor: VOLLGAS RÜCKWÄRTS!!
                time.sleep(2)                                                                                                     #           für 1.5 Sekunden
                linienparkour_bewältigen_US_OS()                                                                                    #           die Linie, die oben und unten ist, wird gefolgt
                return Richtung.WENDEN                                                                                              #
        else:                                                                                                                       #   sonst:
            print("kreuzung is Richtung.GERADEAUS")                                                                                 #       sagt er: "muss geradeaus"
            return Richtung.GERADEAUS                                                                                               #
    else:                                                                                                                           # Sonst:
        return Richtung.GERADEAUS                                                                                                  #

def linie_aussuchen_unten(dieser_frame, offset, linie_erkennen_unten):                                                                                      # EGAL!!
    global praeferierte_linie                                                                                                                               #
    if len(linie_erkennen_unten) is 0:                                                                                                                      #
        praeferierte_linie = (False, 0)                                                                                                                     #
    elif len(linie_erkennen_unten) is 1:                                                                                                                    #
        praeferierte_linie = linie_erkennen_unten[0]                                                                                                        #
    else:                                                                                                                                                   #
        abstaende = []                                                                                                                                      #
        for linie in linie_erkennen_unten:                                                                                                                  #
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])                                                                   #
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))                                                                                            #
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])                                                                         #
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)   #
    return praeferierte_linie                                                                                                                               #

def linie_aussuchen_oben(dieser_frame, offset, linie_erkennen_oben):                                                                                        # EGAL!!
    global praeferierte_linie                                                                                                                               #
    if len(linie_erkennen_oben) is 0:                                                                                                                       #
        praeferierte_linie = (False, 0)                                                                                                                     #
    elif len(linie_erkennen_oben) is 1:                                                                                                                     #
        praeferierte_linie = linie_erkennen_oben[0]                                                                                                         #
    else:                                                                                                                                                   #
        abstaende = []                                                                                                                                      #
        for linie in linie_erkennen_oben:                                                                                                                   #
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])                                                                   #
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))                                                                                            #
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])                                                                         #
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)   #
    return praeferierte_linie                                                                                                                               #
                                                                                                                                                            
def linie_aussuchen_links(dieser_frame, offset, linie_erkennen_links):                                                                                      # EGAL!!
    global praeferierte_linie                                                                                                                               #
    if len(linie_erkennen_links) is 0:                                                                                                                      #
        praeferierte_linie = (False, 0)                                                                                                                     #
    elif len(linie_erkennen_links) is 1:                                                                                                                    #
        praeferierte_linie = linie_erkennen_links[0]                                                                                                        #
    else:                                                                                                                                                   #
        abstaende = []                                                                                                                                      #
        for linie in linie_erkennen_links:                                                                                                                  #
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])                                                                   #
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))                                                                                            #
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])                                                                         #
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)   #
    return praeferierte_linie                                                                                                                               #

def linie_aussuchen_rechts(dieser_frame, offset, linie_erkennen_rechts):                                                                                    # EGAL!!
    global praeferierte_linie                                                                                                                               #
    if len(linie_erkennen_rechts) is 0:                                                                                                                     #
        praeferierte_linie = (False, 0)                                                                                                                     #
    elif len(linie_erkennen_rechts) is 1:                                                                                                                   #
        praeferierte_linie = linie_erkennen_rechts[0]                                                                                                       #
    else:                                                                                                                                                   #
        abstaende = []                                                                                                                                      #
        for linie in linie_erkennen_rechts:                                                                                                                 #
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])                                                                   #
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))                                                                                            #
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])                                                                         #
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)   #
    return praeferierte_linie                                                                                                                               #

def linie_erkennen_unten(dieser_frame, schwarze_maske, offset):                                                                                             # Funktion für das Erkennen der Linie unten
    global cx                                                                                                                                               # Variable für den Zentrumpunkt der Linie
    global cy                                                                                                                                               # Variable für den Zentrumpunkt der Linie
    global US                                                                                                                                               # Booleaan für das Vorhandensein der Linie
    yoffset = PIXEL_HOEHE - SLICE_HOEHE_FUER_SCHWARZ - offset - 1                                                                                           # Verschiebung der "Schicht" auf der y- Achse
    roi_line = schwarze_maske[yoffset: yoffset + SLICE_HOEHE_FUER_SCHWARZ, 0: PIXEL_BREITE - 1]
    _, konturen, _ = cv2.findContours(roi_line, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cx = 0
    cy = yoffset + SLICE_HOEHE_FUER_SCHWARZ/2
    cnt = 0
    farbe = GRUEN
    linien = []
    for kontur in konturen:
        x, y, w, h = cv2.boundingRect(kontur)
        if cv2.contourArea(kontur) > MIN_FLAECHE:
            if w >= PIXEL_BREITE-MIN_HOEHE_VON_SCHWARZ:
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
        #cx = (PIXEL_BREITE - 1) / 2
        US = False
    else:
        cx = cx / cnt
        cv2.circle(dieser_frame, (int(cx), int(cy)), 5, farbe, -1)
        US = True
    return linien

def linie_erkennen_oben(dieser_frame, schwarze_maske):
    global cx1
    global cy1
    global OS
    roi_line = schwarze_maske[:SLICE_HOEHE_FUER_SCHWARZ_1, 0: PIXEL_BREITE - 1]
    _, konturen, _ = cv2.findContours(roi_line, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cx1 = 0
    cy1 = SLICE_HOEHE_FUER_SCHWARZ_1/2
    cnt = 0
    farbe = GRUEN
    linien = []
    for kontur in konturen:
        x1, y1, w1, h1 = cv2.boundingRect(kontur)
        if cv2.contourArea(kontur) > MIN_FLAECHE:
            if w1 >= PIXEL_BREITE-MIN_HOEHE_VON_SCHWARZ:
                farbe = ROT
                ist_kreuzung = True
            else:
                farbe = GELB
                ist_kreuzung = False
            cv2.rectangle(dieser_frame, (x1, y1), (x1 + w1, y1 + h1), farbe, 2)
            cx1 = cx1 + int(x1 + w1 / 2)
            cnt = cnt + 1
            if ist_kreuzung:
                linien.append((True, cx1 - PIXEL_BREITE / 2))
            else:
                linien.append((False, cx1 - PIXEL_BREITE / 2))
    if cx1 is 0:
        OS = False
    else:
        cx1 = cx1 / cnt
        cv2.circle(dieser_frame, (int(cx1), int(cy1)), 5, farbe, -1)
        OS = True
    return linien

def linie_erkennen_links(dieser_frame, schwarze_maske):
    global cy2
    global cx2
    global LS
    roi_line = schwarze_maske[:PIXEL_HOEHE-1, : SLICE_BREITE_FUER_SCHWARZ]
    _, konturen, _ = cv2.findContours(roi_line, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cy2 = 0
    cx2 = SLICE_BREITE_FUER_SCHWARZ_1/2
    cnt = 0
    farbe = GRUEN
    linien = []
    for kontur in konturen:
        x2, y2, w2, h2 = cv2.boundingRect(kontur)
        if cv2.contourArea(kontur) > MIN_FLAECHE:
            if h2 >= PIXEL_HOEHE-MIN_HOEHE_VON_SCHWARZ:
                farbe = ROT
                ist_kreuzung = True
            else:
                farbe = GELB
                ist_kreuzung = False
            cv2.rectangle(dieser_frame, (x2, y2), (x2 + w2, y2 + h2), farbe, 2)
            cy2 = cy2 + int(y2 + h2 / 2)
            cnt = cnt + 1
            if ist_kreuzung:
                linien.append((True, cy2 - PIXEL_HOEHE / 2))
            else:
                linien.append((False, cy2 - PIXEL_HOEHE / 2))
    if cy2 is 0:
        LS = False#
    else:
        LS = True
        cy2 = cy2 / cnt
        cv2.circle(dieser_frame, POINT_2, 5, farbe, -1)
    return linien

def linie_erkennen_rechts(dieser_frame, schwarze_maske, offset):
    global cy3
    global cx3
    global RS
    xoffset = PIXEL_BREITE - SLICE_BREITE_FUER_SCHWARZ_1 - offset - 1
    roi_line = schwarze_maske[0: PIXEL_HOEHE - 1, xoffset: xoffset + SLICE_BREITE_FUER_SCHWARZ]
    _, konturen, _ = cv2.findContours(roi_line, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cy3 = 0
    cx3 = SLICE_BREITE_FUER_SCHWARZ_1/2 + xoffset
    cnt = 0
    farbe = GRUEN
    linien = []
    for kontur in konturen:
        x3, y3, w3, h3 = cv2.boundingRect(kontur)
        if cv2.contourArea(kontur) > MIN_FLAECHE:
            if h3 >= PIXEL_HOEHE-MIN_HOEHE_VON_SCHWARZ:
                farbe = ROT
                ist_kreuzung = True
            else:
                farbe = GELB
                ist_kreuzung = False
            cv2.rectangle(dieser_frame, (x3 + xoffset, y3), (x3 + xoffset + w3, y3 + w3), farbe, 2)
            cy3 = cy3 + int(y3 + h3 / 2)
            cnt = cnt + 1
            if ist_kreuzung:
                linien.append((True, cy3 - PIXEL_HOEHE / 2))
            else:
                linien.append((False, cy3 - PIXEL_HOEHE / 2))
    if cy3 is 0:
        RS = False
        #cx1 = 1# (PIXEL_BREITE - 1) / 2
    else:
        cy3 = cy3 / cnt
        cv2.circle(dieser_frame, (int(cx3), int(cy3)), 5, farbe, -1)
        RS = True
    return linien

def linienparkour_bewältigen_US_OS():
    global FAHRGESCHWINDIGKEIT
    FAHRGESCHWINDIGKEIT = 60
    GEGENKATHETE = POINT_1[0] - 159
    ANKATHETE = 209
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_OS")

def linienparkour_bewältigen_US_LS():
    GEGENKATHETE = POINT_2[0] - STANDARD_PUNKT[0]
    ANKATHETE = POINT_2[1] - STANDARD_PUNKT[1] + 0.1
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_LS")
    
def linienparkour_bewältigen_US_RS():
    GEGENKATHETE = POINT_3[0] - STANDARD_PUNKT[0]
    ANKATHETE = POINT_3[1] - STANDARD_PUNKT[1] + 0.1
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_RS")
    
def linienparkour_bewältigen_US_OS_RS():
    print("linienparkour_bewältigen_US_OS_RS")
    #print(WINKEL)
    linienparkour_bewältigen_US_OS()

def linienparkour_bewältigen_US_OS_LS():
    print("linienparkour_bewältigen_US_OS_LS")
    #print(WINKEL)
    linienparkour_bewältigen_US_OS()

def linienparkour_bewältigen_US_OS_LS_RS():
    GEGENKATHETE = POINT_1[0] - STANDARD_PUNKT[0]
    ANKATHETE = 209
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_OS_LS_RS")
    #print(WINKEL)
    linienparkour_bewältigen_US_OS()

def linienparkour_bewältigen_US_LS_RS():
    print("linienparkour_bewältigen_US_LS_RS")
    if POINT_2[1] > POINT_3[1]:
        GEGENKATHETE = POINT_3[0] - 169
        ANKATHETE = POINT_3[1] - STANDARD_PUNKT[1] + 0.1
        WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
        print("linienparkour_bewältigen_US_RS")
        #print(WINKEL)
        
    else:
        GEGENKATHETE = POINT_2[0] - 69
        ANKATHETE = POINT_2[1] - STANDARD_PUNKT[1] + 0.1
        WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
        print("linienparkour_bewältigen_US_LS")
        #print(WINKEL)

def linienparkour_bewältigen_LS_RS():
    print("linienparkour_bewältigen_LS_RS")
    if POINT_2[1] > POINT_3[1]:
        GEGENKATHETE = POINT_3[0] - 169
        ANKATHETE = POINT_3[1] - STANDARD_PUNKT[1] + 0.1
        WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
        print("linienparkour_bewältigen_US_RS")
        #print(WINKEL)
        linienparkour_bewältigen_US_RS()
    else:
        GEGENKATHETE = POINT_2[0] - 69
        ANKATHETE = POINT_2[1] - STANDARD_PUNKT[1] + 0.1
        WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
        print("linienparkour_bewältigen_US_LS")
        #print(WINKEL)
        linienparkour_bewältigen_US_LS()

def rampe():
    beschleunigung_x, beschleunigung_y, beschleunigung_z = beschl_kompass_sensor.acceleration
    global FAHRGESCHWINDIGKEIT
    FAHRGESCHWINDIGKEIT = 60
    if beschleunigung_x >= 3:
        print("Bergab!")
        FAHRGESCHWINDIGKEIT = 50
    elif beschleunigung_x <= -3:
        print("Bergauf!")
        FAHRGESCHWINDIGKEIT = VOLLGAS
    else:
        FAHRGESCHWINDIGKEIT = 70

def scale(wert, a, b, c, d):
    wert = (wert-a)*((d-c)/(b-a))+c
    return wert

def HINDERNIS():
    if abstand == 0:
        pass
    else:
        if abstand < 85:
            print("Abstand=%smm" % (abstand))
            
            
try:
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    beschl_kompass_sensor = adafruit_lsm303.LSM303(i2c_bus)
    gyro_sensor = adafruit_l3gd20.L3GD20_I2C(i2c_bus)

    kamera = PiCamera(resolution=(PIXEL_BREITE, PIXEL_HOEHE), framerate=32)
    speichert_einen_frame = numpy.empty((PIXEL_HOEHE, PIXEL_BREITE, 3), dtype=numpy.uint8)

    for dieser_frame in kamera.capture_continuous(speichert_einen_frame, 'bgr', use_video_port=True):
        
        abstand = tof_sensor.range

        rampe()
        HINDERNIS()
        gray = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(dieser_frame, cv2.COLOR_BGR2HSV)
        
        STANDARD_PUNKT = (159, 224)
        POINT = (int(cx),int(cy))
        POINT_1 = (int(cx1),int(cy1))
        POINT_2 = (int(cx2),int(cy2))
        POINT_3 = (int(cx3),int(cy3))

        _, schwarze_maske = cv2.threshold(gray, helligkeits_schwelle, 255, cv2.THRESH_BINARY_INV)
        gruene_maske = cv2.inRange(hsv, gruen_untere_schwelle, gruen_obere_schwelle)
        schwarze_maske = schwarze_maske - gruene_maske

        kreuzung = kreuzung_abbiegen(kreuzungen_erkennen(dieser_frame, gruene_maske))
        linie_unten = linie_aussuchen_unten(dieser_frame,0, linie_erkennen_unten(dieser_frame, schwarze_maske, 35))
        linie_oben = linie_aussuchen_oben(dieser_frame,0, linie_erkennen_oben(dieser_frame, schwarze_maske))
        linie_links = linie_aussuchen_links(dieser_frame,0, linie_erkennen_links(dieser_frame, schwarze_maske))
        linie_rechts = linie_aussuchen_rechts(dieser_frame,0, linie_erkennen_rechts(dieser_frame, schwarze_maske, 0))


        if US and OS and not RS and not LS:
            linienparkour_bewältigen_US_OS()

        elif US and OS and LS and not RS:
            linienparkour_bewältigen_US_OS_LS()

        elif US and OS and RS and not LS:
            linienparkour_bewältigen_US_OS_RS()

        elif US and OS and LS and RS:
            linienparkour_bewältigen_US_OS()

        elif US and LS and not OS and not RS:
            linienparkour_bewältigen_US_LS()

        elif US and RS and not LS and not OS:
            linienparkour_bewältigen_US_RS()

        elif RS and LS and not OS and not US:
            linienparkour_bewältigen_LS_RS()

        elif US and not RS and not LS and not OS:
            print('Lückenanfang')
            
        elif not US and not RS and not LS and not OS:
            print('Lücke')

        elif OS and not US and not LS and not RS:
             linienparkour_bewältigen_US_OS()

        elif not US and OS and LS and not RS:
            linienparkour_bewältigen_US_OS()

        elif not US and OS and not LS and RS:
            linienparkour_bewältigen_US_OS()

        elif not US and OS and LS and RS:
            linienparkour_bewältigen_US_OS()

        center_line(dieser_frame)
        cv2.imshow("Maze Runner", dieser_frame)
        cv2.waitKey(1)

finally:
    print("Räume auf...")
    kamera.close()