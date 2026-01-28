import os
import requests
from flask import Flask, request, jsonify
from mila import mila_reply

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]

app = Flask(__name__)

def send_message(to, text):
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
    requests.post(url, headers=headers, json=payload)

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == "mila":
        return request.args.get("hub.challenge"), 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user = msg["from"]
        text = msg["text"]["body"]

        reply = mila_reply(text)
        if reply:
            send_message(user, reply)
    except Exception as e:
        print("Webhook error:", e)

    return jsonify(ok=True), 200

@app.route("/start", methods=["GET"])
def start_chat():
    test_number = "393391236716"  # es: 393391236716
    send_message(test_number, "hey")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





