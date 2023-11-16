import socket
import json
import sys
import struct
from micropython import const

EVENT_READ = const(0)
EVENT_WRITE = const(1)


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


class Connection:
    def __init__(self, sock, addr):
        self.sock: socket.socket = sock
        self.addr = addr
        self.responseCreated = False
        self.jsonHeader: dict = {}
        self.request: dict = {}
        self.mask = EVENT_WRITE
        self._lenJSON: int = 0
        self._buffer = b""
        self._sendBuffer = b""

    def close(self):
        print(f"Closing connection to {self.addr}")
        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")
        finally:
            self.sock = socket.socket()

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
                "content-type"
            ):
                if reqhdr not in self.jsonHeader:
                    raise ValueError(f"Missing required header '{reqhdr}'.")

    def getRequest(self):
        contLen = self.jsonHeader["content-length"]

        if not len(self._buffer) >= contLen:
            print("\tFailed -> Not Same JSON Len!")
            return
        data = self._buffer[:contLen]
        self._buffer = self._buffer[contLen:]
        self.request = self._decodeJSON(data)

    def _resetParams(self):
        self._lenJSON = 0
        self.jsonHeader = {}
        self.request = {}
        self.responseCreated = False

    def _encodeJSON(self, obj):
        return json.dumps(obj).encode("utf-8")

    def _decodeJSON(self, bytesJSON):
        return json.loads(bytesJSON)

    def _read(self):
        try:
            data = self.sock.recv(4096)
        except OSError:
            print("\n\n!!! ERROR READ -> \t\n\n", sys.exc_info()[0])
        else:
            if data:
                self._buffer += data
            else:
                raise RuntimeError("!!! Server closed connection")

    def read(self):
        self._resetParams()
        self._read()

        if self._lenJSON == 0:
            # print("\t\t-> Getting len...")
            self.getLenJSON()

        if self._lenJSON is not None and len(self.jsonHeader) == 0:
            # print("\t\t-> Getting JSON Header...")
            self.getJSONHeader()

        if self.jsonHeader and len(self.request) == 0:
            # print("\t\t-> Getting request...")
            self.getRequest()
        return self.request

    def _createMessage(self, *, content_bytes, content_type, content_encoding):
        jsonHeader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonHeaderBytes = self._encodeJSON(jsonHeader)
        messageHdr = struct.pack(">H", len(jsonHeaderBytes))
        message = messageHdr + jsonHeaderBytes + content_bytes
        return message

    def createResponse(self, data):
        response = {
            "content_bytes": self._encodeJSON(data),
            "content_type": "text/json",
            "content_encoding": "utf-8"
        }
        message = self._createMessage(**response)
        self.responseCreated = True
        self._sendBuffer += message

    def _write(self):
        if self._sendBuffer:
            try:
                sent = self.sock.send(self._sendBuffer)
            except OSError:
                pass
            else:
                self._sendBuffer = self._sendBuffer[sent:]
                if sent and not self._sendBuffer:
                    return True
        return True

    def write(self, data):
        if not self.responseCreated:
            self.createResponse(data)
        self._write()

    def changeMask(self, mode):
        if mode == EVENT_READ:
            self.mask = EVENT_READ
        elif mode == EVENT_WRITE:
            self.mask = EVENT_WRITE
        else:
            raise ValueError("Mode not valid!")


class senderListener:
    def __init__(self, conn: Connection, qRecv):
        self.conn = conn
        self.queueAPI: dict = qRecv
        self.dataIn: dict = {}
        self.dataOut: list = []

    def processEvents(self) -> bool:
        mask = self.conn.mask
        if mask == EVENT_READ:
            print("\t▣ Getting data...", end=" ")
            self.dataIn = self.conn.read()
            self.queueAPI.append(self.dataIn)
            self.conn.changeMask(EVENT_WRITE)
            print("OK!\n")
            return True
        if mask == EVENT_WRITE:
            print("\t▣ Sending data...")
            self.conn.write(self.dataOut)
            self.conn.changeMask(EVENT_READ)
            return True
        return False

    def setData(self, data):
        self.dataOut = data
