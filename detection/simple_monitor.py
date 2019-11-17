import os
import time

if __name__ == '__main__':

    WAVE_OUTPUT_FILENAME = "output.wav"

    creation_time = 0
    while True:
        time.sleep(0.1)
        if os.stat(WAVE_OUTPUT_FILENAME).st_ctime > creation_time:
            print('file changed.')
