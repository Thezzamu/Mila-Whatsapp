import os
import requests
from flask import Flask, request, jsonify
from mila import mila_reply

# =========================
# CONFIG
# =========================

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# METTI QUI IL TUO NUMERO PERSONALE (SENZA +)
# es: 393391236716
TEST_NUMBER = "393391236716"

if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
    raise RuntimeError("ACCESS_TOKEN o PHONE_NUMBER_ID mancanti")

# =========================
# APP
# =========================

app = Flask(__name__)

print("### SERVER STARTED ###")

# =========================
# WHATSAPP SEND
# =========================

def send_message(to, text):
    print(f"### SEND_MESSAGE → {to}: {text}")

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

    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)


# =========================
# WEBHOOK VERIFY (META)
# =========================

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == "mila":
        return challenge, 200

    return "Forbidden", 403


# =========================
# WEBHOOK RECEIVE
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("### WEBHOOK HIT ###")
    print(data)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        messages = value.get("messages")
        if not messages:
            print("No messages field, ignoring")
            return jsonify(ok=True), 200

        msg = messages[0]
        user = msg["from"]
        text = msg.get("text", {}).get("body")

        if not text:
            print("No text body, ignoring")
            return jsonify(ok=True), 200

        print("TEXT:", text)

        reply = mila_reply(text)

        if reply:
            send_message(user, reply)

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return jsonify(ok=True), 200


# =========================
# START CHAT (TEST)
# =========================

@app.route("/start", methods=["GET"])
def start_chat():
    print("### /start CALLED ###")
    send_message(TEST_NUMBER, "hey")
    return "ok", 200


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
