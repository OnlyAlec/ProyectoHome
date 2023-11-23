from datetime import datetime


class dataSensor:
    """
    Clase para representar los datos de los sensores

    Args:
        typeSensor (str): Tipo de sensor
        data (dict): Datos del sensor
        tR (list): Tiempo de recibo

    Attributes:
        type (str): Tipo de sensor
        dataRecived (dict): Datos del sensor
        timeRecived (str): Tiempo de recibo
        dataServer (dict): Datos para la API
        timeProcess (str): Tiempo de procesamiento
        action (list|dict): Lista de acciones a realizar

    Methods:
        setFn(listActions): Establece las acciones a realizar para mandarlas a la PICO
        setServer(data, tP): Establece los datos para la API
        toServer(): Devuelve los datos en formato JSON
    """

    def __init__(self, typeSensor: str, data: dict, tR: list):
        self.type = typeSensor
        self.dataRecived = data
        self.timeRecived = datetime(
            tR[0], tR[1], tR[2], tR[3], tR[4], tR[5]).isoformat()
        # Adicional
        self.dataServer = {}
        self.timeProcess = None
        self.action: list | dict = []

    def setFn(self, listActions: dict | list):
        """
        Establece las acciones a realizar para mandarlas a la PICO

        Args:
            listActions (dict|list): Acciones a realizar
        """

        self.action = listActions

    def setServer(self, data: dict, tP: datetime):
        """
        Establece los datos para la API

        Args:
            data (dict): Datos para la API
            tP (datetime): Tiempo de procesamiento
        """

        self.dataServer = data
        self.timeProcess = tP.strftime("%Y-%m-%dT%H:%M:%S")

    def toServer(self):
        """
        Aplica el formato de los datos para la API

        Returns:
            dict: Datos en formato JSON
        """

        if len(self.dataServer) > 1:
            dictFormat = [
                {
                    "type": "notification",
                    "title": self.dataServer['notification']["title"],
                    "message": self.dataServer['notification']["message"]
                },
                {

                    "type": "sensor",
                    "sensor": self.type,
                    "data": self.dataServer,
                    "timeRecived": self.timeRecived,
                    "timeProcess": self.timeProcess
                }
            ]
            return dictFormat
        dictFormat = {
            "type": "sensor",
            "sensor": self.type,
            "data": self.dataServer,
            "timeRecived": self.timeRecived,
            "timeProcess": self.timeProcess
        }
        return dictFormat


def sGas(**kwargs):
    """
    Funcion para el sensor de gas

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """

    # results = [kwargs["Smoke"], kwargs["LPG"],
    #            kwargs["Methane"], kwargs["Hydrogen"]]
    results = kwargs["Methane"]
    if results > 10000:
        action = {
            "function": "buzzerAction", "args": {
                "buzzer": "BUZZER_COCINA", "state": "ON"
            }
        }
        notification = {
            "type": "notification",
            "title": "¡Alerta de Gas!",
            "message": "Se ha detectado una fuga de gas en la cocina."
        }
        return action, {"gas": results, "notification": notification}
    action = {
        "function": "buzzerAction", "args": {
            "buzzer": "BUZZER_COCINA", "state": "OFF"
        }
    }
    return action, {"gas": results}


def sHumedad(**kwargs):
    """
    Funcion para el sensor de humedad

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """

    vAnalog = kwargs["valueAnalog"]
    humedad = 100 - ((vAnalog / 65535) * 100)
    print(f'\t\t◈  Humedad: {humedad}')
    if 15 > humedad > 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion sobre Jardin!",
            "message": "Es momento de regar el jardín, la humedad de la tierra esta baja."
        }
        return False, {"humedad": humedad, "notification": notification}
    return False, {"humedad": humedad}


def sRFID(**kwargs):
    """
    Funcion para el sensor de RFID

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """

    card = kwargs["card"]
    print(f'\t\t◈  RFID: {card}')
    if card == 4276175027:
        action = [
            {
                "function": "servoAction",
                "args": {"servo": "SERVO_ENTRADA", "state": "ON"}
            }
        ]
        notification = {
            "type": "notification",
            "title": "¡Notification de entrada!",
            "message": "Se ha detectado un acceso autorizado."
        }
    elif card != "null":
        action = {
            "function": "buzzerAction",
            "args": {"buzzer": "BUZZER_ENTRADA", "state": "ON"}
        }
        notification = {
            "type": "notification",
            "title": "¡Notification de entrada!",
            "message": "Se ha detectado un acceso no autorizado."
        }
        return action, {"RFID": card,  "notification": notification}
    return False, False


def sLuz(**kwargs):
    """
    Funcion para el sensor de Luz

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """

    maxDark = 65535
    minLight = 0
    vAnalog = kwargs["valueAnalog"]

    porcentaje = ((vAnalog - minLight) / (maxDark - minLight)) * 100
    porcentaje = 100 - porcentaje
    porcentaje = max(0, min(100, porcentaje))
    print(f'\t\t◈  Luz: {porcentaje}%')

    if porcentaje < 30:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "ON"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "ON"}
            }
        ]
    else:
        action = [
            {
                "function": "ledChange",
                "args": {"led": "LED_HABITACION", "state": "OFF"}
            },
            {
                "function": "ledChange",
                "args": {"led": "LED_JARDIN_LUZ", "state": "OFF"}
            }
        ]
    return action, {"luz": porcentaje}


def sIR(**kwargs):
    """
    Funcion para el sensor de proximidad

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """
    status = kwargs["status"]
    print(f'\t\t◈  IR: {status}')
    if status == "True":
        action = {
            "function": "ledChange",
            "args": {"led": "LED_ENTRADA", "state": "ON"}
        }
        notification = {
            "type": "notification",
            "title": "¡Hay alguien afuera!",
            "message": "Se ha detectado un movimiento en la entrada de la casa."
        }
        return action, {"IR": status, "notification": notification}
    action = {
        "function": "ledChange",
        "args": {"led": "LED_ENTRADA", "state": "OFF"}
    }
    return action, {"IR": status}


def sTemp(**kwargs):
    """
    Funcion para el sensor de temperatura

    Args:
        kwargs (dict): Diccionario con los datos del sensor

    Returns:
        dict: Accion a realizar
        dict: Datos para la API
    """
    vAnalog = kwargs["valueAnalog"]
    conversionFactor = 3.3 / (65535)
    v = vAnalog * conversionFactor
    temp = 27 - (v - 0.706)/0.001721
    print(f'\t\t◈  Temperatura: {temp}')
    if temp >= 30:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Lleva ropa ligera, la temperatura del dia de hoy es alta."
        }
        return False, {"temperatura": temp,  "notification": notification}
    if temp <= 20:
        notification = {
            "type": "notification",
            "title": "¡Recomedacion de Temperatura!",
            "message": "Está haciendo mucho frío, no olvides abrigarte al salir."
        }
        return False, {"temperatura": temp,  "notification": notification}
    return False, {"temperatura": temp}
