import json
from queue import Queue
from flask import Flask, request, make_response
from oracledb import DatabaseError, OperationalError
from flask_cors import CORS

from libSQL import DB, Operation
from libNOSQL import NODB, Firebase

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


dbnosql = NODB(q)
dbnosql.setupListeners()


@app.route("/v1.0/dbnosql", methods=["GET", "POST"])
def mainNoSQL():
    app.logger.info('Init request NoSQL!')
    if not request.is_json and len(request.args) == 0 and request.method == "POST":
        return "Invalid request", 400

    # &Cuando mando datos para la firebase
    if request.method == "POST":
        db = Firebase(request.json)
        try:
            if db.type == "notification":
                db.insertNotification()
                return "OK POST!"
            db.parseJSON()
            db.insertBucket()
            db.insertReg()
            db.insertLastReg()
            return "OK POST!"
        except Exception as e:
            app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
            return respondServer(("error", e.args[0]), 500)

    # &Cuando recibo datos del firebase
    else:
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
