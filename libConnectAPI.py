import json
import http.client
import queue
from firebase_admin import db

q = queue.Queue()


def sendNoSQL(sensor: str, data: dict, tR: str, tP: str):
    ref = db.reference(sensor)
    ref.child(tR).set(
        {"data": data, "timeProcess": tP})
    print("Data send to server!")


def listenAPIWorker(data):
    parseData = json.loads(data)
    q.put(data)


def senderAPIWorker(qNoSQL):
    while True:
        if not qNoSQL.empty():
            data = qNoSQL.get()
            headers = {'Content-Type': 'application/json'}
            jsonData = json.dumps(data)

            conn = http.client.HTTPSConnection('https://localhost:80')
            conn.request("POST", "/v1.0/db", jsonData, headers)
