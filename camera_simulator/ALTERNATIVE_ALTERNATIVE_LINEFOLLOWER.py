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
import adafruit_vl53l0x                                                                                                             

TOF_SENSOR_ADDRRESSE = 0x29                                                                                                         
i2c_bus = busio.I2C(board.SCL, board.SDA)                                                                                           
tof_sensor = adafruit_vl53l0x.VL53L0X(i2c_bus, address=TOF_SENSOR_ADDRRESSE)                                                        
tof_sensor.measurement_timing_budget = 20000 

PIXEL_BREITE = 320                                                                                                                  
PIXEL_HOEHE = 240                                                                                                                   

GRUEN = (0, 255, 0)                                                                                                                 
GELB = (0,255,255)                                                                                                                  
ROT = (0, 0, 255)                                                                                                                   
BLAU = (255, 0, 0)                                                                                                                  

helligkeits_schwelle = 50                                                                                                           
gruen_untere_schwelle = numpy.uint8([5, 80, 20])                                                                                   
gruen_obere_schwelle = numpy.uint8([89, 255, 200])                                                                                 

SLICE_HOEHE = 30                                                                                                                   
SLICE_HOEHE_FUER_GRUEN = 180                                                                                                       
SLICE_HOEHE_FUER_GRUEN_1 = 100

SLICE_HOEHE_FUER_SCHWARZ = 30                                                                                                      
SLICE_HOEHE_FUER_SCHWARZ_1 = 30                                                                                                    
SLICE_BREITE_FUER_SCHWARZ = 30                                                                                                     
SLICE_BREITE_FUER_SCHWARZ_1 = 30                                                                                                   

LENKEN_IGNORIEREN = 20                                                                                                             

VOLLGAS = 100                                                                                                                       

MIN_FLAECHE = 400                                                                                                                   
MIN_HOEHE_VON_SCHWARZ = 50                                                                                                          

global cx,cy,cx1,cy1,cx2,cy2,cx3,cy3,FAHRGESCHWINDIGKEIT,WINKEL                                                                            
cy,cx,cx1,cy1,cx2,cy2,cx3,cy3,FAHRGESCHWINDIGKEIT,WINKEL = 0,0,0,0,0,0,0,0,60,0                                                            
global US,OS,LS,RS,istLinks                                                                                                        
US = True                                                                                                                           
OS = True                                                                                                                           
LS = True                                                                                                                           
RS = True                                                                                                                           
istLinks = True

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
            if y > PIXEL_HOEHE - SLICE_HOEHE_FUER_GRUEN and y < PIXEL_HOEHE - SLICE_HOEHE_FUER_GRUEN_1:
                farbe = BLAU
            else:
                farbe = BLAU
            cv2.rectangle(dieser_frame, (x, y), (x + w, y + h), farbe, 2)                                                                 
            markierungen.append(rechteck_zentrum(x, y, w, h))
    return markierungen                                                                                                            

