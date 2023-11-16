import os
import queue
import json
from datetime import datetime
from firebase_admin import db, credentials, initialize_app


class NODB:
    def __init__(self, q):
        self.connect()
        self._baseSpaces = "Mi_Casa_Inteligente/Espacios/"
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
            return "LED", "ledChange"
        if disp == "ALARMA_DE_HUMO":
            return "BUZZER", "buzzerAction"
        if disp == "SERVOMOTOR":
            return "SERVO", "servoAction"
        return ValueError("Null value!"), ValueError("Null value!")

    def onChange(self, event: db.Event):
        if event.path == "/":
            return
        if space := event.path.split("/")[1] not in self._spaces:
            return
        refSpace = dict(db.reference(
            self._baseSpaces + event.path.rsplit('/', 1)[0]).get())
        disp, fn = self.parseDisp(refSpace["dispositivos"])

        jsonAction = {
            "function": fn,
            "args": {disp: f"{disp}_{space}", "state": event.data}
        }
        self.queueActions.put(jsonAction)


class Firebase:
    def __init__(self, data):
        self.version = 1
        self.dataJson = data
        self.space = ""
        self.sensor = ""
        self.info = ""
        # Adicional
        self.timeRecived = ""
        self.timeProcess = ""

    def parseJSON(self):
        for key, value in self.dataJson:
            if key == "sensor":
                self.sensor = value
            if key == "data":
                self.info = value
            if key == "timeRecived":
                self.timeRecived = value
            if key == "timeProcess":
                self.timeProcess = value

    def generateDates(self):
        base = datetime.now()
        actual = base.strftime("%Y_%m_%d")
        timeSensor = base.strftime("%Y_%m_%d_%H_%M_%S")
        start = (base.replace(hour=0, minute=0, second=0,
                 microsecond=0)).strftime("%Y_%m_%d_%H_%M_%S")
        end = (base.replace(hour=23, minute=59, second=59,
               microsecond=999999)).strftime("%Y_%m_%d_%H_%M_%S")
        return [actual, timeSensor, start, end]

    def createAlert(self):
        #
        pass

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
            'valor': self.info
        }
        ref.push(json.dumps(reg))

    def insertLastReg(self):
        sensorName = self.sensor.lower()
        ultRef = db.reference(
            f'Mi_Casa_Inteligente/Ultima_sensores/Ultima_{sensorName}')
        ultRef.update({
            'version': self.version,
            'timestamp': self.generateDates()[1],
            'valor': self.info
        })
