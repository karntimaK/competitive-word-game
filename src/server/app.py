from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import uuid
import os
import sys
import time
import eventlet

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_core.core_logic import WordGame

app = Flask(__name__, static_folder="../../static", template_folder="../../client")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

waiting_players = []
rooms = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "../../client")

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")

@socketio.on("connect")
def on_connect(auth):
    print(f"[CONNECT] A user connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    print(f"[DISCONNECT] User disconnected: {sid}")

    global waiting_players
    waiting_players = [p for p in waiting_players if p["sid"] != sid]

    room_to_remove = None
    opponent_sid = None
    for room_id, room_data in list(rooms.items()):
        if any(p["sid"] == sid for p in room_data["players"]):
            room_to_remove = room_id
            for p in room_data["players"]:
                if p["sid"] != sid:
                    opponent_sid = p["sid"]
            break

    if room_to_remove:
        if opponent_sid:
            emit("player_left", {"message": "Opponent disconnected."}, to=opponent_sid)
            emit("game_result", {"result": "win"}, to=opponent_sid)

        timer_task = rooms[room_to_remove].get("timer_task")
        if timer_task:
            rooms[room_to_remove]["timer_cancelled"] = True
        del rooms[room_to_remove]
        print(f"[CLEANUP] Room {room_to_remove} removed after disconnect.")

@socketio.on("find_match")
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

        game_instance = WordGame()
        secret = game_instance.start_new_game()
        print(f"[DEBUG] Room {room_id} secret word: {secret}")

        rooms[room_id] = {
            "players": players,
            "guesses": {p1["sid"]: [], p2["sid"]: []},
            "game": game_instance,
            "timer_cancelled": False
        }

        def room_timer(rid):
            total_seconds = 5 * 60
            while total_seconds > 0:
                # ถ้า room ถูกลบไปแล้ว (disconnect หรือจบเกม) → ออก
                if rid not in rooms:
                    print(f"[TIMER] Room {rid} no longer exists, stopping timer.")
                    return

                remaining = total_seconds
                for p in rooms[rid]["players"]:
                    socketio.emit("time_update", {"seconds": remaining}, to=p["sid"])
                
                eventlet.sleep(1)
                total_seconds -= 1

            # timeout → room ยังอยู่
            if rid in rooms:
                print(f"[TIMER] Room {rid} timed out, both lose.")
                for p in rooms[rid]["players"]:
                    socketio.emit("game_result", {"result": "timeout"}, to=p["sid"])
                # ลบ room หลังหมดเวลา
                del rooms[rid]
                print(f"[TIMER] Room {rid} removed after timeout.")

        timer_task = socketio.start_background_task(room_timer, room_id)
        rooms[room_id]["timer_task"] = timer_task

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
    sid = request.sid

    if room_id not in rooms:
        emit("status", {"message": "Room not found"})
        return

    room_data = rooms[room_id]
    game_instance = room_data["game"]

    if not game_instance.validate_guess(guess):
        emit("invalid_word", {"word": guess}, room=sid)
        return

    feedback = game_instance.check_guess(guess)
    room_data["guesses"][sid].append({"word": guess, "feedback": feedback})

    emit("update_board", {"guess": guess, "feedback": feedback}, room=sid)

    opponent_sid = None
    for p in room_data["players"]:
        if p["sid"] != sid:
            opponent_sid = p["sid"]
            emit("update_opponent_board", {"feedback": feedback}, room=opponent_sid)

    if guess == game_instance.secret_word:
        emit("game_result", {"result": "win"}, room=sid)
        if opponent_sid:
            emit("game_result", {"result": "lose"}, room=opponent_sid)
        room_data["timer_cancelled"] = True
        del rooms[room_id]
        return

    if opponent_sid and len(room_data["guesses"][opponent_sid]) >= 6:
        correct_guesses = [
            g for g in room_data["guesses"][opponent_sid]
            if g["word"] == game_instance.secret_word
        ]
        if not correct_guesses:
            emit("game_result", {"result": "win"}, room=sid)
            emit("game_result", {"result": "lose"}, room=opponent_sid)
            room_data["timer_cancelled"] = True
            del rooms[room_id]

if __name__ == "__main__":
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
