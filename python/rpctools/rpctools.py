import time
import threading
import socket
import select
import json
import Queue

class Logger():
    NONE = 0
    INFO = 0x01
    WARNING = 0x02
    ERROR = 0x04
    DEBUG = 0x08
    ALL = 0x0FF

    default_levels = ALL

    _logs = []

    def __init__(self):
        self._levels = Logger.default_levels  # all by default
        self._verbose = False
        self._custom_logger = None
        Logger._logs.append(self)

    def __del__(self):
        Logger._logs.remove(self)

    @staticmethod
    def global_set_levels(levels):
        for log in Logger._logs:
            log.set_levels(levels)

    @staticmethod
    def global_set_logger(custom_logger):
        for log in Logger._logs:
            log.set_logger(custom_logger)

    @staticmethod
    def global_set_verbose(verbose):
        for log in Logger._logs:
            log.set_verbose(verbose)



    def set_levels(self, levels):
        self._levels = levels

    def set_logger(self, custom_logger):
        self._custom_logger = custom_logger

    def set_verbose(self, verbose):
        self._verbose = verbose

    def info(self, message):
        self._log(Logger.INFO, message)

    def warning(self, message):
        self._log(Logger.WARNING, message)

    def error(self, message):
        self._log(Logger.ERROR, message)

    def debug(self, message):
        self._log(Logger.DEBUG, message)

    def _log(self, type, message):
        if (type & self._levels) == 0:
            return

        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
        type_str = "[?????]"
        if type is Logger.INFO:
            type_str = "[INFO] "
        elif type is Logger.WARNING:
            type_str = "[WARN] "
        elif type is Logger.ERROR:
            type_str = "[ERROR]"
        elif type is Logger.DEBUG:
            type_str = "[DEBUG]"

        text = "%s %s %s" % (timestamp, type_str, message)

        if self._custom_logger is not None:
            if self._verbose:
                print(text)
            self._custom_logger(text)
        else:
            print(text)

class DataParser(object):
    def __init__(self):
        self.parsed_str = ""
        self._callback = {
            "parsed": None
        }

    def set_callback(self, name, cb):
        self._callback[name] = cb

    def clear(self):
        self.parsed_str = ""


class SerialParser(DataParser):
    def __init__(self):
        super(SerialParser, self).__init__()

    def parse_data(self, data):
        for ch in data:
            if ch == '\n':
                if self._callback["parsed"] is not None:
                    self._callback["parsed"](self.parsed_str)
                    self.parsed_str = ""
            else:
                self.parsed_str += ch


class JsonParser(DataParser):
    def __init__(self):
        super(JsonParser, self).__init__()
        self._parse_level = 0
        self._in_str = False
        self._esc_char = False

    def parse_data(self, data):
        done = False
        for ch in data:
            if ch == '\"':
                if not self._in_str:
                    self._in_str = True
                else:
                    if not self._esc_char:
                        self._in_str = False
                    else:
                        self._esc_char = False

            if self._in_str:
                if ch == "\\":
                    self._esc_char = True
            else:
                if ch == '{':
                    if self._parse_level == 0:
                        self.parsed_str = ""
                    self._parse_level += 1
                elif ch == '}':
                    self._parse_level -= 1
                    if self._parse_level == 0:
                        done = True

            self.parsed_str += ch

            if done and self._callback["parsed"] is not None:
                self._callback["parsed"](self.parsed_str)

class RPCServer(object):

    def __init__(self):
        self._rpc_thread = threading.Thread(target=self._run)
        self._rpc_thread.daemon = True
        self._tcp_listener = threading.Thread(target=self._listener)
        self._tcp_listener.setDaemon(True)
        self._server = None
        self._alive = False
        self._request_to_quit = False
        self._clients = []
        self._lock = threading.Lock()
        self._queue = Queue.Queue()
        self.log = Logger()
        self.rpc_prefix = "rpc_"

    def _run(self):
        self.log.info("%s is running..." % self.__class__.__name__)
        while self._request_to_quit is False:
            rpc = self._queue.get()
            if "rpc" in rpc.keys():
                self._handle_rpc(rpc)

    def run(self, cli=False):
        if cli:
            self._rpc_thread.start()
            while True:
                input_text = raw_input()
                self.handle_rpc_serial_data(input_text)
                if input_text == "quit":
                    break
            self._rpc_thread.join()
        else:
            self._run()

    def rpc_quit(self):
        self._request_to_quit = True

    def _handle_message(self, text):
        self.log.debug("Message: %s" % text)
        for skt in self._clients:
            skt.send(json.dumps(text))

    def message(self, text, params={}, meta=""):
        self._handle_message({"message": {
            "origin": self.__class__.__name__,
            "meta": meta,
            "text": text,
            "params": params,
            }})

    def connect(self, hostname, port):
        self._alive = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind((hostname, port))
        self._server.listen(1)
        self._tcp_listener.start()
        self.message("", meta="server.connected")

    def disconnect(self):
        self._alive = False
        #self._thread_listener.join(10000)
        self.message("", meta="server.disconnected")
        self._server.fileno()
        #self._server.shutdown(socket.SHUT_RD)
        self._server.close()

    def _listener(self):
        while self._alive:
            rd, wr, err = select.select([self._server], [], [])
            for s in rd:
                if s is self._server:
                    client_skt, client_addr = self._server.accept()
                    self._lock.acquire()
                    self._clients.append(client_skt)
                    self._lock.release()
                    threading._start_new_thread(self._handle_client, (client_skt, client_addr))
        self._server.close()
        print("Server closed")

    def use_prefix(self, prefix):
        self.rpc_prefix = prefix

    def _handle_rpc(self, rpc):
        if "rpc" not in rpc.keys():
            # Invalid RPC. And that's fine.
            self.log.debug("invalid RPC: \"rpc\" element not found")
            return
        rpc = rpc["rpc"]
        rpc_method = rpc["method"]
        rpc_params = rpc["params"]

        try:
            rpc_cb = getattr(self, self.rpc_prefix + rpc_method)
        except Exception, e:
            self.log.error("RPC not implemented: %s" % rpc_method)
            return

        rpc_cb(**rpc_params)


    def handle_rpc_serial_data(self, data):
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
                rpc_pkt = {
                    "rpc": {
                        "method": method,
                        "params": params,
                    }
                }
                self._queue.put(rpc_pkt)

    def _handle_client(self, skt, addr):
        self.log.info("Client connected: %s %d" % (addr[0], skt.fileno()))

        data_parser = SerialParser()
        data_parser.set_callback("parsed", self.handle_rpc_serial_data)
        while 1:
            try:
                data = skt.recv(1024)
                if not data:
                    break
                data_parser.parse_data(data)
            except Exception, e:
                self.log.error(str(e))
                break
        self._lock.acquire()
        self._clients.remove(skt)
        self._lock.release()
        self.log.info("Client disconnected: %s %d" % (addr[0], skt.fileno()))
        skt.close()

class RPCClient(object):

    def __init__(self):
        self._alive = True
        self._json_parser = JsonParser()
        self._json_parser.set_callback("parsed", self._handle_json)
        self.log = Logger()

    def connect(self, hostname, port):
        print "CONNECT CLIENT"
        self._alive = True
        self._thread_listener = threading.Thread(target = self._listener)
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
        self._skt.write(text + "\n\r")

    def handle_message(self, message):
        pass

    def _handle_json(self, json_str):
        json_data = json.loads(json_str)
        if "message" in json_data.keys():
            self.handle_message(json_data)

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
