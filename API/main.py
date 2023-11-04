from flask import Flask, request, make_response
from libSQL import DB, Operation
# import libNOSQL as dbNSQL


class Request:
    def __init__(self, dRequest):
        self.db = dRequest.get("db")
        self.crud = dRequest.get("crud")
        self.data = dRequest.get("data")

    def validateRequest(self):
        miss = []
        var = vars(self)
        for name, value in var.items():
            if value is None or value == "" or value is False:
                miss.append(name)
        return miss

    def respondServer(self, text: tuple[str, str | Exception], code: int):
        resp = make_response({text[0]: text[1]}, code)
        resp.headers["Content-Type"] = "application/json"
        return resp


# Init
app = Flask(__name__)


# @app.route("/api/v1/sql", methods=["GET"])
@app.route("/api/v1/sql", methods=["POST"])
def mainGETDB():
    req = Request(request.json)
    if miss := req.validateRequest():
        return req.respondServer(("error", "Missing " + ", ".join(miss)), 400)
    if req.db == "SQL":
        try:
            db = DB()
            reqOp = Operation(db, req.crud, req.data)
            if reqOp.error:
                return req.respondServer(("error", reqOp.error), 400)
            return req.respondServer(("action", "OK"), 200)
        except Exception as e:
            return req.respondServer(("error", e), 500)
    # elif req.db == "NOSQL":
        # db = dbNSQL.DB()
    return {}
