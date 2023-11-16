import os
import queue
import time
from functools import wraps
from datetime import datetime
from firebase_admin import db, credentials, initialize_app


def cooldown(tiempo):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(tiempo)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class NODB:
    def __init__(self, q):
        self.connect()
        self._baseSpaces = "Mi_Casa_Inteligente/Espacios"
        self._spaces = self.getSpacesName()
        self.queueActions: queue.Queue = q

    def connect(self):
        cred = credentials.Certificate('./Auth/firebase.json')
        initialize_app(cred, {'databaseURL': os.getenv('URL_FIREBASE')})

    def getSpacesName(self):
        ref = db.reference('Mi_Casa_Inteligente/Nombre_espacios')
        return list(ref.get())

    def setupListeners(self):
        print("Init Listener for Espacios")
        ref = db.reference('Mi_Casa_Inteligente/Espacios/')
        ref.listen(self.onChange)

    def parseDisp(self, disp: str):
        disp = disp.upper()
        if disp == "FOCO":
            return "led", "ledChange"
        if disp == "ALARMA":
            return "buzzer", "buzzerAction"
        if disp == "SERVOMOTOR":
            return "servo", "servoAction"
        return ValueError("Null value!"), ValueError("Null value!")

    def onChange(self, event: db.Event):
        if event.path == "/":
            return
        if event.path.find("Ultimo_modificado") != -1:
            return
        if (space := event.path.split("/")[1]) not in self._spaces:
            return
        refSpace = dict(db.reference(
            self._baseSpaces + event.path).get())
        disp, fn = self.parseDisp(refSpace["dispositivo"])
        state = event.data['estado']
        jsonAction = {
            "function": fn,
            "args": {disp: f"{disp.upper()}_{space.upper()}", "state": "ON" if state else "OFF"}
        }
        self.queueActions.put(jsonAction)


class Firebase:
    def __init__(self, data):
        self.version = 1
        self.type = ""
        self.dataJson = data
        self.sensor = ""
        self.info: dict = {}
        # Adicional
        self.timeRecived = ""
        self.timeProcess = ""
        self.title = ""
        self.message = ""

    def parseJSON(self):
        for key, value in self.dataJson.items():
            if key == "sensor":
                self.sensor = value
            elif key == "data":
                self.info = value
            elif key == "timeRecived":
                self.timeRecived = value
            elif key == "timeProcess":
                self.timeProcess = value
            elif key == "type":
                self.type = value
            elif key == "title":
                self.title = value
            elif key == "message":
                self.message = value

    def generateDates(self):
        base = datetime.now()
        actual = base.strftime("%Y_%m_%d")
        timeSensor = base.strftime("%Y_%m_%d_%H_%M_%S")
        start = (base.replace(hour=0, minute=0, second=0,
                 microsecond=0)).strftime("%Y_%m_%d_%H_%M_%S")
        end = (base.replace(hour=23, minute=59, second=59,
               microsecond=999999)).strftime("%Y_%m_%d_%H_%M_%S")
        return [actual, timeSensor, start, end]

    @cooldown(5)
    def insertNotification(self):
        ref = db.reference(
            f"Mi_Casa_Inteligente/Notificaciones/{self.generateDates()[1]}")
        ref.update({
            'message': self.message,
            'timestamp': self.generateDates()[1],
            'tipo': self.title,
            'version': self.version
        })

    @cooldown(5)
    def insertBucket(self):
        sensorName = self.sensor.lower()
        ref = db.reference(
            f'Mi_Casa_Inteligente/Registros_sensores/Registros_{sensorName}/{self.generateDates()[0]}')
        ref.update({
            'version': self.version,
            'hora_inicio': self.generateDates()[2],
            'hora_final': self.generateDates()[3]
        })

    def insertReg(self):
        sensorName = self.sensor.lower()
        ref = db.reference(
            f'Mi_Casa_Inteligente/Registros_sensores/Registros_{sensorName}/{self.generateDates()[0]}/registros')
        reg = {
            'version': self.version,
            'timestamp': self.generateDates()[1],
            'valor': self.info[sensorName]
        }
        ref.push(reg)

    def insertLastReg(self):
        sensorName = self.sensor.lower()
        ultRef = db.reference(
            f'Mi_Casa_Inteligente/Ultima_sensores/Ultima_{sensorName}')
        ultRef.update({
            'version': self.version,
            'timestamp': self.generateDates()[1],
            'valor': self.info[sensorName]
        })
