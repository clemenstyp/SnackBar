import json
import threading

import paho.mqtt.publish as mqtt_publish

from Snackbar.Helper.Database import settings_for


def send_webhook(coffeeDict):
    webhook_thread = threading.Thread(target=send_webhook_now, args=(coffeeDict,))
    webhook_thread.start()


def send_webhook_now(coffeeDict):
    if settings_for('publishToMqtt') == 'true' and settings_for('mqttTopic') != '' and settings_for(
            'mqttServer') != '' and settings_for('mqttPort') != '':
        data_out = json.dumps(coffeeDict)

        broker_url = settings_for('mqttServer')
        broker_port = int(settings_for('mqttPort'))
        broker_topic = settings_for('mqttTopic')

        mqtt_publish.single(broker_topic, payload=data_out, hostname=broker_url, port=broker_port)