def kreuzung_abbiegen(markierungen):                                                                                               
    if len(markierungen) is 1:                                                                                                 
        motor_links.setSpeed(0)
        motor_rechts.setSpeed(0)
        time.sleep(1)
        if LS and RS:
            D = (POINT_2[1] + POINT_3[1])//2 
            if D > markierungen[0][1]:
                print("kreuzung is Richtung.GERADEAUS")                                                                                   
                motor_links.setSpeed(VOLLGAS)                                                                                        
                motor_rechts.setSpeed(VOLLGAS)                                                                                       
                time.sleep(1)                                                                                                        
                return Richtung.GERADEAUS
            else:
                if markierungen[0][0] < POINT[0]:
                    motor_links.setSpeed(-VOLLGAS)
                    motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(1)
        elif LS:
            if POINT_2[1] > markierungen[0][1]:
                print("kreuzung is Richtung.GERADEAUS")
                print("LS")                                                                                     
                motor_links.setSpeed(VOLLGAS)                                                                    
                motor_rechts.setSpeed(VOLLGAS)                                                                   
                time.sleep(1)                                                                                    
                return Richtung.GERADEAUS
            elif POINT_2[1] > markierungen[0][1]:
                if markierungen[0][0] < 159:
                    print("q")
                    motor_links.setSpeed(-VOLLGAS)
                    motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(0.7)
                else:
                    print("e")
                    motor_rechts.setSpeed(60)                                                                                              
                    motor_links.setSpeed(60)                                                                                               
                    time.sleep(0.3)
                    motor_rechts.setSpeed(90)                                                                                              
                    motor_links.setSpeed(-40)                                                                                              
                    time.sleep(1.4)
        elif RS:
            if POINT_3[1] > markierungen[0][1]:
                print("kreuzung is Richtung.GERADEAUS")
                print("LS")                                                                                     
                motor_links.setSpeed(VOLLGAS)                                                                    
                motor_rechts.setSpeed(VOLLGAS)                                                                   
                time.sleep(1)                                                                                    
                return Richtung.GERADEAUS
            elif POINT_2[1] > markierungen[0][1]:
                if markierungen[0][0] < 159:
                    print("q")
                    motor_links.setSpeed(-VOLLGAS)
                    motor_rechts.setSpeed(VOLLGAS)
                    time.sleep(0.7)
                else:
                    print("e")
                    motor_rechts.setSpeed(60)                                                                                              
                    motor_links.setSpeed(60)                                                                                               
                    time.sleep(0.3)
                    motor_rechts.setSpeed(90)                                                                                              
                    motor_links.setSpeed(-40)                                                                                              
                    time.sleep(1.4)                                                          
        D = (POINT_2[1] + POINT_3[1])//2
        if markierungen[0][0] < POINT[0] and markierungen[1][0] < POINT[0]:                  
            print("kreuzung is Richtung.LINKS2")                                             
            motor_rechts.setSpeed(90)                                                        
            motor_links.setSpeed(-40)                                                        
            time.sleep(0.6)
            return Richtung.LINKS                                                            
        elif markierungen[0][0] > POINT[0] and markierungen[1][0] > POINT[0]:                
            print("kreuzung is Richtung.RECHTS2")                                            
            motor_rechts.setSpeed(-40)                                                                                              
            motor_links.setSpeed(90)                                                                                                
            time.sleep(0.8)
            return Richtung.RECHTS                                                                                                  
        elif markierungen[0][1] < D and markierungen[1][1] > D:
            if markierungen[1][0] < 159:
                motor_rechts.setSpeed(60)                                                                                           
                motor_links.setSpeed(60)                                                                                            
                time.sleep(0.3)
                motor_rechts.setSpeed(90)                                                                                           
                motor_links.setSpeed(-40)                                                                                           
                time.sleep(1.4)
            else:
                motor_rechts.setSpeed(60)                                                                                           
                motor_links.setSpeed(60)                                                                                            
                time.sleep(0.3)
                motor_rechts.setSpeed(-40)                                                                                          
                motor_links.setSpeed(90)                                                                                            
                time.sleep(1.4)
        elif markierungen[0][1] > D and markierungen[1][1] < D:
            if markierungen[0][0] < 159:
                motor_rechts.setSpeed(60)                                                                                           
                motor_links.setSpeed(60)                                                                                            
                time.sleep(0.3)
                motor_rechts.setSpeed(90)                                                                                           
                motor_links.setSpeed(-40)                                                                                           
                time.sleep(1.4)
            else:
                motor_rechts.setSpeed(60)                                                                    
                motor_links.setSpeed(60)                                                                     
                time.sleep(0.3)
                motor_rechts.setSpeed(-40)           
                motor_links.setSpeed(90)             
                time.sleep(1.4)    
        elif LS and RS:                              
            motor_links.setSpeed(0)
            motor_links.setSpeed(0)
            time.sleep(1)
            LS_RS_DURCHSCHNITT = (POINT_2[1]+POINT_3[1])/2                                                              
            MARKIERUNGEN_DURCHSCHNITT = (markierungen[0][1]+markierungen[1][1])/2                                       
            if LS_RS_DURCHSCHNITT < MARKIERUNGEN_DURCHSCHNITT:                                                          
                print("kreuzung is Richtung.WENDEN")                                                                    
                motor_links.setSpeed(-VOLLGAS)                                                                          
                motor_rechts.setSpeed(VOLLGAS)                                                                          
                time.sleep(1.8)                                                                                         
                linienparkour_bewältigen_US_OS()                                                                        
                return Richtung.WENDEN                                                                                  
        else:                                                                                                           
            print("kreuzung is Richtung.GERADEAUS2")                                                                    
            return Richtung.GERADEAUS  
    elif len(markierungen) is 4:
        print("kreuzung is Richtung.WENDEN")                                                                            
        motor_links.setSpeed(-VOLLGAS)      
        motor_rechts.setSpeed(VOLLGAS)      
        time.sleep(1.8)                     
        linienparkour_bewältigen_US_OS()    
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
        LS = False
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
    else:
        cy3 = cy3 / cnt
        cv2.circle(dieser_frame, (int(cx3), int(cy3)), 5, farbe, -1)
        RS = True
    return linien

