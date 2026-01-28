import os
import requests
from flask import Flask, jsonify

print("### SERVER STARTED ###")

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]

app = Flask(__name__)

def send_message(to, text):
    print("### SEND_MESSAGE CALLED ###")
    print("TO:", to)
    print("TEXT:", text)

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

@app.route("/start", methods=["GET"])
def start():
    print("### /START HIT ###")

    test_number = "393391236716"  # SENZA +
    send_message(test_number, "Hey")

    return jsonify(ok=True), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
