
import threading
import select
import socket
import Queue
import json
from logger import Logger
from parser import SerialParser

class TCPServer(object):

    def __init__(self):
        self.log = Logger()
        self._listener_thread = threading.Thread(target=self._listener)
        self._listener_thread.setDaemon(True)
        self._alive = False
        self._lock = threading.Lock()
        self._clients = []
        self._server = None

    def is_alive(self):
        return self._alive

    def bind(self, hostname, port):
        self._alive = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind((hostname, port))
        self._server.listen(1)
        self._listener_thread.start()
        self.log.info("%s listening on %s %d" % (self.__class__.__name__, hostname, port))

    def close(self):
        if self._alive:
            self._alive = False
            self._server.close()
            self._listener_thread.join()
            self.log.info("TcpServer closed")

    def _handle_client(self, skt, addr):
        self.log.info("Client connected: %s %d" % (addr[0], skt.fileno()))
        self.handle_client(skt, addr)
        self.log.info("Client disconnected: %s %d" % (addr[0], skt.fileno()))
        self._lock.acquire()
        self._clients.remove(skt)
        self._lock.release()
        skt.close()

    def send_to_all(self, data):
        self._lock.acquire()
        clients = list(self._clients)
        self._lock.release()
        for client in clients:
            try:
                client.send(data)
            except:
                self.log.error("Failed to send data to client %s" % client)


    def handle_client(self, skt, addr):
        while 1:
            try:
                data = skt.recv(1024)
                if not data:
                    break
                self.log.debug("Data received: %s" % data)
            except Exception, e:
                self.log.error(str(e))
                break

    def _listener(self):
        while self._alive:
            rd, wr, err = select.select([self._server], [], [])
            for s in rd:
                if s is self._server:
                    try:
                        client_skt, client_addr = self._server.accept()
                        self._lock.acquire()
                        self._clients.append(client_skt)
                        self._lock.release()
                        threading._start_new_thread(self._handle_client, (client_skt, client_addr))
                    except Exception, e:
                        break

        #self._server.close()


class PigeonServer(TCPServer):

    def __init__(self):
        super(PigeonServer, self).__init__()
        self._pgn_thread = threading.Thread(target=self._run)
        self._pgn_thread.setDaemon(True)
        self._request_to_quit = False
        self._cond = threading.Condition()
        self._waiting_for_cond = False
        self._queue = Queue.Queue()
        self._reply_text = ""
        self.pgn_prefix = "pgn_"

    def _run(self):
        self.log.info("%s is running..." % self.__class__.__name__)
        while self._request_to_quit is False:
            pgn = self._queue.get()
            if "pgn" in pgn.keys():
                self._handle_pgn(pgn)

    def run(self, cli=False):
        self._pgn_thread.start()
        if cli:
            while True:
                input_text = raw_input()
                self.handle_pgn_serial_data(input_text)
                if input_text == "quit":
                    break
        self._pgn_thread.join()

    def pgn_quit(self):
        self._request_to_quit = True
        self._queue.put({"dum": "my"})
        self._pgn_thread.join()

    def pgn_reply(self, text):
        if self._waiting_for_cond is True:
            self._cond.acquire()
            self._reply_text = text
            self._cond.notify()
            self._cond.release()
        else:
            self.log.error("Not waiting for a reply (%s)" % text)

    def _handle_message(self, text):
        self.log.debug("Message: %s" % text)
        for skt in self._clients:
            skt.send(json.dumps(text) + "\r\n")

    def message(self, text, params={}, meta=""):
        self._handle_message({"message": {
            "origin": self.__class__.__name__,
            "meta": meta,
            "text": text,
            "params": params,
            }})

    def ask(self, text, meta=""):
        self._waiting_for_cond = True
        self.message(text, meta=meta)
        self._cond.acquire()
        self._cond.wait()
        self._cond.release()
        self._waiting_for_cond = False
        return self._reply_text


    def bind(self, hostname, port):
        super(PigeonServer, self).bind(hostname, port)
        self.message("", meta="server.connected")

    def close(self):
        if self.is_alive():
            self.message("", meta="server.disconnected")
        super(PigeonServer, self).close()


    def use_prefix(self, prefix):
        self.pgn_prefix = prefix

    def _handle_pgn(self, pgn):
        if "pgn" not in pgn.keys():
            # Invalid RPC. And that's fine.
            self.log.debug("invalid method/function: element not found")
            return
        pgn = pgn["pgn"]
        pgn_method = pgn["method"]
        pgn_params = pgn["params"]

        try:
            pgn_cb = getattr(self, self.pgn_prefix + pgn_method)
        except Exception, e:
            self.log.error("Function/method not implemented: %s" % pgn_method)
            return

        def _call_callback():
            pgn_cb(**pgn_params)

        threading._start_new_thread(_call_callback, ())


    def handle_pgn_serial_data(self, data):
        data = data.replace('\r', '')
        data = data.replace('\n', '')
        fields = data.split(' ')
        if len(fields) < 1:
            self.log.debug("Invalid DATA:", data)
        else:
            method = fields[0]
            params = {}
            for param in fields[1:]:
                param_fields = param.split("=")
                if len(param_fields) == 2:
                    param_name = param_fields[0]
                    param_value = param_fields[1]
                    if param_value.isdigit():
                        param_value = int(param_value)
                    params.update({param_name: param_value})
            pgn_pkt = {
                "pgn": {
                    "method": method,
                    "params": params,
                }
            }
            self._queue.put(pgn_pkt)

    def handle_client(self, skt, addr):

        data_parser = SerialParser()
        data_parser.set_callback("parsed", self.handle_pgn_serial_data)
        while 1:
            try:
                data = skt.recv(1024)
                if not data:
                    break
                data_parser.parse_data(data)
            except Exception, e:
                self.log.error(str(e))
                break


if __name__ == "__main__":
    class App(PigeonServer):

        def pgn_greeting(self, text):
            self.message("Hello %s!" % text, meta="hello")
            while self.ask("Do you want me to say it again?", meta="hello_again?") == "yes":
                self.message("Hello again %s!" % text, meta="hello_again")

    app = App()
    app.bind("localhost", 1234)
    app.run(True)