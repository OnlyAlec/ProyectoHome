"""Librerias."""
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


class Connection:
    """
    Clase para manejar la conexion con la PICO usando sockets.

    Args:
        selector (selectors.DefaultSelector): Selector de eventos.
        sock (socket.socket): Socket de conexion.
        addr (tuple): IP y puerto del servidor.

    Attributes:
        selector (selectors.DefaultSelector): Selector de eventos.
        sock (socket.socket): Socket de conexion.
        addr (tuple): IP y puerto del servidor.
        responseCreated (bool): Bandera para saber si se creo una respuesta.
        jsonHeader (dict): Diccionario con los headers del JSON.
        request (dict):  Diccionario con los datos recibidos.
        _lenJSON (int): Tamaño del JSON.
        _buffer (bytes): Buffer para almacenar los datos recibidos.
        _sendBuffer (bytes): Buffer para almacenar los datos a enviar.

    Methods:
        close:
            Cierra la conexion con la RPI.
        getLenJSON:
            Obtiene el tamaño del JSON.
        getJSONHeader:
            Obtiene los headers del JSON.
        getRequest:
            Obtiene los datos recibidos.
        _resetParams:
            Resetea los parametros de la clase.
        _encodeJSON:
            Codifica un diccionario a JSON.
        _decodeJSON:
            Decodifica un JSON a diccionario.
        _read:
            Lee los datos recibidos del socket.
        read:
            Empieza el proceso de recibir datos.
        _createMessage:
            Crea el mensaje a enviar.
        createResponse:
            Crea la respuesta a enviar.
        _write:
            Envia los datos almacenados en el buffer.
        write:
            Empieza el proceso para el envio de datos.
        changeMask:
            Cambia la mascara para el manejo de eventos.
    """

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
        """
         Cierra la conexión al PICO.

         Raise:
            OSError: Si la conexión no se puede cerrar. Esto probablemente significa que la conexión ya está cerrada.
        """

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
        """
         Obtiene la longitud de los datos JSON.
         Esto se utiliza para determinar si vamos a leer o no un archivo
        """

        hdrlen = 2
        if len(self._buffer) >= hdrlen:
            self._lenJSON = struct.unpack(
                ">H", self._buffer[:hdrlen]
            )[0]
            self._buffer = self._buffer[hdrlen:]

    def getJSONHeader(self):
        """
         Parsear y almacenar el encabezado JSON.

         Raise:
            ValueError: Si falta el encabezado requerido.
        """

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
        """
        Obtenga la solicitud del buffer y decodifique.

        Return:
            dict: Diccionario con los datos recibidos.
        """

        contLen = self.jsonHeader["content-length"]

        if not len(self._buffer) >= contLen:
            print("\tFailed -> Not Same JSON Len!")
            return
        data = self._buffer[:contLen]
        self._buffer = self._buffer[contLen:]
        self.request = self._decodeJSON(data)

    def _resetParams(self):
        """
         Resete los parámetros a valores predeterminados antes de enviar una solicitud al servidor.
        """
        self._lenJSON = 0
        self.jsonHeader = {}
        self.request = {}
        self.responseCreated = False

    def _encodeJSON(self, obj):
        """
        Codifica un diccionario en JSON.

        Args:
            obj (dict): Diccionario a codificar.

        Return:
            bytes: Diccionario codificado.
        """

        return json.dumps(obj).encode("utf-8")

    def _decodeJSON(self, bytesJSON):
        """
         Decodifica una cadena JSON en un diccionario de Python.

         Args:
            bytesJSON (bytes): Cadena JSON a decodificar.

        Return:
            dict: Diccionario decodificado.
        """

        tiow = io.TextIOWrapper(
            io.BytesIO(bytesJSON), encoding="utf-8", newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _read(self):
        """
        Lea los datos de la socket y almacena en el buffer.

        Raise:
            RuntimeError: Si el cliente cierra la conexión.
        """

        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            pass
        else:
            # Añadir datos al buffer.
            if data:
                self._buffer += data
            else:
                raise RuntimeError("!!! Client closed connection")

    def read(self):
        """
        Empieza el proceso de recibir datos.

        Return:
            dict: Diccionario con los datos recibidos.
        """

        self._resetParams()
        self._read()

        # Obtenga la longitud de la cadena JSON
        if self._lenJSON == 0:
            # print("\t\t-> Getting len...")
            self.getLenJSON()

        # Obtenga el encabezado JSON si lenJSON no es Ninguna
        if self._lenJSON is not None and len(self.jsonHeader) == 0:
            # print("\t\t-> Getting JSON Header...")
            self.getJSONHeader()

        # Obtenga la solicitud del servidor si la solicitud aún no ha sido configurada.
        if self.jsonHeader and len(self.request) == 0:
            # print("\t\t-> Getting request...")
            self.getRequest()
        return self.request

    def _createMessage(self, *, content_bytes, content_type, content_encoding):
        """
        Crear un mensaje para enviar.

        Args:
            content_bytes (bytes): Bytes a enviar.
            content_type (str): Tipo de contenido.
            content_encoding (str): Codificacion del contenido.

        Return:
            bytes: Mensaje a enviar.
        """

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
        """
        Crear una respuesta a la solicitud.

        Args:
            data (dict): Diccionario con los datos a enviar.
        """

        response = {
            "content_bytes": self._encodeJSON(data),
            "content_type": "text/json",
            "content_encoding": "utf-8"
        }
        message = self._createMessage(**response)
        self.responseCreated = True
        self._sendBuffer += message

    def _write(self):
        """
        Envia los datos almacenados en el buffer.

        Return:
            bool: Verdadero si se envio el socket al socket.
        """

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
        """
        Empieza el proceso para el envio de datos.

        Args:
            data (dict): Diccionario con los datos a enviar.

        Raise:
            RuntimeError: Si la respuesta no se ha creado.
        """
        if not self.responseCreated:
            self.createResponse(data)
        self._write()

    def changeMask(self, mode):
        """
        Cambiar la máscara de lectura / escritura.

        Args:
            mode (str): Modo de la mascara.

        Raise:
            ValueError: Si el modo no es valido.
        """

        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {mode!r}.")
        self.selector.modify(self.sock, events, data=self)


def initConnectPico() -> Connection:
    """
    Inicializa la conexion con el PICO.

    Returns:
        Connection: Objeto de la clase Connection.
    """

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


class senderListener:
    """
    Clase que procesa eventos de lectura y escritura en una conexión de red.

    Args:
        conn (Connection):  Representa la conexión a la PICO.
        qSend (queue.Queue): Cola de datos de salida.
        qRecv (queue.Queue): Cola de datos de entrada.

    Attributes:
        conn (Connection):  Representa la conexión a la PICO.
        qSend (queue.Queue): Cola de datos de salida.
        qRecv (queue.Queue): Cola de datos de entrada.
        dataIn (dict): Diccionario con los datos recibidos.
        dataOut (dict): Diccionario con los datos a enviar.
        _libSensorsState (dict): Diccionario con el estado de los sensores.

    Methods:
        processEvents:
            Procesa eventos de lectura y escritura en la conexión de red.
        checkAction:
            Verifica las acciones a realizar en base a los datos recibidos.
        processData:
            Procesa los datos recibidos y realiza las acciones correspondientes.
        checkQueue:
            Verifica la cola de datos y envía los datos correspondientes.
    """

    def __init__(self, conn: Connection, qAPISend, qAPIRecv):
        self.conn = conn
        self.qSend: queue.Queue = qAPISend
        self.qRecv: queue.Queue = qAPIRecv
        self.dataIn: dict = {}
        self.dataOut: dict = {}
        self._libSensorsState: dict = {}

    def processEvents(self, mask) -> bool:
        """
        Procesa eventos de lectura y escritura en la conexión de red.

        Args:
            mask: Máscara de eventos.

        Return:
            bool: True si se procesaron eventos, False en caso contrario.
        """

        if mask & selectors.EVENT_READ:
            print(" ▣ Obteniendo datos...")
            self.dataIn = self.conn.read()
            self.processData()
            self.dataIn = {}
            self.conn.changeMask("w")
            return True
        if mask & selectors.EVENT_WRITE:
            print(" ▣ Enviando datos...")
            self.checkQueue()
            self.conn.write(self.dataOut)
            self.dataOut = {}
            self.conn.changeMask("r")
            return True
        return False

    def checkAction(self, action: list | dict):
        """
        Verifica las acciones a realizar en base a los datos recibidos.

        Args:
            action: Acción o lista de acciones a verificar.

        Return:
            bool: True si todas las acciones son válidas, False en caso contrario.
        """

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
        """
        Procesa los datos recibidos y realiza las acciones correspondientes.
        """

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
        """
        Verifica la cola de datos y envía los datos correspondientes.
        """

        if not self.qRecv.empty():
            if isinstance(self.dataOut, dict):
                self.dataOut["API"] = self.qRecv.get()
            elif isinstance(self.dataOut, list):
                self.dataOut.append(self.qRecv.get())
            self.qRecv.task_done()


class API:
    """
    Clase para manejar la conexion con la API.

    Args:
        qAPISend (queue.Queue): Cola de datos de salida.
        qAPIRecv (queue.Queue): Cola de datos de entrada.

    Attributes:
        url (str): URL de la API.
        queueAPI (queue.Queue): Cola de datos de salida.    
        queueActions (queue.Queue): Cola de datos de entrada.
        dataIn (dict): Diccionario con los datos recibidos.
        dataOut (dict): Diccionario con los datos a enviar.

    Methods:
        listenerWorker:
            Procesa los datos recibidos de la API.
        senderWorker:
            Procesa los datos a enviar a la API.
        getStateSensor:
            Obtiene el estado de los sensores.
    """

    def __init__(self, qAPISend, qAPIRecv):
        # self.url = "https://apihomeiot.online/v1.0/dbnosql"
        self.url = "http://200.10.0.1:80/v1.0/dbnosql"
        self.queueAPI: queue.Queue = qAPISend
        self.queueActions: queue.Queue = qAPIRecv
        self.dataIn: dict = {}
        self.dataOut: dict = {}

    def listenerWorker(self, stop):
        """
        Procesa los datos recibidos de la API, se maneja por un Thread.

        Args:
            stop: Bandera para detener el proceso.

        Raise:
            Exception: Si ocurre un error al obtener los datos.
        """

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
        """	
        Procesa los datos a enviar a la API, se maneja por un Thread.

        Args:
            stop: Bandera para detener el proceso.

        Raise:
            Exception: Si ocurre un error al enviar los datos.
        """

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
        """
        Obtiene el estado de los sensores.
        """

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
