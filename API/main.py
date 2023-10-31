from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request

load_dotenv()

# Init
app = Flask(__name__)


@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"
