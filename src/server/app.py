from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import uuid
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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

    # เช็คว่าผู้เล่นอยู่ใน waiting list หรือยัง
    if any(p["sid"] == request.sid for p in waiting_players):
        emit("status", {"message": "Already waiting..."})
        return

    waiting_players.append({"sid": request.sid, "username": username})

    if len(waiting_players) >= 2:
        p1 = waiting_players.pop(0)
        p2 = waiting_players.pop(0)
        room_id = str(uuid.uuid4())[:8]
        players = [p1, p2]

        game_instance = WordGame()  
        secret = game_instance.start_new_game()
        print(f"[DEBUG] Room {room_id} secret word: {secret}")

        rooms[room_id] = {
            "players": players,
            "guesses": {p1["sid"]: [], p2["sid"]: []},
            "game": game_instance
        }

        for p in players:
            emit(
                "matched",
                {"room": room_id, "players": [pl["username"] for pl in players]},
                to=p["sid"]
            )


@socketio.on("submit_guess")
def on_submit_guess(data):
    room_id = data.get("room")
    guess = data.get("guess", "").upper()

    if room_id not in rooms:
        emit("status", {"message": "Room not found"})
        return

    game_instance = rooms[room_id]["game"]

    # ตรวจสอบว่า guess อยู่ใน dictionary
    if not game_instance.validate_guess(guess):
        emit("invalid_word", {"word": guess}, room=request.sid)
        return

    feedback = game_instance.check_guess(guess)

    # เก็บคำและ feedback
    rooms[room_id]["guesses"][request.sid].append({"word": guess, "feedback": feedback})

    # ส่งให้ผู้เล่นตัวเอง
    emit("update_board", {"guess": guess, "feedback": feedback}, room=request.sid)

    # ส่งให้คู่ต่อสู้ → แค่ feedback
    opponent_sid = None
    for p in rooms[room_id]["players"]:
        if p["sid"] != request.sid:
            opponent_sid = p["sid"]
            emit("update_opponent_board", {"feedback": feedback}, room=opponent_sid)

    # ตรวจเงื่อนไขชนะ
    # 1. ผู้เล่นตัวเองใส่คำถูกต้อง
    if guess == game_instance.secret_word:
        emit("game_result", {"result": "win"}, room=request.sid)
        if opponent_sid:
            emit("game_result", {"result": "lose"}, room=opponent_sid)
        return

    # 2. ฝ่ายตรงข้ามหมด 6 รอบและเดาไม่ถูก
    if opponent_sid and len(rooms[room_id]["guesses"][opponent_sid]) >= 6:
        correct_guesses = [g for g in rooms[room_id]["guesses"][opponent_sid] if g["word"] == game_instance.secret_word]
        if not correct_guesses:
            emit("game_result", {"result": "win"}, room=request.sid)
            emit("game_result", {"result": "lose"}, room=opponent_sid)


if __name__ == "__main__":
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
