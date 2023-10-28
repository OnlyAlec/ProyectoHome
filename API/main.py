from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request

load_dotenv()

# Init
app = Flask(__name__)


@app.route("/api/v1.0/helloWorld", methods=["GET"])
def login():
    dataRequest = request.form.to_dict()
    testParam = request.form.get("Test")
    if testParam:
        dataJSON = {
            "data": {
                "text": "Hello World";
            },
            "time": datetime.now(),
        }
        dataResponse = jsonify(dataJSON)
        dataResponse.headers.add("Content-Type", "application/json")
        return dataResponse
    abort(400, "Faltan parametros")

if __name__ == "__main__":
    app.run()