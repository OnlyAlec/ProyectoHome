import socket
import selectors
import json
import sys
import struct
import io
import traceback
import queue

q = queue.Queue()
sel = selectors.DefaultSelector()
pending_messages = []


class Connection:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock: socket.socket = sock
        self.addr = addr
        self.jsonHeader: dict = {}
        self.request = None
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
        tiow = io.TextIOWrapper(
            io.BytesIO(bytesJSON), encoding="utf-8", newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

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
        self.request = self._decodeJSON(data)
        q.put(self.request)
        print("\tOK!")

    def close(self):
        print(f"Closing connection to {self.addr}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.addr}: {e!r}"
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
    sel.register(conn, selectors.EVENT_READ, data=m)
    return m


def initConnectRPI(host, port):
    print("Connecting to RPI...", end=" ")
    addr = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect_ex(addr)
        print(f'\tOK!:  {addr}')
    except OSError as e:
        print(f'\tFailed!: {e}')
        sys.exit()

    m = Connection(sel, s, addr)
    sel.register(s, selectors.EVENT_WRITE, data=m)
    return m


def listenerWorker(qRecv):
    global q
    q = qRecv

    try:
        while True:
            events = sel.select(timeout=0)
            for key, mask in events:
                message: Connection = key.data
                try:
                    message.read()
                except Exception:
                    print(
                        f"!!! ERROR EXCEPTION -> {message.addr}: \n"
                        f"{traceback.format_exc()}"
                    )
                    message.close()
    finally:
        sel.close()


def senderWorker(conn: Connection, sensorData):
    request = {"content": sensorData}
    conn.queue_request(request)
    events = sel.select(timeout=1)

    for key, mask in events:
        conn = key.data
        try:
            conn.write()
        except Exception:
            print(
                f"!!! ERROR EXCEPTION -> {conn.addr}: \n"
                f"{traceback.format_exc()}"
            )
            conn.close()
            return False
    if not sel.get_map():
        return False
