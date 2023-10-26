import selectors
import json
import io
import struct
import socket
import queue

sel = selectors.DefaultSelector()
q = queue.Queue()


class Message:
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

    def _decodeJSON(self, bytesJSON):
        tiow = io.TextIOWrapper(
            io.BytesIO(bytesJSON), encoding="utf-8", newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def read(self):
        print("\t▣ Getting data...", end=" ")

        self._read()

        if self._lenJSON is None:
            self.getLenJSON()

        if self._lenJSON is not None and self.jsonHeader is None:
            self.getJSONHeader()

        if self.jsonHeader and self.request is None:
            self.getRequest()

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


def initConectivity():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 8080))
    s.listen()
    print('Listening for PICO...', end=" ")

    conn, addr = s.accept()
    print(f'\tOK!:  {addr}')

    conn.setblocking(False)
    m = Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=m)
    return conn


def listenerWorker(qRecv: queue.Queue):
    global q
    q = qRecv

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                message: Message = key.data
                try:
                    message.read()
                except Exception:
                    print(f"!!! ERROR EXCEPTION -> {message.addr}: \n")
                    message.close()
    finally:
        sel.close()
