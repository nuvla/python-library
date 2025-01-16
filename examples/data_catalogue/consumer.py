import json
import queue
from pprint import pprint

import paho.mqtt.client as mqtt

from nuvla.api import Api as Nuvla
from nuvla.api.models import CimiResource


class DataConsumer:
    def __init__(self, nuvla: Nuvla, topic: str, host: str, port: int):
        self.nuvla: Nuvla = nuvla
        self.topic: str = topic
        self.host = host
        self.port = port

        self.mqtt_client: mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.link_queue: queue.Queue = queue.Queue()

    def on_connect(self, cli, userdata, flags, rc, properties=None):

        if rc == 0:
            print("Connected to broker")
            self.mqtt_client.subscribe(self.topic)
        else:
            print("Connection failed")

    def _get_dr_from_message(self, message) -> CimiResource | None:
        t = json.loads(message.payload.decode())
        m_str = json.dumps(t, indent=4)
        print(f"Received message: \n{m_str}\n on topic {message.topic}")

        dr_id: str = t.get("resource_uri", None)
        if not dr_id or "api/data-record" not in dr_id:
            print("No resource URI in message")
            return None

        dr_id = dr_id.replace("api/", "")
        pprint("Data record ID: " + dr_id)
        return self.nuvla.get(dr_id)

    def on_message(self, cli, userdata, message):
        try:
            dr_obj = self._get_dr_from_message(message)
            if not dr_obj.data:
                return

            data_object = dr_obj.data.get("data-object", None)

            if not data_object:
                print("No data object in data record")
                return

            dr_obj = self.nuvla.get(data_object)
            link = self.nuvla.operation(dr_obj, "download")

            self.link_queue.put(link)

        except Exception as e:
            print(f"Error processing message: {e}")

    def listen(self):
        """
        Listen to the data catalogue for new events
        """
        self.mqtt_client.connect(self.host, self.port)
        self.mqtt_client.loop_start()
