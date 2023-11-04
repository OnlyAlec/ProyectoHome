from flask import Flask, request
from datetime import datetime
import json
from libSQL import DB, Operation
# import libNOSQL as dbNSQL


class Request:
    def __init__(self, dRequest: dict):
        self.db = dRequest["db"]
        self.crud = dRequest["crud"]
        self.dest = dRequest["dest"]
        self.data = dRequest["data"]

    def validateRequest(self):
        miss = []
        var = vars(self)
        for name, value in var.items():
            if value is None or value == "" or value is False:
                miss.append(name)
        return miss


class response:
    def __init__(self, status: str, message: str, time: str):
        self.status = status
        self.message = message
        self.time = time
        self.error = None

    def errorFormat(self):
        return json.dumps({
            "status": self.status,
            "error": self.error,
            "time": self.time
        })

    def successFormat(self):
        return json.dumps({
            "status": self.status,
            "message": self.message,
            "time": self.time
        })


# Init
app = Flask(__name__)


# @app.route("/api/v1/sql", methods=["GET"])
@app.route("/api/v1/sql", methods=["POST"])
def mainGETDB():
    req = Request(request.form.to_dict())
    if miss := req.validateRequest():
        return response("400", "Missing {miss}" + " " + ", ".join(miss), str(datetime.now())).errorFormat()
    if req.db == "SQL":
        db = DB()
        Operation(db, req.crud, req.data)
        return response("200", "OK", str(datetime.now())).successFormat()
    # elif req.db == "NOSQL":
        # db = dbNSQL.DB()
    return {}
