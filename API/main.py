import json
from queue import Queue
from flask import Flask, request, make_response
from oracledb import DatabaseError, OperationalError
from flask_cors import CORS
from firebase_admin import db as firebaseDB
from libSQL import DB, Operation
from libNOSQL import ConnectionFirebase, Firebase

q = Queue()


def respondServer(text, code: int):
    resp = make_response({text[0]: text[1]}, code)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


class Request:
    def __init__(self, dRequest):
        self.crud = dRequest.get("crud")
        self.data = dRequest.get("data")

    def validateRequestSQL(self, method=None):
        if method == None:
            return "Method not found"
        if method == "POST" and self.crud not in ["INSERT", "DELETE", "UPDATE"]:
            return "Invalid CRUD"
        if method == "GET" and self.crud not in ["SELECT"]:
            return "Invalid CRUD"
        if not self.data:
            return "Not Data"


# Init
app = Flask(__name__)
CORS(app)
firebaseApp = ConnectionFirebase(q)


@app.route("/v1.0/dbsql", methods=["GET", "POST"])
def mainSQL():
    app.logger.info('Init request SQL!')
    req = Request(request.json if request.is_json else request.args)
    if miss := req.validateRequestSQL(request.method):
        return respondServer(("error", miss), 400)
    try:
        db = DB()
        reqOp = Operation(db, req.crud, req.data)
        app.logger.info('Return request!')
        return respondServer(("OK", reqOp.response), 200)
    except Exception as e:
        if isinstance(e, (OperationalError, DatabaseError)):
            app.logger.error(e.args[0].message)
            return respondServer(("error", e.args[0].message), 500)
        app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
        return respondServer(("error", e.args[0]), 500)

    app.logger.critical('Client end up here! Problem with structure!')
    return "Que haces aqui? Hablale a Alec!"


@app.route("/v1.0/dbnosql", methods=["GET", "POST"])
def firebasePushPull():
    app.logger.info('Init request NoSQL!')
    # &Cuando mando datos para la firebase
    if request.method == "POST":
        if not isinstance(request.json, list):
            listData = [request.json]
        else:
            listData = request.json

        for data in listData:
            db = Firebase(data)
            db.parseJSON()
            try:
                if db.type == "notification":
                    db.insertNotification()
                else:
                    db.insertBucket()
                    db.insertReg()
                    db.insertLastReg()
            except Exception as e:
                app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
                return respondServer(("error", e.args[0]), 500)
        return respondServer(("OK", "Data inserted"), 200)

    # &Cuando recibo datos del firebase
    try:
        listAction = []
        while not q.empty():
            listAction.append(q.get())

        if len(listAction) == 0:
            return respondServer(("error", "No data"), 400)

        jsonList = json.dumps(listAction)
        return jsonList
    except Exception as e:
        app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
        return respondServer(("error", e.args[0]), 500)

    app.logger.critical('Client end up here! Problem with structure!')
    return "Que haces aqui? Hablale a Alec!"


@app.route("/v1.0/dbnosql/getState", methods=["GET"])
def firebaseGetState():
    actions = []
    try:
        for space in firebaseApp.spaces:
            url = f"{firebaseApp.baseSpaces}/{space}/Dispositivos"
            data = firebaseDB.reference(url).get()
            for disp, args in dict(data).items():
                dispParse, fn = firebaseApp.parseDisp(disp.upper())
                if dispParse == "null":
                    continue
                jsonAction = {
                    "function": fn,
                    "args": {
                        disp: f"{dispParse.upper()}_{space.upper()}",
                        "state": "ON" if args["estado"] else "OFF"
                    }
                }
                actions.append(jsonAction)
        return json.dumps(actions)
    except Exception as e:
        app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
        return respondServer(("error", e.args[0]), 500)
