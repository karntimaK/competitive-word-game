from flask import Flask, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="../../static", template_folder="../../client")
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "../../client")

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
