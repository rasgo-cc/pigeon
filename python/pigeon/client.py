
import json
import socket
import threading
import select
from parser import JsonParser
from logger import Logger

class PigeonClient(object):

    def __init__(self):
        self._alive = True
        self._json_parser = JsonParser()
        self._json_parser.set_callback("parsed", self._handle_json)
        self.log = Logger()

    def connect(self, hostname, port):
        self._alive = True
        self._thread_listener = threading.Thread(target=self._listener)
        self._thread_listener.setDaemon(True)
        self._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._skt.connect((hostname, port))
        self._thread_listener.start()

    def disconnect(self):
        self._alive = False
        self._skt.shutdown(socket.SHUT_RDWR)
        self._skt.close()
        self._thread_listener.join(3000)

    def send_data(self, text):
        self._skt.send(text + "\n\r")

    def handle_message(self, message):
        self.log.debug("Message received: %s" % message)
        pass

    def _handle_json(self, json_str):
        json_data = json.loads(json_str)
        if "message" in json_data.keys():
            self.handle_message(json_data["message"])

    def _listener(self):
        while self._alive:
            input,output,err = select.select([self._skt],[],[])
            for rd in input:
                if self._alive is True:
                    try:
                        data = rd.recv(1)
                        self._json_parser.parse_data(data)
                    except:
                        self._alive = False
                        break
