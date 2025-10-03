from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import uuid
import os
from game_core.core_logic import WordGame

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
        emit("status", {"message": "Already waiting..."})
        return

    waiting_players.append({"sid": request.sid, "username": username})

    if len(waiting_players) >= 2:
        p1 = waiting_players.pop(0)
        p2 = waiting_players.pop(0)
        room_id = str(uuid.uuid4())[:8]
        players = [p1, p2]

        # สร้าง WordGame instance สำหรับห้องนี้
        game_instance = WordGame()  # ใช้ mock secret_word
        rooms[room_id] = {
            "players": players,
            "guesses": {p1["sid"]: [], p2["sid"]: []},
            "game": game_instance
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

    # ตรวจคำด้วย core_logic
    game_instance = rooms[room_id]["game"]
    feedback = game_instance.check_guess(guess)

    # เก็บคำเดาและ feedback
    rooms[room_id]["guesses"][request.sid].append({"word": guess, "feedback": feedback})

    # ส่ง feedback สีไปอัพเดตตารางผู้เล่นตัวเอง
    emit("update_board", {"guess": guess, "feedback": feedback}, room=request.sid)

    # ส่ง feedback ไปอัพเดตมุมเล็กของฝ่ายตรงข้าม
    for player in rooms[room_id]["players"]:
        if player["sid"] != request.sid:
            emit("update_opponent_board", {"feedback": feedback}, room=player["sid"])

if __name__ == "__main__":
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
