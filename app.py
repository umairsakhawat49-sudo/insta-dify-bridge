import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_API_URL = "https://api.dify.ai/v1/chat-messages"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


@app.route("/", methods=["GET"])
def home():
  return "Instagram-Dify Bridge is running successfully!"


@app.route("/webhook", methods=["GET"])
def verify_webhook():
  mode = request.args.get("hub.mode")
  token = request.args.get("hub.verify_token")
  challenge = request.args.get("hub.challenge")

  if mode and token:
    if mode == "subscribe" and token == VERIFY_TOKEN:
      print("WEBHOOK_VERIFIED")
      return challenge, 200
    else:
      return "Verification failed", 403
  return "Hello World", 200


@app.route("/webhook", methods=["POST"])
def webhook():
  data = request.json
  print("Received data:", data)

  try:
    if data.get("object") == "instagram":
      for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
          sender_id = messaging_event.get("sender", {}).get("id")
          message_text = messaging_event.get("message", {}).get("text")

          if sender_id and message_text:
            dify_response = send_to_dify(sender_id, message_text)
            send_instagram_message(sender_id, dify_response)

  except Exception as e:
    print("Error processing webhook:", e)

  return jsonify({"status": "ok"}), 200


def send_to_dify(user_id, query):
  headers = {
      "Authorization": f"Bearer {DIFY_API_KEY}",
      "Content-Type": "application/json",
  }
  payload = {
      "inputs": {},
      "query": query,
      "response_mode": "blocking",
      "user": f"insta_user_{user_id}",
  }

  try:
    response = requests.post(
        DIFY_API_URL, json=payload, headers=headers, timeout=30
    )
    res_data = response.json()
    return res_data.get(
        "answer", "Sorry, an error occurred while processing your request."
    )
  except Exception as e:
    print("Dify API Error:", e)
    return "Sorry, could not connect to the bot."


def send_instagram_message(recipient_id, message_text):
  url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
  payload = {
      "recipient": {"id": recipient_id},
      "message": {"text": message_text},
  }
  headers = {"Content-Type": "application/json"}

  try:
    response = requests.post(url, json=payload, headers=headers)
    print("Instagram Send Response:", response.json())
  except Exception as e:
    print("Instagram API Error:", e)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
