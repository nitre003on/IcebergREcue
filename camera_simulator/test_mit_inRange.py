"""
Demonstration der Nutzung von inRange im HSV-Farbschema.

Zeichnet auf 3 Schnitten im Kamerabild die gefundenen Linienstückchen als grüne
Rechtecke ein.
Wird die eine Linie zu breit, wird das Rechteck rot eingefärbt.
Das Zentrum aller Linienstückchen in einem Schnitt wird mit einem Punkt markiert.
Grüne Areale ab einer gewissen Größe werden blau umrandet.

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
PIXEL_BREITE, PIXEL_HOEHE: Auflösung des Kamerabilds. Lieber nicht verändern, da alle
Positionen im Kamerabild mit Konstanten gehardcoded sind.
PARCOURS_PFAD: Pfad zum Parcours-Bild. Zur Auswahl stehen momentan:
    - parcours_cold_RESIZED.JPG und
    - parcours_warm_RESIZED.JPG
black_lower_limit, black_lower_limit: schwarz-Grenzen im HSV-Farbschema
green_lower_limit, green_upper_limit: grün-Grenzen im HSV-Farbschema
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

#                                H  S  V
black_lower_limit = numpy.uint8([0, 0, 0])
black_upper_limit = numpy.uint8([255, 50, 100])
#                                R  G  B
#black_lower_limit = numpy.uint8([0, 0, 0])
#black_upper_limit = numpy.uint8([50, 50, 50])
#                                H  S  V
green_lower_limit = numpy.uint8([40, 80, 20])
green_upper_limit = numpy.uint8([80, 255, 255])

GRUEN = (0, 255, 0)
GELB = (0,255,255)
ROT = (0, 0, 255)

def line_slice(roi_kreuzung, dieser_frame, offset):
    """
    Zeichnet auf auf einem Schnit am gegebenen Y-Offset im Kamerabild die gefundenen
    Linienstückchen als grüne Rechtecke ein.
    Wird die eine Linie zu breit, wird das Rechteck rot eingefärbt.
    Das Zentrum aller Linienstückchen in einem Schnitt wird mit einem Punkt markiert.
    """
    yoffset = PIXEL_HOEHE - (PIXEL_HOEHE - 200) - 20 - offset
    # Horizontalen Streifen an y-Position "offset" herausschneiden
    roi_line = dieser_frame[PIXEL_HOEHE - 20 - offset:PIXEL_HOEHE - 1 - offset, 0:PIXEL_BREITE - 1]
    # in HSV-Farbschema umwandeln
    hsv = cv2.cvtColor(roi_line, cv2.COLOR_BGR2HSV)
    # Maske erstellen (Monochromes Bild: Linie weiß, alles andere schwarz)
    black_mask = cv2.inRange(hsv, black_lower_limit, black_upper_limit)
    # Konturen extrahieren
    _, konturen, _ = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cx = 0
    cy = yoffset+5
    cnt = 0
    farbe = GRUEN
    # Liste der X-Positionen der Zentren der gefundenen Linienstücke
    ret = []
    is_kreuzung = False
    for kontur in konturen:
        # Rechteck um die Kontur erhalten
        x, y, w, h = cv2.boundingRect(kontur)
        # zu kleine Konturen wegfiltern
        if w > 10:
            # zu große Konturen rot einfärben
            if w > 150:
                farbe = ROT
                is_kreuzung = True
            # sonst grün einfärben
            else:
                farbe = GRUEN
            # Rechteck um die Kontur zeichnen
            cv2.rectangle(roi_kreuzung, (x, y + yoffset), (x + w, y + yoffset + h), farbe, 2)
            # Summe aller x-Positionen der Zentren der gefundenen Rechtecke bilden
            cx = cx + int(x + w / 2)
            # Anzahl der gefundenen Rechecke mitzählen
            cnt = cnt + 1
            # Rote Rechtecke: X-Position ist 0 (Mitte des Kamerabildes)
            if is_kreuzung:
                ret.append(0)
            # Grüne Rechtecke: Abweichung von Bildmitte an Liste anfügen
            else:
                ret.append(cx - PIXEL_BREITE / 2)
    # keine Linienstücke gefunden: Durchnitt aller X-Positionen ist Bildmitte
    if cx is 0:
        cx = (PIXEL_BREITE - 1) / 2
    # Linienstückchen gefunden: Durchschnitt aller X-Positionen errechnen
    else:
        cx = cx / cnt
    # Kreis zeichnen an durchschnittlicher X-Position aller gefundenen Linienstückchen
    cv2.circle(roi_kreuzung, (int(cx), int(cy)), 5, farbe, -1)
    # Ergebnisliste zurückgeben: Liste der Abweichung der Linie von Mitte in Pixel
    return ret

def center_line(roi_kreuzung):
    """
    Senkrechte Linie in der Bildmitte einzeichnen
    """
    cv2.line(roi_kreuzung,(int((PIXEL_BREITE-1)/2),0),(int((PIXEL_BREITE-1)/2),PIXEL_HOEHE-1),GELB,1)

def green_squares(roi_kreuzung):
    """
    Grüne Areale ab einer gewissen Größe werden blau umrandet.
    """
    # in HSV-Farbschema konvertieren
    hsv2 = cv2.cvtColor(roi_kreuzung, cv2.COLOR_BGR2HSV)
    # Maske erstellen (Monochromes Bild: grüne Areale weiß, alles andere schwarz)
    green_mask = cv2.inRange(hsv2, green_lower_limit, green_upper_limit)
    # Konturen extrahieren
    _, konturen, _ = cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for kontur in konturen:
        # zu kleine Konturen wegfiltern
        if cv2.contourArea(kontur) > 4000:
            # Rechteck um die Kontur erhalten
            x, y, w, h = cv2.boundingRect(kontur)
            # Rechteck um die Kontur zeichnen
            cv2.rectangle(roi_kreuzung, (x, y), (x + w, y + h), (255, 0, 0), 2)

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
    bla = 0
    while True:
        # frame lesen
        dieser_frame = kamera.get_frame()
        # kleineren Ausschnitt des Bildes herausschneiden, damit die folgenden Schritte
        # etwas fixer gehen
        roi_kreuzung = dieser_frame[PIXEL_HOEHE - 200:PIXEL_HOEHE - 1, 0:PIXEL_BREITE - 1]
        # grüne Areale blau umranden
        green_squares(roi_kreuzung)
        # Auf Höhe 30 Pixel von Bildunterkante nach schwarzen Arealen suchen, einzeichnen
        # und X-Positionen der gefundenen Linienstückchen als Liste zurückgeben.
        lines = line_slice(roi_kreuzung, dieser_frame, 30)
        # Auf Höhe 90 Pixel von Bildunterkante nach schwarzen Arealen suchen und einzeichnen
        line_slice(roi_kreuzung, dieser_frame, 90)
        # Auf Höhe 150 Pixel von Bildunterkante nach schwarzen Arealen suchen und einzeichnen
        line_slice(roi_kreuzung, dieser_frame, 150)
        # Senkrechte Linie in der Mitte des Bildes zeichnen
        center_line(roi_kreuzung)

        # Kamerabild anzeigen
        cv2.imshow("Maze Runner", roi_kreuzung)

        # Motoren ansteuern
        if len(lines) > 0:
            # Linienstückchen gefunden
            motoren.set_speed(30, 30)
            # gefundene Linien ausgeben
            print(lines)
        else:
            # keine Linienstückchen gefunden
            motoren.set_speed(10, 10)
            print('No line on Sensor')

        # Pausieren mit p, bewegen mit w,a,s,d, rotieren mit q,e, beenden mit k
        # wird zum testen mit dem richtigen Roboter ersetzt durch cv2.waitKey(10)
        simulator.handle_interactive_mode(cv2.waitKey(10))

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
    simulator.close()
