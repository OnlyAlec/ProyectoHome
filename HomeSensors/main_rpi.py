import sys
import threading
import queue
from datetime import datetime
import libConnect


# ----------------------------------
# Globales
# ----------------------------------
q = queue.Queue()
connPICO = None
connRPI = None


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
        self.timeProcess = tP.strftime("%Y-%m-%dT%H:%M:%S")

    def toServer(self):
        dictFormat = {
            "sensor": self.type,
            "data": self.dataServer,
            "timeRecived": self.timeRecived,
            "timeProcess": self.timeProcess
        }
        return dictFormat

    def toFn(self):
        jsonFormat = {
            "function": self.fn,
            "args": self.args,
        }
        return jsonFormat


# ----------------------------------
# Funciones Conectividad
# ----------------------------------
def sendData(pico: libConnect.Connection, rpi: libConnect.Connection, dataS: dataSensor):
    if dataS.fn:
        libConnect.senderWorker(pico, dataS.toFn())
    # libConnect.senderWorker(rpi, dataS.toServer())

# ----------------------------------
# Funciones por hilos
# ----------------------------------


def functionWorker(cPICO, cRPI):
    fnValid = {
        "Ultrasonico": sInfrared,
        "IR": sIR,
        "Temperatura": sTemp
    }
    while True:
        data = q.get()
        if data:
            dataS = dataSensor(data["sensorName"], data["data"], data["time"])
            fn, args, server = fnValid[dataS.type](**dataS.dataRecived)
            dataS.setFn(fn, args)
            dataS.setServer(server, datetime.now())
            sendData(cPICO, cRPI, dataS)
            q.task_done()


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
    connPICO = libConnect.initConnectPico()
    connRPI = libConnect.initConnectRPI(host="200.10.0.1", port=2050)

    gD = threading.Thread(target=libConnect.listenerWorker,
                          args=(connPICO, q), daemon=True)
    sD = threading.Thread(target=functionWorker, args=(
        connPICO, connRPI), daemon=True)
    gD.start()
    sD.start()

    while True:
        if not gD.is_alive or not sD.is_alive:
            print("Threads stopped")
            sys.exit()
