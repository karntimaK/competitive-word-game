from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import os

app = Flask(__name__, static_folder="../../static", template_folder="../../client")
socketio = SocketIO(app, cors_allowed_origins="*")

waiting_players = []
rooms = {}

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

    if any(p["sid"] == request.sid for p in waiting_players):
        emit("status", {"message": "Already waiting for opponent..."})
        return

    waiting_players.append({"sid": request.sid, "username": username})

    if len(waiting_players) >= 2:
        p1 = waiting_players.pop(0)
        p2 = waiting_players.pop(0)
        room_id = str(uuid.uuid4())[:8]
        players = [p1, p2]
        rooms[room_id] = {
            "players": players,
            "guesses": {p1["sid"]: [], p2["sid"]: []}  # เก็บคำของแต่ละคน
        }

        for p in players:
            join_room(room_id, sid=p["sid"])

        socketio.emit(
            "matched",
            {"room": room_id, "players": [pl["username"] for pl in players]},
            room=room_id
        )

@socketio.on("submit_guess")
def on_submit_guess(data):
    room_id = data.get("room")
    guess = data.get("guess", "").upper()

    if room_id not in rooms:
        emit("status", {"message": "Room not found"})
        return

    # บันทึกคำเดาใน game state
    rooms[room_id]["guesses"][request.sid].append(guess)

    # ส่งกลับให้ผู้เล่นอัพเดตตาราง (placeholder สี GREY)
    emit("update_board", {"guess": guess}, room=request.sid)

@socketio.on('disconnect')
def on_disconnect():
    print("A user disconnected:", request.sid)
    global waiting_players
    waiting_players = [p for p in waiting_players if p["sid"] != request.sid]
    # TODO: handle disconnect กลางห้อง

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
