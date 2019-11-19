import logging
import json
import greengrasssdk

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_client = greengrasssdk.client('iot-data')

send_topic = 'sns/message'

detectors = []


alert_message = {'request': {'message': 'Shots fired.'}}


def function_handler(event, context):

    global detectors

    logger.info(event)

    message = event['current']['state']['reported']

    if message['gunshot'] == 'yes':
        direction = message['direction']
        amplitude = message['amplitude']
        index = message['index']

        detectors.append(index)

        logger.info(detectors)

        iot_client.publish(topic=send_topic, payload=json.dumps(alert_message))
