import socket
import json
import base64

conn = None


def pair():
    host = '0.0.0.0'  # Escucha en todas las interfaces de red
    port = 45871
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print(f'Listening... {host}: {port}')

    connection, addr = s.accept()
    print(f'Connection OK!:  {addr}')
    return connection


def getData():
    while True:
        encodeData = conn.recv(1024)
        data = base64.b64decode(encodeData)
        if data:
            print(f'Data: {encodeData}')
            return json.loads(data.decode('utf-8'))


def sInfrared(dataSensor):
    inicio, fin = dataSensor
    duracion = fin - inicio
    distancia = (duracion * 0.0343) / 2
    print(f'Distancia detectada: {distancia}m')


if __name__ == '__main__':
    conn = pair()
    while True:
        info = getData()
        sInfrared(info)
