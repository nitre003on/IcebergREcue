"""
Test, ob OpenCV korrekt installiert ist, indem die Versionsnummern ausgegeben werden.
"""
from cv2 import cv2

try:
    # Library Version in Teminal ausgeben
    print(cv2.__version__)

except KeyboardInterrupt:
    print("Abbruch durch Benutzer... Tschau!")
    pass

finally:
    print("Räume auf...")