def Winkel():
    global Winkel
    if not US and OS:
        ANKATHETE = 209
        GEGENKATHETE = POINT_1[0] - STANDARD_PUNKT[0]
    if US and OS:
        ANKATHETE = 209
        if POINT[0] < 159 and POINT_1[0] < 159:
            GEGENKATHETE = POINT_1[0] - 319 + POINT[0]
        elif POINT[0] > 159 and POINT_1[0] < 159:
            GEGENKATHETE = POINT_1[0] - POINT[0]
        elif POINT[0] < 159 and POINT_1[0] > 159:
            GEGENKATHETE = POINT_1[0] - POINT[0]      
        else:
            GEGENKATHETE = POINT_1[0] - 319 + POINT[0]
    elif US and RS:
        ANKATHETE = POINT_3[1] - POINT[1]
        if POINT[0] < 159:
            GEGENKATHETE = POINT_3[0] - POINT[0]
        else:
            GEGENKATHETE = POINT_3[0] - 319 + POINT[0]
    elif US and LS:
        ANKATHETE = POINT_2[1] - POINT[1]
        if POINT[0] > 159:
            GEGENKATHETE = POINT_2[0] - POINT[0]
        else:
            GEGENKATHETE = POINT_2[0] - 319 + POINT[0]
    WINKEL = abs(int(math.degrees(math.atan(GEGENKATHETE/ANKATHETE))))
    return WINKEL

def linienparkour_bewältigen_US_OS():
    global FAHRGESCHWINDIGKEIT, WINKEL
    FAHRGESCHWINDIGKEIT = 60
    Winkel()
    if WINKEL <= LENKEN_IGNORIEREN:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif WINKEL < 0:
        motor_links.setSpeed(-scale(WINKEL,0,90,40,FAHRGESCHWINDIGKEIT))
        motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT))
    else:
        motor_links.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT))
        motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)))

def linienparkour_bewältigen_US_LS():
    print("linienparkour_bewältigen_US_LS")
    if WINKEL is 0:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif POINT_2[1] < 45:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)  
    else:    
        motor_links.setSpeed(-(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT))-5)
        motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)+5)

def linienparkour_bewältigen_US_RS():
    if WINKEL is 0:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
    elif POINT_3[1] < 45:
        motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
        motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)  
    else:    
        motor_links.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)+5)
        motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)-5))

def linienparkour_bewältigen_US_OS_RS():
    print("linienparkour_bewältigen_US_OS_RS")
    #print(WINKEL)
    linienparkour_bewältigen_US_OS()

