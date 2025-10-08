from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import uuid
import os
import sys
import eventlet
from datetime import datetime, timedelta
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_core.core_logic import WordGame

app = Flask(__name__, static_folder="../../static", template_folder="../../client")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

waiting_players = []
rooms = {}
room_codes = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(BASE_DIR, "../../client")

@app.route("/")
def index():
    return send_from_directory(CLIENT_DIR, "index.html")

def generate_code():
    """Generate a unique 6-digit numeric code."""
    for _ in range(1000):
        code = f"{random.randint(0, 999999):06d}"
        if code not in room_codes:
            return code
    return f"{random.randint(0, 999999):06d}"

def cleanup_room(rid):
    """Remove room and its code mapping (if any)."""
    if rid in rooms:
        code = rooms[rid].get("code")
        if code and code in room_codes:
            del room_codes[code]
        del rooms[rid]
        print(f"[CLEANUP] Room {rid} removed.")

@socketio.on("connect")
def on_connect(auth):
    print(f"[CONNECT] A user connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    print(f"[DISCONNECT] User disconnected: {sid}")

    global waiting_players
    waiting_players = [p for p in waiting_players if p["sid"] != sid]

    for rid, room in list(rooms.items()):
        if any(p["sid"] == sid for p in room["players"]):
            if room.get("game") is None:
                other = next((pl for pl in room["players"] if pl["sid"] != sid), None)
                if other:
                    socketio.emit("status", {"message": "Creator left the room"}, to=other["sid"])
                cleanup_room(rid)
                return

            opponent = next((pl for pl in room["players"] if pl["sid"] != sid), None)
            if opponent:
                socketio.emit("player_disconnected", {"message": "Opponent disconnected"}, to=opponent["sid"])
                socketio.emit("game_result", {"result": "win", "reason": "opponent_disconnected"}, to=opponent["sid"])
            cleanup_room(rid)
            return

@socketio.on("create_room")
def on_create_room(data):
    """Client requests to create a 6-digit private room. Creator is added as first player (room waits)."""
    username = data.get("username", "Anonymous")
    sid = request.sid

    code = generate_code()
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        "players": [{"sid": sid, "username": username}],
        "guesses": {sid: []},
        "game": None,
        "end_time": None,
        "code": code
    }
    room_codes[code] = room_id

    print(f"[CREATE_ROOM] {username} ({sid}) created room {room_id} code={code}")
    emit("room_created", {"room": room_id, "code": code}, room=sid)

@socketio.on("join_room_code")
def on_join_room_code(data):
    """Client provides a 6-digit code to join a custom room."""
    code = data.get("code")
    username = data.get("username", "Anonymous")
    sid = request.sid

    if not code:
        emit("join_failed", {"message": "No code provided"}, room=sid)
        return

    room_id = room_codes.get(code)
    if not room_id or room_id not in rooms:
        emit("join_failed", {"message": "Room code not found"}, room=sid)
        return

    room = rooms[room_id]

    if len(room["players"]) >= 2:
        emit("join_failed", {"message": "Room already full"}, room=sid)
        return

    room["players"].append({"sid": sid, "username": username})
    room["guesses"][sid] = []

    game_instance = WordGame()
    secret = game_instance.start_new_game()
    room["game"] = game_instance
    room["end_time"] = datetime.now() + timedelta(minutes=5)

    socketio.start_background_task(room_timer, room_id)

    for p in room["players"]:
        emit("matched", {"room": room_id, "players": room["players"]}, room=p["sid"])

    print(f"[JOIN_ROOM] {username} ({sid}) joined room {room_id} code={code}, secret={secret}")

@socketio.on("find_match")
def on_find_match(data):
    """Random matching (existing behavior)."""
    username = data.get("username", "Anonymous")
    sid = request.sid
    emit("status", {"message": "Searching for a match..."}, room=sid)

    if any(p["sid"] == sid for p in waiting_players):
        emit("status", {"message": "Already waiting..."}, room=sid)
        return

    waiting_players.append({"sid": sid, "username": username})
    print(f"[FIND] {username} queued for random match ({sid})")

    if len(waiting_players) >= 2:
        p1 = waiting_players.pop(0)
        p2 = waiting_players.pop(0)
        room_id = str(uuid.uuid4())[:8]
        players = [p1, p2]

        game_instance = WordGame()
        secret = game_instance.start_new_game()
        rooms[room_id] = {
            "players": players,
            "guesses": {p1["sid"]: [], p2["sid"]: []},
            "game": game_instance,
            "end_time": datetime.now() + timedelta(minutes=5),
            "code": None
        }
        socketio.start_background_task(room_timer, room_id)

        for p in players:
            emit(
                "matched",
                {"room": room_id, "players": players},
                room=p["sid"]
            )

        print(f"[MATCHED] Random {p1['username']} vs {p2['username']} in room {room_id} secret={secret}")

