import os
import threading
import queue
from dotenv import load_dotenv
from firebase_admin import db, credentials, initialize_app
from libConnect import initConnectRPI, listenerWorker

load_dotenv()
q = queue.Queue()
conn = None


def initFirebase():
    cred = credentials.Certificate('./Auth/firebase.json')
    initialize_app(cred, {'databaseURL': os.getenv('URL_FIREBASE')})


def sendNoSQL(sensor: str, data: dict, tR: str, tP: str):
    ref = db.reference(sensor)
    ref.child(tR).set(
        {"data": data, "timeProcess": tP})
    print("Data send to server!")


if __name__ == '__main__':
    print("Init Center RPI..")
    conn = initConnectRPI()
    initFirebase()

    gD = threading.Thread(target=listenerWorker, args=(conn, q), daemon=True)
    gD.start()

    while True:
        d: dict = q.get()
        print("\n", d)
        sendNoSQL(d["sensor"], d["data"], d["timeRecived"], d["timeProcess"])
        q.task_done()
