from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from database import init_db
from models import (
    insert_history,
    update_occupation,
    get_all_voies,
    get_history
)
print("=== APP.PY STARTED ===")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()

@app.route("/event", methods=["POST"])
def receive_event():
    data = request.json

    insert_history(
        data["timestamp"],
        data["voie_id"],
        data["train_number"],
        data["action"],
        data["confidence"]
    )

    update_occupation(
        data["voie_id"],
        data["action"],
        data["train_number"]
    )

    socketio.emit("update", {
        "voie_id": data["voie_id"],
        "action": data["action"]
    })

    return jsonify({"message": "Event processed"}), 200


@app.route("/voies", methods=["GET"])
def voies():
    return jsonify(get_all_voies())


@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_history())

