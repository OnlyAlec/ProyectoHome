from flask import Flask, request, make_response
from libSQL import DB, Operation
from flask_cors import CORS
# import libNOSQL as dbNSQL


class Request:
    def __init__(self, dRequest):
        self.db = dRequest.get("db")
        self.crud = dRequest.get("crud")
        self.data = self.getData(dRequest.get("data"))

    def validateRequest(self, method=None):
        if method == "POST" and self.crud not in ["INSERT", "DELETE", "UPDATE"]:
            return ["Invalid CRUD"]
        if method == "GET" and self.crud not in ["SELECT"]:
            return ["Invalid CRUD"]

        miss = []
        var = vars(self)
        for name, value in var.items():
            if value is None or value == "" or value is False:
                miss.append(name)
        return miss

    def getData(self, data: str | dict):
        if isinstance(data, str):
            key, value = data.split(":")[0], data.split(":")[1]
            return [key, value]

        if isinstance(data, dict):
            return data

    def respondServer(self, text: tuple[str, str | Exception], code: int):
        resp = make_response({text[0]: text[1]}, code)
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


# Init
app = Flask(__name__)
CORS(app)


@app.route("/api/v1/sql", methods=["GET", "POST"])
def mainGETDB():
    if request.is_json is False:
        req = Request(request.args)
    else:
        req = Request(request.json)
    if miss := req.validateRequest(request.method):
        return req.respondServer(("error", "Missing " + ", ".join(miss)), 400)
    if req.db == "SQL":
        try:
            db = DB()
            reqOp = Operation(db, req.crud, req.data)
            if reqOp.error:
                return req.respondServer(("error", reqOp.error), 400)
            return req.respondServer(("action", "OK"), 200)
        except Exception as e:
            return req.respondServer(("error", e.args[0].message.split("\n")[0]), 500)
    # elif req.db == "NOSQL":
    # db = dbNSQL.DB()
    return {}
