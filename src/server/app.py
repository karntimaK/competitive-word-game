from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import uuid
import os

app = Flask(__name__, static_folder="../../static", template_folder="../../client")
socketio = SocketIO(app, cors_allowed_origins="*")

waiting_players = []  # [{ "sid": xxx, "username": "Alice" }]
rooms = {}            # { room_id: [ {sid, username}, {sid, username} ] }


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "../../client")

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")


@socketio.on("connect")
def on_connect(auth):
    print("A user connected:", request.sid)


@socketio.on('find_match')
def on_find_match(data):
    username = data.get("username", "Anonymous")
    
    emit("status", {"message": "Searching for a match..."})

    # ตรวจว่า user นี้อยู่ waiting list อยู่แล้วหรือยัง
    if any(p["sid"] == request.sid for p in waiting_players):
        emit("status", {"message": "Already waiting for opponent..."})
        return

    # เพิ่ม user ใหม่
    waiting_players.append({"sid": request.sid, "username": username})

    # จับคู่ทันทีถ้ามี >=2 คน
    while len(waiting_players) >= 2:
        p1 = waiting_players.pop(0)
        p2 = waiting_players.pop(0)

        room_id = str(uuid.uuid4())[:8]
        players = [p1, p2]
        rooms[room_id] = players

        for p in players:
            join_room(room_id, sid=p["sid"])

        socketio.emit(
            "matched",
            {"room": room_id, "players": [pl["username"] for pl in players]},
            room=room_id
        )


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
