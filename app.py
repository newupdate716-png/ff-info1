from flask import Flask, request, jsonify
import requests
from user_agent import generate_user_agent
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

def clean_label(label):
    # শুধু কোলন এবং অপ্রয়োজনীয় স্পেস রিমুভ করবে, যাতে কি-ওয়ার্ড নষ্ট না হয়
    label = label.replace(":", "").strip()
    # স্পেসকে আন্ডারস্কোর করবে যাতে JSON কি (key) হিসেবে সুন্দর দেখায়
    return re.sub(r'\s+', '_', label)

def clean_value(label, value):
    if "Likes" in label or "Curtidas" in label:
        value = value.split("–")[0].strip()
    return value

def freefire(uid):
    player_info = {}
    url = f'https://freefirejornal.com/en/perfil-jogador-freefire/{uid}/'
    
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        # টাইমআউট কিছুটা বাড়ানো হয়েছে যাতে বড় রিকোয়েস্টে এরর না আসে
        req = requests.get(url, headers=headers, timeout=15)
        req.raise_for_status() 
    except Exception as e:
        return {"status": "error", "message": f"Connection Error: {str(e)}"}

    if req.status_code != 200:
        return {
            "status": "error",
            "message": "Failed to fetch data from server",
            "code": req.status_code
        }

    soup = BeautifulSoup(req.text, 'html.parser')
    
    # মূল ইনফরমেশন কন্টেইনার খোঁজা
    div_tag = soup.find("div", class_="jg-player-infos")

    if not div_tag:
        return {
            "status": "error",
            "message": "Invalid UID or Player profile not found"
        }

    # সাকসেস হলে ডেটা সংগ্রহ শুরু
    player_info["status"] = "success"
    player_info["uid"] = uid
    
    items = div_tag.find_all("li")

    for li in items:
        strong = li.find("strong")
        if strong:
            # লেবেল তৈরি (যেমন: Nickname, Level, etc.)
            raw_label = strong.get_text(strip=True)
            label_key = clean_label(raw_label)

            # ভ্যালু তৈরি (যেমন: Player Name, 75, etc.)
            # strong ট্যাগ বাদে বাকি টেক্সটটুকু নেওয়া হচ্ছে
            value = li.get_text(strip=True).replace(raw_label, "").strip()

            if value:
                # ভাষা যাই হোক, ইংরেজিতে ট্রান্সলেট করার চেষ্টা করবে
                try:
                    if not value.isdigit(): # শুধু নাম্বার হলে ট্রান্সলেটের দরকার নেই
                        value = GoogleTranslator(source='auto', target='en').translate(value)
                except:
                    pass

            # ভ্যালু ক্লিন করা
            value = clean_value(label_key, value)
            
            # ডাইনামিকালি ডেটা সেভ করা
            if label_key:
                player_info[label_key] = value

    return player_info

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Free Fire Profile API is running perfectly",
        "usage": "/info?uid=12345678"
    })

@app.route('/info', methods=['GET'])
def get_info():
    uid = request.args.get('uid')

    if not uid:
        return jsonify({
            "status": "error",
            "message": "UID parameter is missing"
        }), 400

    # ডেটা ফেচ করা
    result = freefire(uid)
    
    # যদি সাকসেস হয় তবে ২০০ কোড, নাহলে ৪০০ বা ৫০০
    status_code = 200 if result.get("status") == "success" else 404
    return jsonify(result), status_code

if __name__ == '__main__':
    # সার্ভার রান করার কমান্ড
    app.run(debug=True, host='0.0.0.0', port=5000)
