from flask import Flask, request
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# ─── YAHAN APNI VALUES DAALO ──────────────────────────────
ACCESS_TOKEN = "EAAR2lY5NTk4BQ79MqLVk5QPTOT3SKexnwlflfvVIwsv8hh9Kd9ej8s1OyZBZCZANTZBmTWJoE8dDNKVifY55oZBZBEKICo0jkA6Hag5ZCvZBJCRVm662qlbciKxWqH5LGPCAIU5KZCJn1ApWwZAU5lN7c1L1NvBNSIQvb6bfpEk5HihZAkjTd0LLtG8K9Qas4sWD4eZAUXHWYZAecCVeFhU6qAor0RJUrl2gA6DmV9gCUFK1uXZAdTPZBMZAgCCA0AW1ACeM02TFVfwcWPIu40G8RkljKYanqLmi"   # ← Naya token yahan
PHONE_NUMBER_ID = "1041537642382604"             # ← Ye sahi hai
VERIFY_TOKEN = "myexpensebot123"                 # ← Ye mat badlo
# ──────────────────────────────────────────────────────────

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_message(to, text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
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
    print(f"Send status: {r.status_code} | {r.text}")

def process_message(user_number, msg):
    msg = msg.strip().lower()
    data = load_data()

    if user_number not in data:
        data[user_number] = {
            "budget": 0,
            "spent": 0,
            "expenses": [],
            "month": datetime.now().strftime("%m-%Y")
        }

    user = data[user_number]

    # Auto reset if new month
    current_month = datetime.now().strftime("%m-%Y")
    if user.get("month") != current_month:
        user["spent"] = 0
        user["expenses"] = []
        user["month"] = current_month

    reply = ""

    # ── Budget set: "budget 50000" ──
    if msg.startswith("budget "):
        try:
            amount = float(msg.split()[1])
            user["budget"] = amount
            user["spent"] = 0
            user["expenses"] = []
            reply = (f"✅ Budget set ho gaya!\n"
                    f"━━━━━━━━━━━━━\n"
                    f"💰 Total Budget: Rs. {amount:,.0f}\n"
                    f"📊 Bacha hua: Rs. {amount:,.0f}\n\n"
                    f"Ab kharchay likhain:\n"
                    f"*khana 500*\n"
                    f"*petrol 2000*\n"
                    f"*bijli 3000*")
        except:
            reply = "❌ Sahi format: *budget 50000*"

    # ── Expense add: "khana 500" ──
    elif len(msg.split()) == 2 and msg.split()[1].replace('.','').isdigit():
        if user["budget"] == 0:
            reply = "⚠️ Pehle budget set karo!\nExample: *budget 50000*"
        else:
            try:
                category = msg.split()[0].title()
                amount = float(msg.split()[1])
                user["spent"] += amount
                remaining = user["budget"] - user["spent"]
                percent_used = (user["spent"] / user["budget"]) * 100

                user["expenses"].append({
                    "category": category,
                    "amount": amount,
                    "date": datetime.now().strftime("%d-%m %H:%M")
                })

                if remaining > 0:
                    emoji = "✅"
                else:
                    emoji = "🚨"

                reply = (f"{emoji} *{category}*: Rs. {amount:,.0f}\n"
                        f"━━━━━━━━━━━━━\n"
                        f"💸 Total Kharch: Rs. {user['spent']:,.0f}\n"
                        f"💰 Bacha hua: Rs. {remaining:,.0f}\n"
                        f"📈 Used: {percent_used:.1f}%")

                if remaining < 0:
                    reply += f"\n\n🚨 *BUDGET EXCEED HO GAYA!*\nRs. {abs(remaining):,.0f} zyada kharch!"
                elif remaining < user["budget"] * 0.2:
                    reply += f"\n\n⚠️ Sirf 20% budget bacha hai! Sambhal ke kharcho."

            except:
                reply = "❌ Sahi format: *category amount*\nExample: *khana 500*"

    # ── Summary ──
    elif msg in ["summary", "report", "s"]:
        if user["budget"] == 0:
            reply = "⚠️ Pehle budget set karo!\nExample: *budget 50000*"
        else:
            remaining = user["budget"] - user["spent"]
            percent = (user["spent"] / user["budget"]) * 100

            reply = (f"📊 *MONTHLY SUMMARY*\n"
                    f"📅 {datetime.now().strftime('%B %Y')}\n"
                    f"━━━━━━━━━━━━━\n"
                    f"💰 Budget:  Rs. {user['budget']:,.0f}\n"
                    f"💸 Kharch:  Rs. {user['spent']:,.0f}\n"
                    f"✅ Bacha:   Rs. {remaining:,.0f}\n"
                    f"📈 Used:    {percent:.1f}%\n"
                    f"━━━━━━━━━━━━━\n")

            if user["expenses"]:
                cat_totals = {}
                for exp in user["expenses"]:
                    cat = exp["category"]
                    cat_totals[cat] = cat_totals.get(cat, 0) + exp["amount"]

                reply += "*📂 Category Breakdown:*\n"
                for cat, total in sorted(cat_totals.items(), key=lambda x: -x[1]):
                    bar_percent = (total / user["budget"]) * 100
                    reply += f"  • {cat}: Rs. {total:,.0f} ({bar_percent:.1f}%)\n"

    # ── History ──
    elif msg in ["history", "h"]:
        if not user["expenses"]:
            reply = "📭 Koi expense nahi abhi."
        else:
            reply = f"📜 *LAST {min(10, len(user['expenses']))} EXPENSES*\n━━━━━━━━━━━━━\n"
            for exp in user["expenses"][-10:]:
                reply += f"• {exp['date']} | {exp['category']}: Rs. {exp['amount']:,.0f}\n"

    # ── Delete last expense ──
    elif msg in ["undo", "delete"]:
        if not user["expenses"]:
            reply = "❌ Koi expense nahi hai delete karne ke liye."
        else:
            last = user["expenses"].pop()
            user["spent"] -= last["amount"]
            remaining = user["budget"] - user["spent"]
            reply = (f"🗑️ Last expense delete ho gaya!\n"
                    f"━━━━━━━━━━━━━\n"
                    f"❌ Removed: {last['category']} Rs. {last['amount']:,.0f}\n"
                    f"💰 Bacha hua: Rs. {remaining:,.0f}")

    # ── Reset ──
    elif msg == "reset":
        user["budget"] = 0
        user["spent"] = 0
        user["expenses"] = []
        reply = "🔄 Sab kuch reset ho gaya!\nNaya budget set karo: *budget 50000*"

    # ── Help / Start ──
    elif msg in ["help", "hi", "hello", "start", "menu"]:
        reply = ("🤖 *EXPENSE TRACKER BOT*\n"
                "━━━━━━━━━━━━━\n"
                "📌 *Commands:*\n\n"
                "💰 *budget 50000*\n"
                "   → Monthly budget set karo\n\n"
                "🛒 *khana 500*\n"
                "   → Expense add karo\n"
                "   (koi bhi category likho)\n\n"
                "📊 *summary* ya *s*\n"
                "   → Poori monthly summary\n\n"
                "📜 *history* ya *h*\n"
                "   → Last 10 kharchay\n\n"
                "↩️ *undo*\n"
                "   → Last expense delete karo\n\n"
                "🔄 *reset*\n"
                "   → Sab reset karo\n"
                "━━━━━━━━━━━━━\n"
                "💡 *Examples:*\n"
                "petrol 3000\n"
                "bijli 2500\n"
                "mobile 1000\n"
                "shopping 5000")
    else:
        reply = ("❓ Samajh nahi aaya!\n\n"
                "*help* likho commands dekhne ke liye\n\n"
                "Ya seedha expense likho:\n"
                "*khana 500*")

    data[user_number] = user
    save_data(data)
    return reply

# ─── WEBHOOK - Verify ──────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200
    return "Forbidden", 403

# ─── WEBHOOK - Receive Messages ────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"Incoming: {json.dumps(data, indent=2)}")
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg_data = entry["messages"][0]
            if msg_data.get("type") == "text":
                user_number = msg_data["from"]
                msg_text = msg_data["text"]["body"]
                print(f"Message from {user_number}: {msg_text}")
                reply = process_message(user_number, msg_text)
                send_message(user_number, reply)
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)