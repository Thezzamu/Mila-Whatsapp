import os
import json
import threading
from flask import Flask, request, jsonify
import requests
from mila import (
    mila_reply,
    mila_maybe_initiate,
    update_emotional_memory,
    remember_event
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

ACCESS_TOKEN = os.environ.get("EAAXOFb0FfcoBQujmZCu3d28JcazeAzlZB1TWj1Bt6DArmd7FZAAXdGZCY3oFNhlZAnbKaAt0W6rgQW9zlq880rbm27EttcjdveEVMuPUlhnsZCOs0JzZBrw1z22r7Wc0iLZAElYUtdFIyEQYrptw3GOiFZAndUY7ZBrdZC7P0L7KquSgZCVg91EZAf4ZBQY3Np9IBoW4WqRJNgQIkrzthhe2srSjsCcY3sQwHVCuQV0E668W0QcEywNJ9pYNEnwyGoDPpSZBb7meG43U4sZB75rwCZCWMhEdYGN2s")
PHONE_NUMBER_ID = os.environ.get("1002065182983203")

STATE_FILE = "memory.json"

app = Flask(__name__)
lock = threading.Lock()


# --------------------------------------------------
# STATE PERSISTENCE
# --------------------------------------------------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# --------------------------------------------------
# WHATSAPP SEND
# --------------------------------------------------

def send_message(to, text):
    if not text:
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    r = requests.post(url, headers=headers, json=payload)
    print("SEND_MESSAGE STATUS:", r.status_code)
    print("SEND_MESSAGE RESP:", r.text)


# --------------------------------------------------
# WEBHOOK VERIFY
# --------------------------------------------------

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == "mila":
        return request.args.get("hub.challenge"), 200
    return "Forbidden", 403


# --------------------------------------------------
# WEBHOOK RECEIVE
# --------------------------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("INCOMING:", data)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        # ignora eventi che non sono messaggi
        if "messages" not in value:
            print("No messages event, ignoring")
            return jsonify(ok=True), 200

        msg = value["messages"][0]
        user = msg["from"]
        text = msg.get("text", {}).get("body")

        if not text:
            print("No text body")
            return jsonify(ok=True), 200

        with lock:
            state = load_state()

            # aggiornamento memoria emotiva base
            update_emotional_memory(state, "attenzione")

            # risposta principale
            reply = mila_reply(text, state)
            print("TEXT:", text)
            print("REPLY:", reply)

            if reply:
                send_message(user, reply)
                state["ultima_risposta"] = state.get("ultima_risposta", 0)

            # possibile iniziativa spontanea
            spontaneo = mila_maybe_initiate(state)
            if spontaneo:
                send_message(user, spontaneo)

            save_state(state)

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return jsonify(ok=True), 200


# --------------------------------------------------
# START CHAT (APERTURA CONVERSAZIONE)
# --------------------------------------------------

@app.route("/start", methods=["GET"])
def start_chat():
    test_number = os.environ.get("393391236716")

    if not test_number:
        return "test number non configurato", 400

    state = load_state()
    remember_event(state, "positivo", 0.1)
    save_state(state)

    send_message(test_number, "Hey")
    return "ok", 200



# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