def room_timer(rid):
    """Background timer that emits time_update and handles timeout outcomes."""
    while True:
        if rid not in rooms:
            print(f"[TIMER] Stopping timer for removed room {rid}")
            return

        room = rooms[rid]
        end_time = room.get("end_time")
        if not end_time:
            eventlet.sleep(1)
            continue

        remaining = int((end_time - datetime.now()).total_seconds())
        if remaining <= 0:
            for p in room["players"]:
                socketio.emit("game_result", {"result": "lose", "reason": "time_expired"}, to=p["sid"])
            cleanup_room(rid)
            print(f"[TIMER] Room {rid} timed out, both lose.")
            return

        for p in room["players"]:
            socketio.emit("time_update", {"seconds": remaining}, to=p["sid"])

        eventlet.sleep(1)

@socketio.on("submit_guess")
def on_submit_guess(data):
    room_id = data.get("room")
    guess = data.get("guess", "").upper()
    sid = request.sid

    if room_id not in rooms:
        emit("status", {"message": "Room not found"}, room=sid)
        return

    room = rooms[room_id]
    game = room.get("game")
    if game is None:
        emit("status", {"message": "Game has not started yet (waiting for opponent)."}, room=sid)
        return

    if not game.validate_guess(guess):
        emit("invalid_word", {"word": guess}, room=sid)
        return

    feedback = game.check_guess(guess)
    room["guesses"][sid].append({"word": guess, "feedback": feedback})

    emit("update_board", {"guess": guess, "feedback": feedback}, room=sid)

    opponent = next((pl for pl in room["players"] if pl["sid"] != sid), None)
    opponent_sid = opponent["sid"] if opponent else None
    if opponent_sid:
        emit("update_opponent_board", {"feedback": feedback}, room=opponent_sid)

    if guess == game.secret_word:
        emit("game_result", {"result": "win", "reason": "correct_guess"}, room=sid)
        if opponent_sid:
            emit("game_result", {"result": "lose", "reason": "opponent_correct"}, room=opponent_sid)
        cleanup_room(room_id)
        return

    player_guesses = room["guesses"].get(sid, [])
    opponent_guesses = room["guesses"].get(opponent_sid, []) if opponent_sid else []
    player_exhausted = len(player_guesses) >= 6
    opponent_exhausted = len(opponent_guesses) >= 6

    if player_exhausted and opponent_exhausted:
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=sid)
        if opponent_sid:
            emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=opponent_sid)
        cleanup_room(room_id)
        return

    if player_exhausted:
        emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=sid)
        if opponent_sid:
            emit("game_result", {"result": "win", "reason": "opponent_turns_remaining"}, room=opponent_sid)
        cleanup_room(room_id)
        return

    if opponent_exhausted:
        emit("game_result", {"result": "win", "reason": "opponent_turns_exhausted"}, room=sid)
        if opponent_sid:
            emit("game_result", {"result": "lose", "reason": "turns_exhausted"}, room=opponent_sid)
        cleanup_room(room_id)
        return

@socketio.on("leave_room")
def on_leave_room(data):
    sid = request.sid

    global waiting_players
    waiting_players = [p for p in waiting_players if p["sid"] != sid]

    for rid, room in list(rooms.items()):
        for p in room["players"]:
            if p["sid"] == sid:
                if room.get("game") is None:
                    cleanup_room(rid)
                else:
                    opponent = next((pl for pl in room["players"] if pl["sid"] != sid), None)
                    if opponent:
                        socketio.emit("game_result", {"result": "win", "reason": "opponent_left"}, to=opponent["sid"])
                    cleanup_room(rid)
                return

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:5000 ...")
    socketio.run(app, host="0.0.0.0", port=5000)
