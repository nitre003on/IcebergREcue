"""
Liest den Time-of-Flight Abstandssensor aus.
Dies ist ein I2C-Sensor, d.h. auf dem Pi muss I2C aktiviert sein.

Die Messverzögerung des ToF-Sensors kann eingestellt werden:
Umso langsamer gemessen wird, umso genauer das Ergebnis und umgekehrt.
Verschiedene Messverzögerungen werden benutzt und die Messung sollte immer genauer werden.

Danach werden nur noch so schnell es geht Werte ausgegeben.

Abgeschrieben hier:
https://learn.adafruit.com/adafruit-vl53l0x-micro-lidar-distance-sensor-breakout/python-circuitpython
"""
try:
    import time
    import board
    import busio
    import adafruit_vl53l0x

    # 7-Bit Adressen:
    TOF_SENSOR_ADDRRESSE = 0x29       # Standardadresse
    #TOF_SENSOR_ADDRRESSE = 0x30      # alternative Adresse, die wir letztes Jahr in manche Tof-Sensoren geschrieben haben

    # SCL ist an Pin GPIO 3, SDA an Pin GPIO 2 angeschlossen
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    # Erzeuge Library-Object, dass auf den I2C-Bus (SCL und SDA) zugreift
    tof_sensor = adafruit_vl53l0x.VL53L0X(i2c_bus, address=TOF_SENSOR_ADDRRESSE)

    input("ToF-Sensor auf ein Objekt richten und dann nicht mehr bewegen. Weiter mit Enter...")

    print("Messungen werden gezeigt von ungenau zu genau:")
    # iteriere über Liste von Messverzögerungen
    for messverzoegerung in [25000, 50000, 100000, 200000]:
        # Messverzögerung setzen
        tof_sensor.measurement_timing_budget = messverzoegerung
        # Abstand messen und auslesen
        abstand = tof_sensor.range
        # Abstand ausgeben
        print("Abstand=%smm (Messverzoegerung=%sns)" % (abstand, messverzoegerung))

    print("Ab jetzt werden einfach nur noch Werte gelesen.")
    print("Der SensoPr darf also wieder bewegt werden.")
    input("Weiter mit Enter, beenden mit Strg+C...")

    # setze auf Standard-Messverzögerung zurück
    tof_sensor.measurement_timing_budget = 20000
    # Endlosschleife:
    while True:
        # Abstand messen und auslesen
        abstand = tof_sensor.range
        # Abstand ausgeben
        print("Abstand=%smm" % (abstand))
        #time.sleep(0.5) # reinkommentieren, um es langsamer zu machen

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
