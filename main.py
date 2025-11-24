from flask import Flask, render_template, request
from threading import Thread, Event
import time
import requests
import os

app = Flask(__name__)

active_tasks = {}
stop_flags = {}

# --------------------------------------------------------
# FACEBOOK ANDROID LOGIN (100% Working)
# --------------------------------------------------------
def fb_login(username, password, otp):
    session = requests.Session()

    login_url = "https://b-api.facebook.com/method/auth.login"

    payload = {
        "email": username,
        "password": password,
        "twofactor_code": otp,
        "generate_session_cookies": "1",
        "credentials_type": "password",
        "format": "json",
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
        "method": "auth.login",
        "locale": "en_US",
        "sdk_version": "2",
        "generate_machine_id": "1"
    }

    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; FB4A Build/QP1A.190711.020)"
    }

    r = session.post(login_url, data=payload, headers=headers)

    if "access_token" in r.text or "session_key" in r.text:
        print("LOGIN SUCCESS")
        return session
    else:
        print("LOGIN FAILED:", r.text)
        return None


# --------------------------------------------------------
# SEND MESSAGES FUNCTION
# --------------------------------------------------------
def send_messages_fb(session, threadId, messages, delay, prefix, task_id):

    for msg in messages:

        if stop_flags[task_id].is_set():
            print("STOP PRESSED — EXITING THREAD")
            break

        final_msg = f"{prefix} {msg}"

        send_url = f"https://graph.facebook.com/v17.0/t_{threadId}/messages"

        data = {
            "message": final_msg,
        }

        headers = {
            "User-Agent": "FB4A"
        }

        try:
            r = session.post(send_url, data=data, headers=headers)
            print("Sent:", final_msg, r.text)
        except:
            print("Error sending:", final_msg)

        time.sleep(delay)


# --------------------------------------------------------
# HOME PAGE
# --------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------------
# START SENDING
# --------------------------------------------------------
@app.route("/start", methods=["POST"])
def start():

    username = request.form.get("username")
    password = request.form.get("password")
    otp = request.form.get("otp")
    threadId = request.form.get("threadId")
    prefix = request.form.get("kidx")
    delay = float(request.form.get("time"))

    txt_file = request.files["txtFile"]

    filepath = "messages.txt"
    txt_file.save(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        messages = [line.strip() for line in f if line.strip()]

    session = fb_login(username, password, otp)
    if session is None:
        return "LOGIN FAILED"

    task_id = str(int(time.time()))
    stop_flags[task_id] = Event()

    t = Thread(target=send_messages_fb, args=(session, threadId, messages, delay, prefix, task_id))
    t.start()

    active_tasks[task_id] = t

    return f"Task Started Successfully.<br>Task ID: <b>{task_id}</b>"


# --------------------------------------------------------
# STOP TASK
# --------------------------------------------------------
@app.route("/stop", methods=["POST"])
def stop():
    task_id = request.form.get("taskId")

    if task_id in stop_flags:
        stop_flags[task_id].set()
        return "Stopped Successfully"

    return "Invalid Task ID"


# --------------------------------------------------------
# RUN APP
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
