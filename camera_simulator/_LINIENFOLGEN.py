from picamera import PiCamera
import time
import cv2
import numpy
from enum import Enum
from operator import itemgetter
import board
import busio
import adafruit_lsm303
import adafruit_l3gd20
from kkos.afmotorshield import *
import math

PIXEL_BREITE = 320
PIXEL_HOEHE = 240

GRUEN = (0, 255, 0)
GELB = (0,255,255)
ROT = (0, 0, 255)
BLAU = (255, 0, 0)

helligkeits_schwelle = 50
gruen_untere_schwelle = numpy.uint8([7, 127, 10])
gruen_obere_schwelle = numpy.uint8([79, 255, 100])
SLICE_HOEHE = 30

SLICE_HOEHE_FUER_GRUEN = 180

SLICE_HOEHE_FUER_SCHWARZ = 30
SLICE_HOEHE_FUER_SCHWARZ_1 = 30
SLICE_BREITE_FUER_SCHWARZ = 30
SLICE_BREITE_FUER_SCHWARZ_1 = 30

LENKEN_IGNORIEREN = 5
FAHRGESCHWINDIGKEIT = 50

global cx,cy,cx1,cy1,cx2,cy2,cx3,cy3
cy,cx,cx1,cy1,cx2,cy2,cx3,cy3 = 0,0,0,0,0,0,0,0
global OS,LS, RS
US = True
OS = True
LS = True
RS = True

praeferierte_linie = (False, 0)

class Richtung(Enum):
    GERADEAUS = 1
    LINKS = 2
    RECHTS = 3
    WENDEN = 4

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

def kreuzung_abbiegen(markierungen):
    if len(markierungen) is 1:
        if markierungen[0][0] < POINT[0]:
            print("kreuzung is Richtung.LINKS")
            linienparkour_bewältigen_US_LS()
            return Richtung.LINKS
        else:
            print("kreuzung is Richtung.RECHTS")
            linienparkour_bewältigen_US_RS()
            return Richtung.RECHTS
    elif len(markierungen) is 2:
        print("kreuzung is Richtung.WENDEN")
        return Richtung.WENDEN
    else:
        return Richtung.GERADEAUS

def linie_aussuchen_unten(dieser_frame, offset, linie_erkennen_unten):
    global praeferierte_linie
    if len(linie_erkennen_unten) is 0:
        praeferierte_linie = (False, 0)
    elif len(linie_erkennen_unten) is 1:
        praeferierte_linie = linie_erkennen_unten[0]
    else:
        abstaende = []
        for linie in linie_erkennen_unten:
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)
    return praeferierte_linie

def linie_aussuchen_oben(dieser_frame, offset, linie_erkennen_oben):
    global praeferierte_linie
    if len(linie_erkennen_oben) is 0:
        praeferierte_linie = (False, 0)
    elif len(linie_erkennen_oben) is 1:
        praeferierte_linie = linie_erkennen_oben[0]
    else:
        abstaende = []
        for linie in linie_erkennen_oben:
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)
    return praeferierte_linie

def linie_aussuchen_links(dieser_frame, offset, linie_erkennen_links):
    global praeferierte_linie
    if len(linie_erkennen_links) is 0:
        praeferierte_linie = (False, 0)
    elif len(linie_erkennen_links) is 1:
        praeferierte_linie = linie_erkennen_links[0]
    else:
        abstaende = []
        for linie in linie_erkennen_links:
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)
    return praeferierte_linie

def linie_aussuchen_rechts(dieser_frame, offset, linie_erkennen_rechts):
    global praeferierte_linie
    if len(linie_erkennen_rechts) is 0:
        praeferierte_linie = (False, 0)
    elif len(linie_erkennen_rechts) is 1:
        praeferierte_linie = linie_erkennen_rechts[0]
    else:
        abstaende = []
        for linie in linie_erkennen_rechts:
            abstaende.append([linie[0], linie[1], abs(praeferierte_linie[1] - linie[1])])
        sortiert_nach_naehe=sorted(abstaende, key=itemgetter(2))
        praeferierte_linie = (sortiert_nach_naehe[0][0], sortiert_nach_naehe[0][1])
    cv2.circle(dieser_frame, (int(PIXEL_BREITE/2 - 1 + praeferierte_linie[1]), int(PIXEL_HOEHE - offset - 1 - SLICE_HOEHE_FUER_SCHWARZ/2)), 10, GRUEN, 3)
    return praeferierte_linie

