# flask 클래스를 import한다.
from flask import Flask

# flask 클래스 인스턴스화한다
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, Flaskbook!"