import socket
import selectors
import json
import queue
import sys
import io
import struct
from datetime import datetime
from time import sleep
import traceback
import requests

import libSensors as sensors


def initConnectPico():
    print('Listening for PICO...', end=" ")
    sel = selectors.DefaultSelector()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ?Para evitar error de puerto en uso
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 8080))
    s.listen()

    sel.register(s, selectors.EVENT_READ)
    conn, addr = s.accept()
    print(f'\tOK!:  {addr}')

    conn.setblocking(True)
    m = Connection(sel, conn, addr)
    sel.register(conn, selectors.EVENT_WRITE, data=m)
    return m


class Connection:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock: socket.socket = sock
        self.addr = addr
        self.responseCreated = False
        self.jsonHeader: dict = {}
        self.request: dict = {}
        self._lenJSON: int = 0
        self._buffer = b""
        self._sendBuffer = b""

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
        tiow = io.TextIOWrapper(
            io.BytesIO(bytesJSON), encoding="utf-8", newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _read(self):
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            pass
        else:
            if data:
                self._buffer += data
            else:
                raise RuntimeError("!!! Client closed connection")

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
            except BlockingIOError:
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
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {mode!r}.")
        self.selector.modify(self.sock, events, data=self)


class senderListener:
    def __init__(self, conn: Connection, qAPISend, qAPIRecv):
        self.conn = conn
        self.qSend: queue.Queue = qAPISend
        self.qRecv: queue.Queue = qAPIRecv
        self.dataIn: dict = {}
        self.dataOut: dict = {}
        self._libSensorsState: dict = {}

    def processEvents(self, mask) -> bool:
        if mask & selectors.EVENT_READ:
            print(" ▣ Getting data...")
            self.dataIn = self.conn.read()
            self.processData()
            self.dataIn = {}
            self.conn.changeMask("w")
            return True
        if mask & selectors.EVENT_WRITE:
            print(" ▣ Sending data...")
            self.checkQueue()
            self.conn.write(self.dataOut)
            self.dataOut = {}
            self.conn.changeMask("r")
            return True
        return False

    def checkAction(self, action: list | dict):
        doAction = []
        if isinstance(action, dict):
            action = [action]

        for a in action:
            if "function" not in a.keys():
                continue
            a = a["args"].copy()
            state = a.popitem()[1]
            sensor = a.popitem()[1]

            if sensor in self._libSensorsState.keys():
                s = self._libSensorsState[sensor]
                if s == state:
                    doAction.append(False)
                else:
                    doAction.append(True)
            self._libSensorsState[sensor] = state
            doAction.append(True)

        return all(doAction)

    def processData(self):
        fnValid = {
            "Gas": sensors.sGas,
            "Humedad": sensors.sHumedad,
            "RFUD": sensors.sRFID,
            "Luz": sensors.sLuz,
            "IR": sensors.sIR,
            "Temperatura": sensors.sTemp,
            "RFID": sensors.sRFID
        }

        for d in self.dataIn:
            dataS = sensors.dataSensor(d["sensorName"], d["data"], d["time"])
            fn, server = fnValid[dataS.type](**dataS.dataRecived)
            if fn is not False and self.checkAction(fn):
                dataS.setFn(fn)
                self.dataOut[dataS.type] = dataS.action
            if server is not False:
                dataS.setServer(server, datetime.now())
                self.qSend.put(dataS.toServer())

    def checkQueue(self):
        if not self.qRecv.empty():
            if isinstance(self.dataOut, dict):
                self.dataOut["API"] = self.qRecv.get()
            elif isinstance(self.dataOut, list):
                self.dataOut.append(self.qRecv.get())
            self.qRecv.task_done()


class API:
    def __init__(self, qAPISend, qAPIRecv):
        # self.url = "https://apihomeiot.online/v1.0/dbnosql"
        self.url = "http://200.10.0.1:80/v1.0/dbnosql"
        self.queueAPI: queue.Queue = qAPISend
        self.queueActions: queue.Queue = qAPIRecv
        self.dataIn: dict = {}
        self.dataOut: dict = {}

    def listenerWorker(self, stop):
        while not stop.is_set():
            try:
                r = requests.get(self.url)
                if r.status_code != 200:
                    sleep(1)
                    continue
                print("\n\t* READY TO DO...")
                data = r.json()
                if data is not None:
                    self.queueActions.put(data)
                sleep(1)
            except Exception:
                print(f"!!! ERROR API LISTENER -> \t"
                      f"{traceback.format_exc()}")
                stop.set()
                break

    def senderWorker(self, stop):
        while not stop.is_set():
            if self.queueAPI.empty():
                continue
            try:
                dataJson = self.queueAPI.get()
                dataJson = json.dumps(dataJson)
                headers = {'Content-Type': 'application/json'}
                requests.post(self.url, headers=headers,
                              data=dataJson)
                self.queueAPI.task_done()
            except Exception:
                print(f"!!! ERROR API SENDER -> \t"
                      f"{traceback.format_exc()}")
                stop.set()
                break

    def getStateSensor(self):
        r = requests.get(self.url+"/getState", timeout=120)
        if r.status_code != 200:
            print("------------------------------")
            print("  * API No Availabe, devices as default...")
            print("------------------------------")
            return
        print("--------------------------------")
        print("  * Getting states of devices...")
        print("--------------------------------")
        data = r.json()
        self.queueActions.put(data)