def linie_erkennen_unten(dieser_frame, schwarze_maske, offset):
    global cx
    global cy
    global US
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
        if cv2.contourArea(kontur) > 400:
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
        if cv2.contourArea(kontur) > 400:
            if w1 >= PIXEL_BREITE-50:
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
        if cv2.contourArea(kontur) > 400:
            if h2 >= PIXEL_HOEHE-50:
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
        if cv2.contourArea(kontur) > 400:
            if h3 >= PIXEL_HOEHE-50:
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
    GEGENKATHETE = POINT_1[0] - 159
    ANKATHETE = 209
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_OS")
    print(WINKEL)
    if abs(WINKEL) <= 20:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif WINKEL < 0:
        motor_links.setSpeed(-scale(abs(WINKEL),0,90,40,50))
        motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,70))
    else:
        motor_links.setSpeed(scale(abs(WINKEL),0,90,40,70))
        motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,50)))

def linienparkour_bewältigen_US_LS():
    GEGENKATHETE = POINT_2[0] - STANDARD_PUNKT[0]
    ANKATHETE = POINT_2[1] - STANDARD_PUNKT[1] + 0.1
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_LS")
    print(WINKEL)
    if WINKEL is 0:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif POINT_2[1] < 45:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)  
    else:    
        motor_links.setSpeed(-(scale(abs(WINKEL),0,90,40,50)))
        motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,70))

def linienparkour_bewältigen_US_RS():
    GEGENKATHETE = POINT_3[0] - STANDARD_PUNKT[0]
    ANKATHETE = POINT_3[1] - STANDARD_PUNKT[1] + 0.1
    WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
    print("linienparkour_bewältigen_US_RS")
    print(WINKEL)
    if WINKEL is 0:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif POINT_3[1] < 45:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)  
    else:    
        motor_links.setSpeed(scale(abs(WINKEL),0,90,40,70))
        motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,50)))

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
        if WINKEL is 0:
            motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
        elif POINT_3[1] < 45:
            motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)  
        else:
            motor_links.setSpeed(scale(abs(WINKEL),0,90,40,70))
            motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,50)))
    else:
        GEGENKATHETE = POINT_2[0] - 69
        ANKATHETE = POINT_2[1] - STANDARD_PUNKT[1] + 0.1
        WINKEL = int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE)))
        print("linienparkour_bewältigen_US_LS")
        #print(WINKEL)
        if WINKEL is 0:
            motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
        elif POINT_2[1] < 45:
            motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
            motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
        else:
            motor_links.setSpeed(-(scale(abs(WINKEL),0,90,40,50)))
            motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,70))

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
    if beschleunigung_x >= 3:
        print("Bergab!")
        FAHRGESCHWINDIGKEIT = 30
    elif beschleunigung_x <= -3:
        print("Bergauf!")
        FAHRGESCHWINDIGKEIT = 75
    else:
        FAHRGESCHWINDIGKEIT = 50

def scale(wert, a, b, c, d):
    wert = (wert-a)*((d-c)/(b-a))+c
    return wert

try:
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    beschl_kompass_sensor = adafruit_lsm303.LSM303(i2c_bus)
    gyro_sensor = adafruit_l3gd20.L3GD20_I2C(i2c_bus)

    kamera = PiCamera(resolution=(PIXEL_BREITE, PIXEL_HOEHE), framerate=32)
    speichert_einen_frame = numpy.empty((PIXEL_HOEHE, PIXEL_BREITE, 3), dtype=numpy.uint8)
    
    motorsteuerung = AFMotorShield(
        pin_clk=23,
        pin_data=6,
        pin_enable=5,
        pin_latch=26
    )

    motor_links = DCMotor(motorsteuerung, 2,
        pwm_pin=22,
        reversed=True
    )

    motor_rechts = DCMotor(motorsteuerung, 1,
        pwm_pin=16,
        reversed=True
    )

    for dieser_frame in kamera.capture_continuous(speichert_einen_frame, 'bgr', use_video_port=True):
        rampe()
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
             motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
             motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)

        elif not US and not RS and not LS and not OS:
             motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
             motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)

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
    motor_links.close()
    motor_rechts.close()
    motorsteuerung.close()