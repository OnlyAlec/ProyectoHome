from flask import Flask, request, make_response
from oracledb import DatabaseError, OperationalError
from libSQL import DB, Operation
from flask_cors import CORS
# import libNOSQL as dbNSQL


class Request:
    def __init__(self, dRequest):
        self.db = dRequest.get("db")
        self.crud = dRequest.get("crud")
        self.data = dRequest.get("data")

    def validateRequest(self, method=None):
        if method == None:
            return "Method not found"
        if method == "POST" and self.crud not in ["INSERT", "DELETE", "UPDATE"]:
            return "Invalid CRUD"
        if method == "GET" and self.crud not in ["SELECT"]:
            return "Invalid CRUD"
        if self.db not in ["SQL", "NOSQL"]:
            return "Invalid DB"
        if not self.data:
            return "Not Data"

    def respondServer(self, text, code: int):
        resp = make_response({text[0]: text[1]}, code)
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


# Init
app = Flask(__name__)
CORS(app)


@app.route("/v1.0/db", methods=["GET", "POST"])
def mainGETDB():
    app.logger.info('Init request!')
    req = Request(request.json if request.is_json else request.args)
    if miss := req.validateRequest(request.method):
        return req.respondServer(("error", miss), 400)
    if req.db == "SQL":
        try:
            db = DB()
            reqOp = Operation(db, req.crud, req.data)
            app.logger.info('Return request!')
            return req.respondServer(("OK", reqOp.response), 200)
        except Exception as e:
            if isinstance(e, (OperationalError, DatabaseError)):
                app.logger.error(e.args[0].message)
                return req.respondServer(("error", e.args[0].message), 500)
            app.logger.error("%s ->\t %s", str(type(e)), e.args[0])
            return req.respondServer(("error", e.args[0]), 500)
    # elif req.db == "NOSQL":
    # db = dbNSQL.DB()
    app.logger.critical('Client end up here! Problem with structure!')
    return "Que haces aqui? Hablale a Alec!"
