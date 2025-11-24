from flask import Flask, render_template, request, jsonify
from threading import Thread, Event
import time
import requests

app = Flask(__name__)

active_tasks = {}
stop_flags = {}

# --------------------------------------------------------
# FB LOGIN FUNCTION (username + password + 2FA)
# --------------------------------------------------------
def fb_login(username, password, otp):
    session = requests.Session()

    # Step 1: Login request (Facebook Android API style)
    login_url = "https://b-graph.facebook.com/auth/login"

    payload = {
        "email": username,
        "password": password,
        "two_factor_code": otp,
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
        "credentials_type": "password",
        "format": "json"
    }

    r = session.post(login_url, data=payload)

    if "session_key" in r.text:
        print("LOGIN SUCCESS")
        return session
    else:
        print("LOGIN FAILED:", r.text)
        return None


# --------------------------------------------------------
# SENDING MESSAGES
# --------------------------------------------------------
def send_messages_fb(session, target_ids, message, delay, task_id):

    for uid in target_ids:
        if stop_flags[task_id].is_set():
            print("STOP PRESSED — exiting thread")
            break

        send_url = f"https://graph.facebook.com/{uid}/messages"

        data = {
            "message": message
        }

        headers = {
            "User-Agent": "FB4A"
        }

        try:
            r = session.post(send_url, data=data, headers=headers)
            print("Sent:", uid, r.text)
        except:
            print("Error sending to:", uid)

        time.sleep(delay)


# --------------------------------------------------------
# ROUTES
# --------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    username = request.form.get("username")
    password = request.form.get("password")
    otp = request.form.get("otp")
    message = request.form.get("message")
    delay = float(request.form.get("delay"))
    numbers = request.form.get("numbers")

    target_ids = numbers.split("\n")

    # FB LOGIN
    session = fb_login(username, password, otp)
    if session is None:
        return jsonify({"status": "fail", "msg": "Login Failed"})

    task_id = str(time.time())
    stop_flags[task_id] = Event()

    t = Thread(target=send_messages_fb, args=(session, target_ids, message, delay, task_id))
    t.start()

    active_tasks[task_id] = t

    return jsonify({"status": "ok", "task_id": task_id})


@app.route("/stop", methods=["POST"])
def stop():
    task_id = request.form.get("task_id")

    if task_id in stop_flags:
        stop_flags[task_id].set()
        return jsonify({"status": "ok"})

    return jsonify({"status": "fail"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
