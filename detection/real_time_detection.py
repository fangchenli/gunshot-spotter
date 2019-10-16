import pyaudio
import wave
import librosa
import numpy as np
import pickle
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import json
from os.path import join

AllowedActions = ['both', 'publish', 'subscribe']


# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


host = 'a1nspdoka830y9-ats.iot.us-west-2.amazonaws.com'
rootCAPath = 'root.ca.pem'
certificatePath = '0ac1cc55b6-certificate.pem.crt'
privateKeyPath = '0ac1cc55b6-private.pem.key'
port = 8883
useWebsocket = False
clientId = 'Detector'
topic = 'pi/gunshot'
mode = 'both'

path = '/home/pi/detector'
feature_length = 880  # feature vector length
CHUNK = 1024  # size of each data frame in which audio will be recorded
FORMAT = pyaudio.paInt16
CHANNELS = 1  # recording channel
RATE = 22050  # sampling rate
RECORD_SECONDS = 1
RESPEAKER_INDEX = 2
model_name = "save_training_2.pickle"
WAVE_OUTPUT_FILENAME = 'background.wav'

model_path = join(path, model_name)
output_path = join(path, WAVE_OUTPUT_FILENAME)
num_frame = int(RATE / CHUNK * RECORD_SECONDS)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# start PyAudio instance
p = pyaudio.PyAudio()


# audio recording and gunshot detection
def detect():
    # load model
    load_training = open(model_path, 'rb')
    clf = pickle.load(load_training, encoding='latin1')  # LOAD TRAINED CLASSIFIER
    load_training.close()

    while True:

        # opening stream for recording audio with given parameters
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=RESPEAKER_INDEX, )

        frames = []
        # here audio is recorded for time according to given parameters and data is stored in frames
        for i in range(0, num_frame):
            data = stream.read(CHUNK)
            frames.append(data)
        stream.stop_stream()
        stream.close()

        # now open a wave file with a specified name to store the audio
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()  # storing of audio is done till here

        # load audio using librosa package
        y, sr = librosa.load(output_path, duration=1)
        # extracting MFCC feature of audio
        s = librosa.feature.mfcc(y=y, sr=sr, hop_length=512, n_mfcc=20)
        s = np.reshape(s, np.product(s.shape))
        # making shape equal to 880 equal to feature vector length

        diff_length = feature_length - s.shape[0]
        # padding_length_before = diff_length // 2
        # padding_length_after = diff_length - padding_length_before
        if s.shape[0] < feature_length:
            # s = np.pad(s, (padding_length_before, padding_length_after), 'constant', constant_values=0)
            s = np.concatenate((s, s[s.shape[0] - diff_length:]))
        else:
            s = s[0:feature_length]

        if clf.predict([s]) == 1:
            pass
        else:
            message = {'message': 'gunshot detected'}
            myAWSIoTMQTTClient.publish(topic, json.dumps(message), 1)


if __name__ == '__main__':

    try:
        detect()
    except KeyboardInterrupt:
        print('\nterminating...\n')
        p.terminate()