def linienparkour_bewältigen_US_OS_LS_RS():
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
            motor_links.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT))
            motor_rechts.setSpeed(-(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)))
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
            motor_links.setSpeed(-(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT)))
            motor_rechts.setSpeed(scale(abs(WINKEL),0,90,40,FAHRGESCHWINDIGKEIT))

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

def forward():
    motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
    motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)

def rampe():
    beschleunigung_x, beschleunigung_y, beschleunigung_z = beschl_kompass_sensor.acceleration
    print(beschleunigung_x)
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
    abstand = tof_sensor.range
    if abstand == 0:
        pass
    else:
        if abstand < 86:
            global istLinks
            if istLinks == True:
                print("Abstand=%smm" % (abstand))
                motor_links.setSpeed(-VOLLGAS)
                motor_rechts.setSpeed(VOLLGAS)
                time.sleep(0.7)
                motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
                motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
                time.sleep(1)
                motor_links.setSpeed(VOLLGAS)
                motor_rechts.setSpeed(-VOLLGAS)
                time.sleep(0.75)
                motor_links.setSpeed(VOLLGAS)
                motor_rechts.setSpeed(25)
                time.sleep(1.75)
                istLinks = False
            else:
                print("Abstand=%smm" % (abstand))
                motor_rechts.setSpeed(-VOLLGAS)
                motor_links.setSpeed(VOLLGAS)
                time.sleep(0.7)
                motor_rechts.setSpeed(FAHRGESCHWINDIGKEIT)
                motor_links.setSpeed(FAHRGESCHWINDIGKEIT)
                time.sleep(1)
                motor_rechts.setSpeed(VOLLGAS)
                motor_links.setSpeed(-VOLLGAS)
                time.sleep(0.75)
                motor_rechts.setSpeed(VOLLGAS)
                motor_links.setSpeed(25)
                time.sleep(1.75)
                istLinks = True

def kreuzung():
    kreuzung_abbiegen(kreuzungen_erkennen(dieser_frame, gruene_maske))
        
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

        linie_unten = linie_aussuchen_unten(dieser_frame,0, linie_erkennen_unten(dieser_frame, schwarze_maske, 35))
        linie_oben = linie_aussuchen_oben(dieser_frame,0, linie_erkennen_oben(dieser_frame, schwarze_maske))
        linie_links = linie_aussuchen_links(dieser_frame,0, linie_erkennen_links(dieser_frame, schwarze_maske))
        linie_rechts = linie_aussuchen_rechts(dieser_frame,0, linie_erkennen_rechts(dieser_frame, schwarze_maske, 0))

        if US and OS and not LS and not RS:
            linienparkour_bewältigen_US_OS()

        elif US and OS and LS and not RS:
            linienparkour_bewältigen_US_OS()

        elif US and OS and not LS and not RS:
            linienparkour_bewältigen_US_OS()

        elif US and OS and LS and RS:
            linienparkour_bewältigen_US_OS()

        elif US and not OS and LS and not RS:
            linienparkour_bewältigen_US_LS()

        elif US and not OS and not LS and RS:
            linienparkour_bewältigen_US_RS()

        elif not US and not OS and LS and RS:
            linienparkour_bewältigen_LS_RS()

        elif not OS and not LS and not RS:
            forward()

        elif not US and OS and not LS and not RS:
             linienparkour_bewältigen_US_OS()

        elif not US and OS and LS and not RS:
            linienparkour_bewältigen_US_OS()

        elif not US and OS and not LS and RS:
            linienparkour_bewältigen_US_OS()

        elif not US and OS and LS and RS:
            linienparkour_bewältigen_US_OS()

        center_line(dieser_frame)
        #cv2.imshow("Maze Runner", dieser_frame)
        cv2.waitKey(1)

finally:
    print("Räume auf...")
    kamera.close()
    motor_links.close()
    motor_rechts.close()
    motorsteuerung.close()