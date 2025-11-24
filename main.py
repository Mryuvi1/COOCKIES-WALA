from flask import Flask, render_template, request
from threading import Thread, Event
import time
import requests
import os

app = Flask(__name__)

active_tasks = {}
stop_flags = {}

# --------------------------------------------------------
# FACEBOOK LOGIN
# --------------------------------------------------------
def fb_login(username, password, otp):
    session = requests.Session()

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
# SEND MESSAGES FUNCTION
# --------------------------------------------------------
def send_messages_fb(session, threadId, messages, delay, prefix, task_id):

    for msg in messages:

        if stop_flags[task_id].is_set():
            print("STOP PRESSED — EXITING THREAD")
            break

        final_msg = f"{prefix} {msg}"

        send_url = f"https://graph.facebook.com/v17.0/t_{threadId}/"

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
            print("Error sending message:", final_msg)

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

    # SAVE FILE TEMP
    filepath = "messages.txt"
    txt_file.save(filepath)

    # READ FILE LINES
    with open(filepath, "r", encoding="utf-8") as f:
        messages = [line.strip() for line in f.readlines() if line.strip()]

    # LOGIN FB
    session = fb_login(username, password, otp)
    if session is None:
        return "LOGIN FAILED"

    task_id = str(time.time())
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
