import socket
import json
import base64
import threading
import queue
import sys

# ----------------------------------
# Globales
# ----------------------------------
conn = socket.socket()
q = queue.Queue()


# ----------------------------------
# Clases
# ----------------------------------
class dataBack:
    def __init__(self, fn: str, data: dict = {}):
        self.function = fn
        self.args = data

    def toJSON(self):
        jsonFormat = {
            "function": self.function,
            "args": self.args,
        }
        return json.dumps(jsonFormat)


# ----------------------------------
# Funciones Conectividad
# ----------------------------------
def pair():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 8080))
    s.listen(1)
    print(f'Listening all network...')

    connection, addr = s.accept()
    print(f'Connection OK!:  {addr}')
    s.setblocking(False)
    return connection


def sendData(dataSend):
    try:
        print("\t▣ Sending data...")
        encodeData = base64.b64encode(dataSend.encode('utf-8'))
        conn.send(encodeData)
        print("\t▣ Data Send!")
    except OSError as e:
        print(f"\t▣ Data Failed Send! ->\t{e}")
        return None


# ----------------------------------
# Funciones por hilos
# ----------------------------------
def functionWorker():
    while True:
        data = q.get()
        print(f"\t▣ Redirecting {data}")
        redirectFunctions(data["type"], data["data"])
        q.task_done()


def getDataWorker():
    encodeData = b''
    delimiter = b'\n'
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            print("No more info!")
            sys.exit(0)
        encodeData += chunk
        posDelimiter = encodeData.find(delimiter)
        if posDelimiter != -1:
            encodeData = encodeData[:posDelimiter]
            print("\t▣ Getting data...")
            data = base64.b64decode(encodeData)

            print(f'\tData: {encodeData}')
            data = json.loads(data.decode('utf-8'))
            q.put(data)
            encodeData = encodeData[posDelimiter + len(delimiter):]


def redirectFunctions(strSensor: str, kwargs: dict = {}):
    functionsValid = {
        "Ultrasonico": sInfrared
    }
    returnData = functionsValid[strSensor](**kwargs)
    print(f"\t▣ Return data: {returnData}")
    if returnData:
        sendData(returnData)


# ----------------------------------
# Proceso de datos sensores
# ----------------------------------
def sInfrared(**kwargs):
    inicio = kwargs["inicio"]
    fin = kwargs["fin"]
    duracion = fin - inicio
    distancia = (duracion * 0.0343) / 2
    print(f'\t\t◈ Distancia detectada: {distancia}')

    if distancia < 10:
        return dataBack("openDoor", {"servo": "SERVO_1", "state": "ON"}).toJSON()
    return dataBack("openDoor", {"servo": "SERVO_1", "state": "OFF"}).toJSON()


# ----------------------------------
# Main
# ----------------------------------
if __name__ == '__main__':
    print("Init program...")
    conn = pair()

    gD = threading.Thread(target=getDataWorker, daemon=True)
    sD = threading.Thread(target=functionWorker, daemon=True)
    sD.start()
    gD.start()

    gD.join()
    sD.join()
