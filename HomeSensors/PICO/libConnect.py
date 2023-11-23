"""Librerias."""
import socket
import json
import sys
import struct
from micropython import const

# ^Constantes para el manejo de eventos.
EVENT_READ = const(0)
EVENT_WRITE = const(1)


class Connection:
    """
    Clase para manejar la conexion con la RPI usando sockets.

    Args:
        sock (socket.socket): Socket para la conexion.
        addr (tuple): IP y puerto del servidor.

    Attributes:
        sock (socket.socket): Socket para la conexion.
        addr (tuple): IP y puerto de la RPI.
        responseCreated (bool): Bandera para saber si se creo una respuesta.
        jsonHeader (dict): Diccionario con los headers del JSON.
        request (dict): Diccionario con los datos recibidos.
        mask (int): Mascara para el manejo de eventos.
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

    def __init__(self, sock, addr):
        self.sock: socket.socket = sock
        self.addr = addr
        self.responseCreated = False
        self.jsonHeader: dict = {}
        self.request: dict = {}
        self.mask = EVENT_READ
        self._lenJSON: int = 0
        self._buffer = b""
        self._sendBuffer = b""

    def close(self):
        """ 
        Funcion para cerrar la conexion con la RPI de manera adecuada.

        Raises:
            OSError: Error al cerrar el socket.
        """

        print(f"Closing connection to {self.addr}")
        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")
        finally:
            self.sock = socket.socket()

    def getLenJSON(self):
        """
        Funcion para obtener el tamaño del JSON.
        """

        hdrlen = 2
        if len(self._buffer) >= hdrlen:
            self._lenJSON = struct.unpack(
                ">H", self._buffer[:hdrlen]
            )[0]
            self._buffer = self._buffer[hdrlen:]

    def getJSONHeader(self):
        """
        Funcion para obtener los headers del JSON.

        Raises:
            ValueError: Error al no encontrar un header requerido.
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
        Funcion para obtener los datos recibidos usando el buffer de entrada.
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
        Funcion para resetear los parametros de la clase.
        """
        self._lenJSON = 0
        self.jsonHeader = {}
        self.request = {}
        self.responseCreated = False

    def _encodeJSON(self, obj) -> bytes:
        """
        Funcion para codificar un diccionario a JSON.

        Args:
            obj (dict): Diccionario a codificar.

        Returns:
            bytes: JSON codificado.
        """

        return json.dumps(obj).encode("utf-8")

    def _decodeJSON(self, bytesJSON) -> dict:
        """	
        Funcion para decodificar un JSON a diccionario.

        Args:
            bytesJSON (bytes): JSON a decodificar.

        Returns:
            dict: Diccionario decodificado.

        Raises:
            Exception: Error al decodificar el JSON.
        """

        try:
            return json.loads(bytesJSON)
        except Exception:
            print("\n\n!!! ERROR DECODE -> \t\n\n", sys.exc_info()[0])
            print(f"\t\t-> {bytesJSON}")
            return {}

    def _read(self):
        """
        Funcion para leer los datos recibidos del socket.

        Raises:
            RuntimeError: Error al cerrar la conexion.
        """

        try:
            data = self.sock.recv(4096)
        except OSError:
            print("\n\n!!! ERROR READ -> \t\n\n", sys.exc_info()[0])
        else:
            if data:
                self._buffer += data
            else:
                raise RuntimeError("!!! Server closed connection")

    def read(self):
        """
        Funcion para empezar el proceso de recibir datos.

        Returns:
            dict: Diccionario con los datos recibidos.
        """

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
        """
        Funcion para crear el mensaje a enviar.

        Args:
            content_bytes (bytes): Bytes a enviar.
            content_type (str): Tipo de contenido.
            content_encoding (str): Codificacion del contenido.

        Returns:
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
        Funcion para crear la respuesta a enviar.

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
        Funcion para enviar los datos almacenados en el buffer.

        Returns:
            bool: True si se enviaron todos los datos, False en caso contrario.
        """

        if self._sendBuffer:
            try:
                sent = self.sock.send(self._sendBuffer)
            except OSError:
                pass
            else:
                self._sendBuffer = self._sendBuffer[sent:]
                if sent and not self._sendBuffer:
                    return True
        return True

    def write(self, data):
        """
        Funcion para empezar el proceso de envio de datos.

        Args:
            data (dict): Diccionario con los datos a enviar.
        """
        self._resetParams()
        if not self.responseCreated:
            self.createResponse(data)
        self._write()

    def changeMask(self, mode):
        """	
        Funcion para cambiar la mascara para el manejo de eventos.

        Args:
            mode (int): Modo de la mascara.

        Raises:
            ValueError: Error al no encontrar un modo valido.
        """

        if mode == EVENT_READ:
            self.mask = EVENT_READ
        elif mode == EVENT_WRITE:
            self.mask = EVENT_WRITE
        else:
            raise ValueError("Mode not valid!")


def initConnectRPI(host, port) -> Connection:
    """
    Funcion que inicializa el socket y se conecta a la RPI para enviar y recibir datos.

    Args:
        host (str): IP del servidor.
        port (int): Puerto del servidor.

    Returns:
        Connection: Objeto de la clase Connection.
    """
    print("Connecting to RPI...", end=" ")
    addr = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(addr)
        print(f'\tOK!:  {addr}')
    except OSError as e:
        print(f'\n\tFailed!: {e}')
        sys.exit()

    m = Connection(s, addr)
    return m


class senderListener:
    """
    Clase para manejar el envio y recepcion de datos.

    Args:
        conn (Connection): Representa la conexion con la RPI.
        qRecv (Queue): Cola para manejar las acciones recibidas.

    Attributes:
        conn (Connection): Objeto de la clase Connection.
        queueAPI (list): Cola para recibir datos.
        dataIn (dict): Diccionario con los datos recibidos.
        dataOut (list): Lista con los datos a enviar.

    Methods:
        processEvents:
            Procesa los eventos de la conexion usando la mascara de la conexion.
        setData:
            Establece los datos a enviar.
        wipe:
            Resetea los datos de la clase.
    """

    def __init__(self, conn: Connection, qRecv):
        self.conn = conn
        self.queueAPI: list = qRecv
        self.dataIn: dict = {}
        self.dataOut: list = []

    def processEvents(self) -> bool:
        """
        Funcion para procesar los eventos de la conexion usando la mascara de la conexion.
        Si la mascara es EVENT_READ, se reciben los datos.
        Si la mascara es EVENT_WRITE, se envian los datos.

        Returns:
            bool: True si se procesaron los eventos, False en caso contrario.
        """
        mask = self.conn.mask
        if mask == EVENT_READ:
            print("\t▣ Getting data...", end=" ")
            self.dataIn = self.conn.read()
            self.queueAPI.append(self.dataIn)
            self.conn.changeMask(EVENT_WRITE)
            print("OK!\n")
            return True
        if mask == EVENT_WRITE:
            print("\t▣ Sending data...")
            self.conn.write(self.dataOut)
            self.conn.changeMask(EVENT_READ)
            return True
        return False

    def setData(self, data):
        """
        Funcion para establecer los datos a enviar.

        Args:
            data (dict): Diccionario con los datos a enviar.
        """

        self.dataOut = data

    def wipe(self):
        """
        Funcion para resetear los datos de la clase.
        """
        self.dataIn = {}
        self.dataOut = []
