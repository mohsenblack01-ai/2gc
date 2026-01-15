from flask import Flask, render_template, request, redirect
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, FeedbackRequired, PleaseWaitFewMinutes, ClientError
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_2id_2gc_2025"

status = {"running": False, "sent": 0, "logs": [], "text": "Ready"}
cfg = {
    "sessionid1": "", "sessionid2": "",
    "thread_id1": "", "thread_id2": "",
    "messages": "", "delay": 12,
    "cycle": 35, "break": 40
}

clients = []
workers = []

DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {msg}")
    if len(status["logs"]) > 600:
        status["logs"] = status["logs"][-600:]

def send_message(client, thread_id, message, id_number):
    for _ in range(3):
        try:
            client.direct_send(message, thread_ids=[thread_id])
            log(f"[ID{id_number}] Sent → {message[:50]}")
            return True
        except (ChallengeRequired, FeedbackRequired):
            log(f"[ID{id_number}] Challenge/Feedback – skipping")
            return False
        except PleaseWaitFewMinutes:
            log(f"[ID{id_number}] Rate limit – waiting 8 min")
            time.sleep(480)
            return False
        except ClientError as e:
            if "pinned" in str(e).lower() or "channels info" in str(e).lower():
                log(f"[ID{id_number}] Pinned channels info error – skipping & continuing")
                return False
            time.sleep(random.uniform(5, 10))
    log(f"[ID{id_number}] Send failed after 3 retries")
    return False

def bomber(cl, tid, msgs, id_number):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            if send_message(cl, tid, msg, id_number):
                local_sent += 1
                status["sent"] += 1

            if local_sent % cfg["cycle"] == 0:
                log(f"[ID{id_number}] Break {cfg['break']}s after {cfg['cycle']} msgs")
                time.sleep(cfg["break"])

            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except Exception as e:
            log(f"[ID{id_number}] Error → {str(e)[:50]}")
            time.sleep(20)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        status["running"] = False
        time.sleep(2)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        cfg["sessionid1"] = request.form.get('sessionid1', '').strip()
        cfg["sessionid2"] = request.form.get('sessionid2', '').strip()
        cfg["thread_id1"] = request.form['thread_id1']
        cfg["thread_id2"] = request.form['thread_id2']
        cfg["messages"] = request.form['messages']
        cfg["delay"] = float(request.form.get('delay', 12))
        cfg["cycle"] = int(request.form.get('cycle', 35))
        cfg["break"] = int(request.form.get('break', 40))

        msgs = [m.strip() for m in cfg["messages"].split('\n') if m.strip()]

        status["running"] = True
        status["text"] = "BOMBING ACTIVE (2 IDs)"
        log("SPAMMER STARTED – 2 IDs / 2 GCs")

        for i in range(1, 3):
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.set_user_agent(f"Instagram {device['app_version']} Android (34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; {device['phone_model']}; raven; raven; en_US)")
            cl.delay_range = [8, 25]

            try:
                cl.login_by_sessionid(cfg[f"sessionid{i}"])
                log(f"ID {i} → Login SUCCESS")
                clients.append(cl)
                tid = cfg[f"thread_id{i}"]
                t = threading.Thread(target=bomber, args=(cl, tid, msgs, i), daemon=True)
                t.start()
                workers.append(t)
            except Exception as e:
                log(f"ID {i} Failed → {str(e)[:90]}")

        if not clients:
            status["text"] = "LOGIN FAILED"
            status["running"] = False

    return render_template('index.html', **status, cfg=cfg)

@app.route('/stop')
def stop():
    status["running"] = False
    log("SPAMMER STOPPED")
    status["text"] = "STOPPED"
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
