"""Librerias."""
import os
import queue
import time
from functools import wraps
from datetime import datetime
from firebase_admin import db, credentials, initialize_app


def cooldown(tiempo):
    """
    Funcion para mantener en espera una función usando `sleep()`.
    Se usa decoradores para mantener en espera la función y se use de forma universal.

    Args:
      `tiempo`: Tiempo en segundos que se mantendra en espera la función.

    Returns:
        `Funcion Decorada.`
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(tiempo)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ConnectionFirebase:
    """
    Clase para establecer una conexión con la base de datos de Firebase y realizar acciones en función de los cambios en la aplicación.

    Args:
        q (queue.Queue): Cola donde se guardan las acciones a realizar.

    Attributes:
        spaces (list): Lista de espacios de la casa obtenida por Firebase.
        baseSpaces (str): URL base de Firebase para casa predeterminada.
        queueActions (queue.Queue): Cola donde se guardan las acciones a realizar.

    Methods:
        connect():
            Inicia la conexión con Firebase y obtiene los espacios de la casa.
        getSpacesName():
            Obtiene los espacios de la casa.
        setupListeners():
            Inicializa los listeners de los cambios en Firebase.
        parseDisp(disp: str) -> Tuple[str, str]:
            Parsea el dispositivo para obtener el nombre del dispositivo y la función a realizar.
        onChange(event: db.Event):
            Función que se ejecuta cuando hay un cambio en la aplicación.
    """

    def __init__(self, q):
        """
        Constructor de la clase que inicializa los atributos `spaces`, `baseSpaces` y `queueActions`, y llama a los métodos `connect()` y `setupListeners()`.

        Args:
            q (queue.Queue): Cola donde se guardan las acciones a realizar.
        """
        self.spaces: list = []
        self.connect()
        self.baseSpaces = "Mi_Casa_Inteligente/Espacios"
        self.queueActions: queue.Queue = q
        self.setupListeners()

    def connect(self):
        """
        Inicia la conexión con Firebase y obtiene los espacios de la casa.
        """
        cred = credentials.Certificate('./Auth/firebase.json')
        initialize_app(cred, {'databaseURL': os.getenv('URL_FIREBASE')})
        self.spaces = self.getSpacesName()

    def getSpacesName(self):
        """
        Obtiene los espacios de la casa.

        Returns:
            list: Lista de espacios de la casa obtenida por Firebase.
        """
        ref = db.reference('Mi_Casa_Inteligente/Nombre_espacios')
        return list(ref.get())

    def setupListeners(self):
        """
        Inicializa los listeners de los cambios en Firebase.
        """
        print("Init Listener for Espacios")
        ref = db.reference('Mi_Casa_Inteligente/Espacios/')
        ref.listen(self.onChange)

    def parseDisp(self, disp: str) -> tuple[str, str]:
        """
        Parsea el dispositivo para obtener el nombre del dispositivo y la función a realizar.

        Args:
            disp (str): Nombre del dispositivo.

        Returns:
            Tuple[str, str]: Nombre del dispositivo y la función a realizar.
        """
        disp = disp.upper()
        if disp == "FOCO":
            return "led", "ledChange"
        if disp == "ALARMA":
            return "buzzer", "buzzerAction"
        if disp == "SERVOMOTOR":
            return "servo", "servoAction"
        return "null", "null"

    def onChange(self, event: db.Event):
        """
        Función que se ejecuta cuando hay un cambio en la aplicación.
        Parsea el evento y lo agrega a la cola de acciones.

        Args:
            event (db.Event): Evento que se ejecuta cuando hay un cambio en Firebase.
        """
        if event.path == "/":
            return
        if event.path.find("Ultimo_modificado") != -1:
            return
        if (space := event.path.split("/")[1]) not in self.spaces:
            return
        refSpace = dict(db.reference(self.baseSpaces + event.path).get())
        disp, fn = self.parseDisp(refSpace["dispositivo"])
        state = event.data['estado']
        jsonAction = {
            "function": fn,
            "args": {disp: f"{disp.upper()}_{space.upper()}", "state": "ON" if state else "OFF"}
        }
        self.queueActions.put(jsonAction)


class Firebase:
    """ 
    Clase para insertar / actualizar datos en Firebase.

        Args:
            `data`: Datos obtenidos por PICO.

        Attributes:
            `version`: Versión del JSON.
            `type`: Tipo de informacion a insertar.
            `dataJson`: Datos obtenidos por PICO.
            `sensor`: Nombre del sensor.
            `info`: Información del sensor.
            `timeRecived`: Tiempo de cuando se recibio la información.
            `timeProcess`: Tiempo de cuando se proceso la información.
            `title`: Titulo de la notificación.
            `message`: Mensaje de la notificación.

        Methods:
            `parseJSON`:
                Parsear los datos obtenidos por PICO.
            `generateDates`:
                Generar las fechas para los JSON.
            `insertNotification`:
                Insertar notificación en Firebase.
            `insertBucket`:
                Insertar bucket en Firebase.
            `insertReg`:
                Insertar registro en Firebase.
            `insertLastReg`:
                Insertar ultimo registro del sensor en Firebase.
        """

    def __init__(self, data):
        """
        Inicializa una instancia de la clase Firebase.

        Args:
            data (dict): Los datos recibidos en formato JSON.

        Attributes:
            version (int): La versión de la clase.
            type (str): El tipo de los datos recibidos.
            dataJson (dict): Los datos recibidos en formato JSON.
            sensor (str): El nombre del sensor.
            info (dict): La información del sensor.
            timeRecived (str): La fecha y hora de recepción de los datos.
            timeProcess (str): La fecha y hora de procesamiento de los datos.
            title (str): El título de la notificación.
            message (str): El mensaje de la notificación.
        """
        self.version = 1
        self.type = ""
        self.dataJson = data
        self.sensor = ""
        self.info: dict = {}
        self.timeRecived = ""
        self.timeProcess = ""
        self.title = ""
        self.message = ""

    def parseJSON(self):
        """
        Parsea los datos obtenidos por PICO y los asigna a los atributos correspondientes de la clase.
        """
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

    def generateDates(self) -> list[str]:
        """
        Genera las fechas necesarias para los JSON.

        Returns:
            List[str]: Lista con las fechas generadas.
        """
        base = datetime.now()
        actual = base.strftime("%Y_%m_%d")
        timeSensor = base.strftime("%Y_%m_%d_%H_%M_%S")
        start = (base.replace(hour=0, minute=0, second=0,
                              microsecond=0)).strftime("%Y_%m_%d_%H_%M_%S")
        end = (base.replace(hour=23, minute=59, second=59,
                            microsecond=999999)).strftime("%Y_%m_%d_%H_%M_%S")
        return [actual, timeSensor, start, end]

    @cooldown(1)
    def insertNotification(self):
        """
        Inserta una notificación en Firebase con la información de la clase.
        """
        ref = db.reference(
            f"Mi_Casa_Inteligente/Notificaciones/{self.generateDates()[1]}")
        ref.update({
            'message': self.message,
            'timestamp': self.generateDates()[1],
            'tipo': self.title,
            'version': self.version
        })

    @cooldown(1)
    def insertBucket(self):
        """
        Inserta un bucket en Firebase con la información de la clase.
        """
        sensorName = self.sensor.lower()
        ref = db.reference(
            f'Mi_Casa_Inteligente/Registros_sensores/Registros_{sensorName}/{self.generateDates()[0]}')
        ref.update({
            'version': self.version,
            'hora_inicio': self.generateDates()[2],
            'hora_final': self.generateDates()[3]
        })

    def insertReg(self):
        """
        Inserta un registro de sensor en Firebase con la información de la clase.
        """
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
        """
        Actualiza el último registro de un sensor en Firebase con la información de la clase.
        """
        sensorName = self.sensor.lower()
        ultRef = db.reference(
            f'Mi_Casa_Inteligente/Ultima_sensores/Ultima_{sensorName}')
        ultRef.update({
            'version': self.version,
            'timestamp': self.generateDates()[1],
            'valor': self.info[sensorName]
        })
