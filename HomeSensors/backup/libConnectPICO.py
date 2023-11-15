import socket
import json
import sys
import struct
from main import actions

pending_messages = []
kill = False


class Connection:
    def __init__(self, sock, addr):
        self.sock: socket.socket = sock
        self.addr = addr
        self.jsonHeader = None
        self.request = None
        self._buffer = b""
        self._lenJSON = None

    def _read(self):
        try:
            data = self.sock.recv(4096)
        except OSError:
            print("\n\n!!! ERROR READ -> \t\n\n", sys.exc_info()[0])
            pass
        else:
            if data:
                self._buffer += data
            else:
                raise RuntimeError("!!! Server closed connection")

    def write(self):
        while pending_messages:
            print("\t# Sending data...", end=" ")
            message = pending_messages.pop()
            try:
                self.sock.send(message)
                print("\tOK!")
            except OSError as e:
                print("\tFailed!\n")
                raise RuntimeError("!!! Server closed connection")

    def read(self):
        print("\t# Getting data...", end=" ")
        self._resetParams()
        self._read()

        if self._lenJSON is None:
            # print("\t\t-> Getting len...")
            self.getLenJSON()

        if self._lenJSON is not None and self.jsonHeader is None:
            # print("\t\t-> Getting JSON Header...")
            self.getJSONHeader()

        if self.jsonHeader and self.request is None:
            # print("\t\t-> Getting request...")
            self.getRequest()

    def queue_request(self, request):
        content = request["content"]
        req = {
            "content_bytes": self._encodeJSON(content),
        }
        message = self._createMessage(**req)
        pending_messages.append(message)

    def _encodeJSON(self, obj):
        return json.dumps(obj).encode("utf-8")

    def _decodeJSON(self, bytesJSON):
        return json.loads(bytesJSON)

    def _createMessage(self, *, content_bytes):
        jsonHeader = {
            "byteorder": sys.byteorder,
            "content-length": len(content_bytes),
        }
        jsonHeaderBytes = self._encodeJSON(jsonHeader)
        messageHdr = struct.pack(">H", len(jsonHeaderBytes))
        message = messageHdr + jsonHeaderBytes + content_bytes
        return message

    def getLenJSON(self):
        hdrlen = 2
        if len(self._buffer) >= hdrlen:
            self._lenJSON = struct.unpack(
                ">H", self._buffer[:hdrlen]
            )[0]
            self._buffer = self._buffer[hdrlen:]

    def getJSONHeader(self):
        hdrlen = self._lenJSON
        if len(self._buffer) >= hdrlen:
            self.jsonHeader = self._decodeJSON(self._buffer[:hdrlen])
            self._buffer = self._buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
            ):
                if reqhdr not in self.jsonHeader:
                    raise ValueError(f"Missing required header '{reqhdr}'.")

    def _resetParams(self):
        self._lenJSON = None
        self.jsonHeader = None
        self.request = None

    def getRequest(self):
        contLen = self.jsonHeader["content-length"]

        if not len(self._buffer) >= contLen:
            print("\tFailed -> Not Same Len!")
            return
        data = self._buffer[:contLen]
        self._buffer = self._buffer[contLen:]
        self.request: dict = self._decodeJSON(data)
        print("\tOK!")

    def close(self):
        print(f"Closing connection to {self.addr}")
        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")
        sys.exit()


def initConnectRPI(host, port):
    print("Connecting to RPI...", end=" ")
    addr = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(addr)
        print(f'\tOK!:  {addr}')
    except OSError as e:
        print(f'\n\tFailed!: {e}')
        sys.exit()

    m = Connection(s, addr)
    return m


def listenerWorker(conn: Connection):
    print(f"Starting listener...")
    while True:
        try:
            print("Listening...", end=" ")
            conn.read()
            data: dict = conn.request
            print(f"\t* Action: {data['function']} -> {data['args']}")
            actions(data["function"], data["args"])
        except Exception as e:
            print(f"\n\n!!! ERROR LISTENER -> \t {e}\n\n")
            conn.close()
            break

    global kill
    kill = True
    print("Killing listener :(...")
    sys.exit()


def senderWorker(conn: Connection, sensorData):
    global kill
    if kill is True:
        print("Killing sender...")
        sys.exit()

    sensorData = {"data": sensorData}
    request = {"content": sensorData}
    conn.queue_request(request)
    try:
        conn.write()
        return
    except Exception as e:
        print(f"\n\n!!! ERROR SENDER -> \t {e}\n\n")
        kill = True
        conn.close()
    print("Ending sender :(...")
