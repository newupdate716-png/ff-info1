from flask import Flask, request, jsonify
import requests
from user_agent import generate_user_agent
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import re

app = Flask(__name__)

def clean_label(label):
    return re.sub(r'[^\x00-\x7F]+', '', label).strip()

def clean_value(label, value):
    if "Likes" in label:
        value = value.split("–")[0].strip()
    return value

def freefire(uid):
    player_info = {}

    url = f'https://freefirejornal.com/en/perfil-jogador-freefire/{uid}/'
    headers = {
        "user-agent": generate_user_agent()
    }

    try:
        req = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if req.status_code != 200:
        return {
            "status": "error",
            "message": "Failed to fetch data",
            "code": req.status_code
        }

    soup = BeautifulSoup(req.text, 'html.parser')
    div_tag = soup.find("div", class_="jg-player-infos")

    if not div_tag:
        return {
            "status": "error",
            "message": "Invalid UID or data not found"
        }

    items = div_tag.find_all("li")

    player_info["status"] = "success"

    for li in items:
        strong = li.find("strong")
        if strong:
            raw_label = strong.get_text(strip=True).replace(":", "")
            label = clean_label(raw_label)

            full_text = li.get_text(strip=True)
            value = full_text.replace(strong.get_text(strip=True), "").strip()

            if value:
                try:
                    value = GoogleTranslator(source='auto', target='en').translate(value)
                except:
                    pass

            value = clean_value(label, value)
            player_info[label] = value

    return player_info


@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "API is running",
        "usage": "/info?uid=your_uid"
    })


@app.route('/info', methods=['GET'])
def get_info():
    uid = request.args.get('uid')

    if not uid:
        return jsonify({
            "status": "error",
            "message": "UID is required"
        }), 400

    data = freefire(uid)
    return jsonify(data)


app = app