import os
import time

WAVE_OUTPUT_FILENAME = "output.wav"

while True:

    time.sleep(1)

    fileStat = os.stat(WAVE_OUTPUT_FILENAME)

    print(fileStat)
