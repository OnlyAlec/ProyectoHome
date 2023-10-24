import socket
import json
import base64
import threading
import queue
import sys
from datetime import datetime
from dotenv import load_dotenv


# ----------------------------------
# Globales
# ----------------------------------
load_dotenv()
conn = socket.socket()
connRPI = socket.socket()
q = queue.Queue()


# ----------------------------------
# Clases
# ----------------------------------
class dataSensor:
    def __init__(self, typeSensor: str, data: dict, tR: list):
        self.type = typeSensor
        self.dataRecived = data
        self.timeRecived = datetime(
            tR[0], tR[1], tR[2], tR[3], tR[4], tR[5]).isoformat()
        # Adicional
        self.fn = None
        self.args = None
        self.dataServer = None
        self.timeProcess = None

    def setFn(self, fn: str, data: dict):
        self.fn = fn
        self.args = data

    def setServer(self, data: dict, tP: datetime):
        self.dataServer = data
        self.timeProcess = tP.isoformat()

    def toServerJSON(self):
        dictFormat = {
            "sensor": self.type,
            "data": self.dataServer,
            "timeRecived": self.timeRecived,
            "timeProcess": self.timeProcess
        }
        return json.dumps(dictFormat)

    def toJSON(self):
        jsonFormat = {
            "function": self.fn,
            "args": self.args,
        }
        return json.dumps(jsonFormat)
# ----------------------------------
# Funciones Conectividad
# ----------------------------------


def connect():
    print("Connecting to RPI...", end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('200.10.0.1', 2050))
        print("\tOK!")
    except OSError as e:
        print(f"\tFAILED ->\t{e}!")
    return s


def pair():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 8080))
    s.listen(1)
    print('Listening for PICO...', end=" ")

    connection, addr = s.accept()
    print(f'\tOK!:  {addr}')
    s.setblocking(False)
    return connection


def sendData(data: dataSensor):
    if data.fn is not None:
        try:
            print("\t▣ Sending function...", end=" ")
            encodeData = base64.b64encode(data.toJSON().encode('utf-8'))
            conn.send(encodeData)
            print("\tOK!")
        except OSError as e:
            print(f"\tFAILED ->\t{e}!")

    try:
        print("\t▣ Sending data to server...", end=" ")
        connRPI.send(data.toServerJSON().encode('utf-8'))
        print("\tOK!")
    except OSError as e:
        print(f"\tFAILED ->\t{e}!")


# ----------------------------------
# Funciones por hilos
# ----------------------------------
def functionWorker():
    fnValid = {
        "Ultrasonico": sInfrared,
        "IR": sIR,
        "Temperatura": sTemp
    }
    while True:
        data = q.get()
        dataS = dataSensor(data["type"], data["data"], data["time"])
        fn, args, server = fnValid[dataS.type](**dataS.dataRecived)
        dataS.setFn(fn, args)
        dataS.setServer(server, datetime.now())
        sendData(dataS)
        q.task_done()


def getDataWorker():
    encodeData = b''
    delimiter = b'\n'
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            print("Server disconnected!")
            sys.exit(0)
        encodeData += chunk
        posDelimiter = encodeData.find(delimiter)
        if posDelimiter != -1:
            encodeData = encodeData[:posDelimiter]
            print("\t▣ Getting data...", end=" ")
            try:
                data = base64.b64decode(encodeData)
                data = json.loads(data.decode('utf-8'))
                q.put(data)
                encodeData = encodeData[posDelimiter + len(delimiter):]
                print("\tOK!")
            except Exception as e:
                print(f"\tFAILED! ->\t{e}: {e.args}")


# ----------------------------------
# Proceso de datos sensores
# ----------------------------------
def sInfrared(**kwargs):
    pulse_time = kwargs["pulse"]
    cms = (pulse_time / 2) / 29.1
    # inicio = kwargs["inicio"]
    # fin = kwargs["fin"]
    # duracion = fin - inicio
    # distancia = (duracion * 0.0343) / 2
    print(f'\t\t◈  Distancia detectada: {cms}')
    if cms < 10:
        return "openDoor", {"servo": "SERVO_1", "state": "ON"}, {"distancia": cms}
    return "openDoor", {"servo": "SERVO_1", "state": "OFF"}, {"distancia": cms}


def sIR(**kwargs):
    status = kwargs["status"]
    print(f'\t\t◈  Estado IR: {status}')
    if status == "True":
        return "ledChange", {"led": "LED_1", "state": "ON"}, {"status": status}
    return "ledChange", {"led": "LED_1", "state": "OFF"}, {"status": status}


def sTemp(**kwargs):
    vAnalog = kwargs["valueAnalog"]
    v = vAnalog * 3.3 / 65535
    temp = v * 100
    print(f'\t\t◈  Temperatura: {temp}')
    return None, None, {"temperatura": temp}


# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    print("Init program...")
    conn = pair()
    connRPI = connect()

    gD = threading.Thread(target=getDataWorker, daemon=True)
    sD = threading.Thread(target=functionWorker, daemon=True)
    sD.start()
    gD.start()

    gD.join()
    sD.join()
