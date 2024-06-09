import socket
import sys


def initConnectRPI(host, port):
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

    # m = Connection(s, addr)
    # return m


initConnectRPI("192.168.4.1", 80)
