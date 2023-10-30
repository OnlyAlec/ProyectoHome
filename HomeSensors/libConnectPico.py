import socket
import json
import sys
import struct
import uselect as selectors
from main_pico import actions

sel = selectors.poll()
pending_messages = []


class Connection:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock: socket.socket = sock
        self.addr = addr
        self.jsonHeader: dict = {}
        self.request: dict = {}
        self._buffer = b""
        self._lenJSON: int = 0

    def _read(self):
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            pass
        else:
            if data:
                self._buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def write(self):
        while pending_messages:
            print("\t▣ Sending data...", end=" ")
            message = pending_messages.pop()
            try:
                self.sock.send(message)
            except BlockingIOError:
                pending_messages.insert(0, message)
                break

    def read(self):
        print("\t▣ Getting data...", end=" ")

        self._read()

        if self._lenJSON is None:
            self.getLenJSON()

        if self._lenJSON is not None and self.jsonHeader is None:
            self.getJSONHeader()

        if self.jsonHeader and self.request is None:
            return self.getRequest()
        return {}

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
        return json.loads(bytesJSON).encode("utf-8")

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

    def getRequest(self):
        contLen = self.jsonHeader["content-length"]

        if not len(self._buffer) >= contLen:
            print("\tFailed -> Not Same Len!")
            return
        data = self._buffer[:contLen]
        self._buffer = self._buffer[contLen:]
        self.request: dict = self._decodeJSON(data)
        print("\tOK!")
        return self.request

    def close(self):
        print(f"Closing connection to {self.addr}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for {
                    self.addr}: {e!r}"
            )

        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")


def initConnectPico():
    print('Listening for PICO...', end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 8080))
    s.listen()

    conn, addr = s.accept()
    print(f'\tOK!:  {addr}')

    conn.setblocking(False)
    m = Connection(sel, conn, addr)
    sel.register(m, selectors.POLLIN)
    return m


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

    m = Connection(sel, s, addr)
    sel.register(m, selectors.POLLOUT)
    return m


def listenerWorker():
    while True:
        events = sel.ipoll()
        for key, mask in events:
            message: Connection = key.data
            try:
                data: dict = message.read()
                print(f"\t▣ Action: {data['function']} -> {data['args']}")
                actions(data["function"], data["args"])
            except Exception as e:
                print(f"!!! ERROR EXCEPTION -> {message.addr}: \n {e}")
                message.close()


def senderWorker(conn: Connection, sensorData):
    request = {"content": sensorData}
    conn.queue_request(request)
    events = sel.ipoll()
    print(events, end="\n\n")
    for key, mask in events:
        print(key)
        print(mask)
        conn = key.data
        try:
            conn.write()
        except Exception as e:
            print(f"!!! ERROR EXCEPTION -> {conn.addr}: \n {e}")
            conn.close()
            return False
