import socket
import json
import base64

conn = None

def pair():
    host = '0.0.0.0'  # Escucha en todas las interfaces de red
    port = 8080
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


def sendData(dataSend):
    try:
        dataSend = json.dumps(dataSend)
        encodeData = base64.b64encode(dataSend.encode('utf-8'))
        conn.send(encodeData)
    except OSError as e:
        print(f"Data Failed Send! ->\t{e}")
        return None
    print("Data Send!")


def sInfrared(dataSensor):
    inicio, fin = dataSensor
    duracion = fin - inicio
    distancia = (duracion * 0.0343) / 2
    print(f'Distancia detectada: {distancia}m')
    
    if distancia < 


if __name__ == '__main__':
    conn = pair()
    jsonData = {
        "type": "infrared",
        "data": "data"
    }
    sendData(jsonData)
    # while True:
    #     info = getData()
    #     sInfrared(info)
