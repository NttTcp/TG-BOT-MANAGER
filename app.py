# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pyrogram import Client
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = "MOD-X_BOT_MANAGER_Secrate_Key2026"

# Database setup
def init_db():
    conn = sqlite3.connect('bot_panel.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, 
                  first_seen TIMESTAMP, is_admin BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS commands 
                 (command TEXT PRIMARY KEY, response TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Bot instance (initialize with your token)
bot_token = None
bot_client = None

def get_bot():
    global bot_client
    if bot_token and (not bot_client or not bot_client.is_connected):
        bot_client = Client("bot_session", api_id=os.getenv('API_ID'), 
                           api_hash=os.getenv('API_HASH'), bot_token=bot_token)
    return bot_client

# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/set_token', methods=['POST'])
def set_token():
    global bot_token
    bot_token = request.json.get('token')
    # Save to database
    conn = sqlite3.connect('bot_panel.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", ('bot_token', bot_token))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Token saved successfully"})

@app.route('/api/bot_info')
def bot_info():
    if not bot_token:
        return jsonify({"error": "No token set"})
    
    try:
        bot = get_bot()
        info = bot.get_me()
        return jsonify({
            "id": info.id,
            "username": info.username,
            "first_name": info.first_name,
            "can_join_groups": info.can_join_groups,
            "can_read_all_group_messages": info.can_read_all_group_messages
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/update_name', methods=['POST'])
def update_name():
    new_name = request.json.get('name')
    try:
        bot = get_bot()
        bot.set_bot_name(new_name)
        return jsonify({"success": True, "message": f"Bot name changed to {new_name}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/update_description', methods=['POST'])
def update_description():
    description = request.json.get('description')
    try:
        bot = get_bot()
        bot.set_bot_description(description)
        return jsonify({"success": True, "message": "Description updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/update_short_description', methods=['POST'])
def update_short_description():
    short_desc = request.json.get('short_description')
    try:
        bot = get_bot()
        bot.set_bot_short_description(short_desc)
        return jsonify({"success": True, "message": "Short description updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/update_commands', methods=['POST'])
def update_commands():
    commands = request.json.get('commands')  # List of {"command": "start", "description": "..."
    try:
        bot = get_bot()
        bot.set_bot_commands(commands)
        
        # Save to local DB
        conn = sqlite3.connect('bot_panel.db')
        c = conn.cursor()
        for cmd in commands:
            c.execute("INSERT OR REPLACE INTO commands VALUES (?, ?)", 
                     (cmd['command'], cmd.get('response', '')))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"{len(commands)} commands updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/update_avatar', methods=['POST'])
def update_avatar():
    if 'photo' not in request.files:
        return jsonify({"error": "No photo uploaded"})
    
    photo = request.files['photo']
    photo_path = f"temp_{photo.filename}"
    photo.save(photo_path)
    
    try:
        bot = get_bot()
        bot.set_bot_profile_photo(photo=photo_path)
        os.remove(photo_path)
        return jsonify({"success": True, "message": "Profile photo updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/send_broadcast', methods=['POST'])
def send_broadcast():
    message = request.json.get('message')
    try:
        conn = sqlite3.connect('bot_panel.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        conn.close()
        
        bot = get_bot()
        sent_count = 0
        for user in users:
            try:
                bot.send_message(user[0], message)
                sent_count += 1
            except:
                pass
        
        return jsonify({"success": True, "sent": sent_count, "total": len(users)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get_stats')
def get_stats():
    conn = sqlite3.connect('bot_panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        "total_users": total_users,
        "bot_status": "active" if bot_token else "inactive"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)