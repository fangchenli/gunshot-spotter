from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import logging
import time
import json
import pickle
import os
import re

from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException

import numpy as np
import librosa

from doa import get_direction


# Custom Shadow callback for updating the desired state in the shadow
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~Shadow Update Accepted~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


# function does basic regex check to see if value might be an ip address
def isIpAddress(value):
    match = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}', value)
    if match:
        return True
    return False


# function reads host GGC ip address from filePath
def getGGCAddr(filePath):
    f = open(filePath, "r")
    return f.readline()


# Used to discover GGC group CA and end point. After discovering it persists in GROUP_PATH
def discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId):
    # Progressive back off core
    backOffCore = ProgressiveBackOffCore()

    # Discover GGCs
    discoveryInfoProvider = DiscoveryInfoProvider()
    discoveryInfoProvider.configureEndpoint(host)
    discoveryInfoProvider.configureCredentials(iotCAPath, certificatePath, privateKeyPath)
    discoveryInfoProvider.configureTimeout(10)  # 10 sec
    print("Iot end point: " + host)
    print("Iot CA Path: " + iotCAPath)
    print("GGAD cert path: " + certificatePath)
    print("GGAD private key path: " + privateKeyPath)
    print("GGAD thing name : " + clientId)
    retryCount = MAX_DISCOVERY_RETRIES
    discovered = False
    groupCA = None
    coreInfo = None
    while retryCount != 0:
        try:
            discoveryInfo = discoveryInfoProvider.discover(clientId)
            caList = discoveryInfo.getAllCas()
            coreList = discoveryInfo.getAllCores()

            # In this example we only have one core
            # So we pick the first ca and core info
            groupId, ca = caList[0]
            coreInfo = coreList[0]
            print("Discovered GGC: " + coreInfo.coreThingArn + " from Group: " + groupId)
            hostAddr = ""

            # In this example Ip detector lambda is turned on which reports
            # the GGC hostAddr to the CIS (Connectivity Information Service) that stores the
            # connectivity information for the AWS Greengrass core associated with your group.
            # This is the information used by discovery and the list of host addresses
            # could be outdated or wrong and you would normally want to
            # validate it in a better way.
            # For simplicity, we will assume the first host address that looks like an ip
            # is the right one to connect to GGC.
            # Note: this can also be set manually via the update-connectivity-info CLI
            for addr in coreInfo.connectivityInfoList:
                hostAddr = addr.host
                if isIpAddress(hostAddr):
                    break

            print("Discovered GGC Host Address: " + hostAddr)

            print("Now we persist the connectivity/identity information...")
            groupCA = GROUP_PATH + CA_NAME
            ggcHostPath = GROUP_PATH + GGC_ADDR_NAME
            if not os.path.exists(GROUP_PATH):
                os.makedirs(GROUP_PATH)
            groupCAFile = open(groupCA, "w")
            groupCAFile.write(ca)
            groupCAFile.close()
            groupHostFile = open(ggcHostPath, "w")
            groupHostFile.write(hostAddr)
            groupHostFile.close()

            discovered = True
            print("Now proceed to the connecting flow...")
            break
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            retryCount -= 1
            print("\n" + str(retryCount) + "/" + str(MAX_DISCOVERY_RETRIES) + " retries left\n")
            print("Backing off...\n")
            backOffCore.backOff()

    if not discovered:
        print("Discovery failed after " + str(MAX_DISCOVERY_RETRIES) + " retries. Exiting...\n")
        sys.exit(-1)


MAX_DISCOVERY_RETRIES = 10  # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"  # directory storing discovery info
CA_NAME = "root-ca.crt"  # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"  # stores GGC host address

host = 'a1nspdoka830y9-ats.iot.us-west-2.amazonaws.com'
iotCAPath = 'root.ca.pem'
certificatePath = 'pi01.cert.pem'
privateKeyPath = 'pi01.private.key'
thingName = 'PI_01'
clientId = 'PI_01'

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)  # set to logging.DEBUG for additional logging
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

if not os.path.isfile('./groupCA/root-ca.crt'):
    discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId)
else:
    print("Greengrass core has already been discovered.")

# read GGC Host Address from file
ggcAddrPath = GROUP_PATH + GGC_ADDR_NAME
rootCAPath = GROUP_PATH + CA_NAME
ggcAddr = getGGCAddr(ggcAddrPath)
print("GGC Host Address: " + ggcAddr)
print("GGC Group CA Path: " + rootCAPath)
print("Private Key of trafficLight thing Path: " + privateKeyPath)
print("Certificate of trafficLight thing Path: " + certificatePath)
print("Client ID(thing name for trafficLight): " + clientId)
print("Target shadow thing ID(thing name for trafficLight): " + thingName)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(ggcAddr, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# # payload = {'state': {'desired': {'safety': 'shot'}}}
# JSONPayload = '{"state":{"reported":{"property":' + '"' + 'WoW' + '"}}}'
# deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)

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
        s = librosa.feature.mfcc(y=np.asfortranarray(y[1, :]), sr=sr, hop_length=512, n_mfcc=20)
        s = s.flatten()
        s = np.resize(s, feature_length)

        time2 = time.time()

        payload = {'timestamp': time1}
        if clf.predict([s]) == 1:
            print('safe.')
        else:
            time3 = time.time()
            print(f'gunshot detected. time: {creation_time}. loading: {time2 - time1}. inference: {time3 - time2}')
            direction = get_direction(y)
            print(direction)

            payload = {'state': {'reported': {'safety': 'shot'}}}

            deviceShadowHandler.shadowUpdate(json.dumps(payload), customShadowCallback_Update, 5)
