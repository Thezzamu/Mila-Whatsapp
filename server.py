print("### SERVER.PY LOADED ###")
import os
import requests
from flask import Flask, request, jsonify
from mila import mila_reply

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]

app = Flask(__name__)

def send_message(to, text):
    print("### SEND_MESSAGE CALLED ###")
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


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("INCOMING:", data)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        # ⚠️ ignora eventi che non sono messaggi
        if "messages" not in value:
            print("No messages event, ignoring")
            return jsonify(ok=True), 200

        msg = value["messages"][0]
        user = msg["from"]
        text = msg.get("text", {}).get("body")

        print("TEXT:", text)

        if not text:
            print("No text body")
            return jsonify(ok=True), 200

        reply = mila_reply(text)
        print("REPLY:", reply)

        if reply:
            send_message(user, reply)

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return jsonify(ok=True), 200

@app.route("/start", methods=["GET"])
def start_chat():
    test_number = "393391236716"  # es: 393391236716
    send_message(test_number, "hey")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)








