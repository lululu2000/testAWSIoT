#!/usr/bin/env python
"""Send temperature data from Raspberry Pi to AWS IoT."""
import logging
import time
import json
import glob
import os
from datetime import datetime, timezone
from random import uniform
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# temperature file location
BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_FOLDER = glob.glob(BASE_DIR + '28*')[0]
DEVICE_FILE = DEVICE_FOLDER + '/w1_slave'
# parameters for mqtt test
END_POINT = os.getenv("END_POINT", \
                      "a2hiwzd7btpoi4.iot.ap-northeast-1.amazonaws.com")
ROOT_CA_PATH = os.getenv("ROOT_CA_PATH", "root.pem")
CERT_PATH = os.getenv("CERT_PATH", "certificate.pem.crt")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "private.pem.key")
CLIENT_ID = os.getenv("CLIENT_ID", "test-device")
TOPIC = os.getenv("TOPIC", \
                  "andes/temperature/develop/developtemp/n119w82wgdh1")

def read_temp_file():
    """Read temperature file"""
    tempfile = open(DEVICE_FILE, 'r')
    lines = tempfile.readlines()
    tempfile.close()
    return lines

def read_temp():
    """Get temperature from file"""
    lines = read_temp_file()
    if lines[0].strip()[-3:] != 'YES':
        print("Failed to get temperature.")
        raise Exception("Failed to get temperature.")
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    else:
        raise Exception("Failed to get temperature.")

def log_configure():
    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - ' + \
            '%(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def custom_callback(client, userdata, message):
    """ Custom MQTT message callback"""
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

def mqtt_init():
    # get work directory
    work_path = os.path.dirname(os.path.abspath(__file__))
    # Init AWSIoTMQTTClient
    mqtt_client = None
    mqtt_client = AWSIoTMQTTClient(CLIENT_ID)
    mqtt_client.configureEndpoint(END_POINT, 8883)
    mqtt_client.configureCredentials( \
        os.path.join(work_path, ROOT_CA_PATH), \
        os.path.join(work_path, PRIVATE_KEY), \
        os.path.join(work_path, CERT_PATH))
    # AWSIoTMQTTClient connection configuration
    mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
    mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
    mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
    mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
    return mqtt_client

def mqtt_transfer():
    # init logger
    log_configure()

    # init MQTTClient
    mqtt_client = mqtt_init()

    # Connect and subscribe to AWS IoT
    mqtt_client.connect()
    # mqtt_client.subscribe(TOPIC, 1, custom_callback)
    time.sleep(2)

    # Publish to the same topic in a loop forever
    while True:
        try:
            msg = {}
            data = {}
            data['temperature'] = read_temp()
            data['humidity'] = uniform(0.0, 100.0)
            loc = {}
            loc['lon'] = uniform(139.0, 141.0)
            loc['lat'] = uniform(35.0, 37.0)
            data['location'] = loc
            msg['@timestamp'] = datetime.now().astimezone().isoformat()
            msg['data'] = data
            message_json = json.dumps(msg)
            mqtt_client.publish(TOPIC, message_json, 1)
            print('Published topic %s: %s\n' % (TOPIC, message_json))
        except Exception as ex:
            print(ex)
        finally:
            pass
        time.sleep(1)

if __name__ == '__main__':
    """ main process: read temperature file and send it to AWS IoT """
    mqtt_transfer()
