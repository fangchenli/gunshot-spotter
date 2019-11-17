import os
import time
import pickle

import numpy as np
import librosa
from doa import get_direction

if __name__ == '__main__':

    model_name = "save_training_2.pickle"
    WAVE_OUTPUT_FILENAME = "output.wav"
    feature_length = 880

    # load model
    with open(model_name, 'rb') as file:
        clf = pickle.load(file, encoding='latin1')

    creation_time = 0
    while True:
        time.sleep(0.1)
        curr_ctime = os.stat(WAVE_OUTPUT_FILENAME).st_ctime
        if curr_ctime > creation_time:

            creation_time = curr_ctime

            time1 = time.time()

            # load audio using librosa package
            y, sr = librosa.load(WAVE_OUTPUT_FILENAME, duration=1, mono=False)

            # extracting MFCC feature of audio
            s = librosa.feature.mfcc(y=np.asfortranarray(y[0, :]), sr=sr, hop_length=512, n_mfcc=20)
            s = s.flatten()
            s = np.resize(s, feature_length)

            time2 = time.time()

            print(s.shape)
            if clf.predict([s]) == 1:
                print('safe.')
            else:
                time3 = time.time()
                print(f'gunshot detected. time: {creation_time}. loading: {time2 - time1}. inference: {time3 - time2}')
                direction = get_direction(y)
                print(direction)
