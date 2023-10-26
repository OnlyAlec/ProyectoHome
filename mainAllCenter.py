import os
import socket
import threading
import queue
import json
from firebase_admin import db, credentials, initialize_app

conn = socket.socket()
q = queue.Queue()


def pair():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 2050))
    s.listen(1)
    print('Listening for RPI...', end=" ")

    connection, addr = s.accept()
    print(f'\tOK!:  {addr}')
    return connection


def getDataWorker():
    while True:
        data = conn.recv(1024)
        print("\t▣ Getting data...", end=" ")
        try:
            data = json.loads(data.decode('utf-8'))
            q.put(data)
            data = None
            print("\tOK!")
        except Exception as e:
            print(f"\tFAILED! ->\t{e}: {e.args}")


def sendNoSQL(sensor: str, data: dict, tR: str, tP: str):
    cred = credentials.Certificate('./.env/firebase.json')
    initialize_app(cred, {
        'databaseURL': os.getenv('URL_FIREBASE')
    })
    ref = db.reference(f'Registros_{sensor}')
    ref.child(tP).set(data)
    print("Data send to server!")


if __name__ == '__main__':
    print("Init Center RPI..")
    conn = pair()

    gD = threading.Thread(target=getDataWorker, daemon=True)
    gD.start()

    while True:
        d: dict = q.get()
        print(d)
        sendNoSQL(d["sensor"], d["data"], d["timeRecived"], d["timeProcess"])
        q.task_done()
