from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import uuid
import os
import sys
import eventlet
from datetime import datetime, timedelta

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
    print(f"[DISCONNECT] User disconnected: {request.sid}")

    global waiting_players
    waiting_players = [p for p in waiting_players if p["sid"] != request.sid]

    for rid, room in list(rooms.items()):
        for p in room["players"]:
            if p["sid"] == request.sid:

                opponent = next(pl for pl in room["players"] if pl["sid"] != request.sid)
                socketio.emit("game_result", {"result": "win", "reason": "opponent_disconnected"}, to=opponent["sid"])
                del rooms[rid]
                print(f"[CLEANUP] Room {rid} removed after disconnect.")
                break

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
            "end_time": datetime.now() + timedelta(minutes=5)
        }

        socketio.start_background_task(room_timer, room_id)

        for p in players:
            emit(
                "matched",
                {"room": room_id, "players": [pl["username"] for pl in players]},
                to=p["sid"]
            )

def room_timer(rid):
    while rid in rooms:
        remaining = int((rooms[rid]["end_time"] - datetime.now()).total_seconds())
        if remaining <= 0:

            for p in rooms[rid]["players"]:
                socketio.emit("game_result", {"result": "lose", "reason": "timeout"}, to=p["sid"])
            del rooms[rid]
            print(f"[TIMER] Room {rid} timed out, both lose.")
            return

        for p in rooms[rid]["players"]:
            socketio.emit("time_update", {"seconds": remaining}, to=p["sid"])
        eventlet.sleep(1)

@socketio.on("submit_guess")
def on_submit_guess(data):
    room_id = data.get("room")
    guess = data.get("guess", "").upper()

    if room_id not in rooms:
        emit("status", {"message": "Room not found"})
        return

    game_instance = rooms[room_id]["game"]
    sid = request.sid

    if not game_instance.validate_guess(guess):
        emit("invalid_word", {"word": guess}, room=sid)
        return

    feedback = game_instance.check_guess(guess)
    rooms[room_id]["guesses"][sid].append({"word": guess, "feedback": feedback})

    emit("update_board", {"guess": guess, "feedback": feedback}, room=sid)

    opponent_sid = next(p["sid"] for p in rooms[room_id]["players"] if p["sid"] != sid)
    emit("update_opponent_board", {"feedback": feedback}, room=opponent_sid)

    if guess == game_instance.secret_word:
        emit("game_result", {"result": "win", "reason": "correct_guess"}, room=sid)
        emit("game_result", {"result": "lose", "reason": "opponent_correct"}, room=opponent_sid)
        del rooms[room_id]
        return

    player_guesses = rooms[room_id]["guesses"][sid]
    opponent_guesses = rooms[room_id]["guesses"][opponent_sid]

    player_exhausted = len(player_guesses) >= 6
    opponent_exhausted = len(opponent_guesses) >= 6

    if player_exhausted and opponent_exhausted:
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=sid)
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=opponent_sid)
        del rooms[room_id]
        return

    if player_exhausted:
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=sid)
        emit("game_result", {"result": "win", "reason": "opponent_turns_remaining"}, room=opponent_sid)
        del rooms[room_id]
        return

    if opponent_exhausted:
        emit("game_result", {"result": "win", "reason": "opponent_turns_exhausted"}, room=sid)
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=opponent_sid)
        del rooms[room_id]
        return

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:5000 ...")
    socketio.run(app, host="0.0.0.0", port=5000)
