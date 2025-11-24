from flask import Flask, render_template, request
from threading import Thread, Event
import time
import requests

app = Flask(__name__)

active_tasks = {}
stop_flags = {}

# ----------------------------------------
# FACEBOOK LOGIN
# ----------------------------------------
def fb_login(username, password, otp):
    session = requests.Session()

    url = "https://b-graph.facebook.com/auth/login"

    payload = {
        "email": username,
        "password": password,
        "two_factor_code": otp,
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
        "credentials_type": "password",
        "format": "json"
    }

    r = session.post(url, data=payload).json()

    if "session_key" in str(r):
        print("LOGIN SUCCESS")
        return session
    else:
        print("LOGIN FAILED:", r)
        return None


# ----------------------------------------
# SEND MESSAGE FUNCTION (WORKING)
# ----------------------------------------
def send_messages_fb(session, threadId, messages, delay, prefix, task_id):

    send_url = "https://b-graph.facebook.com/messaging/send/"

    for msg in messages:

        if stop_flags[task_id].is_set():
            print("STOP PRESSED — EXITING THREAD")
            break

        final_msg = f"{prefix} {msg}"

        payload = {
            "recipient": {
                "thread_key": {
                    "thread_fbid": threadId
                }
            },
            "message": {
                "text": final_msg
            }
        }

        headers = {
            "User-Agent": "FB4A",
            "Content-Type": "application/json",
            "fb_api_req_friendly_name": "MessengerComposerSendMessageMutation"
        }

        try:
            r = session.post(send_url, json=payload, headers=headers)
            print("Sent:", final_msg, r.text)
        except Exception as e:
            print("Error sending:", final_msg, e)

        time.sleep(delay)


# ----------------------------------------
# HOME PAGE
# ----------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ----------------------------------------
# START
# ----------------------------------------
@app.route("/start", methods=["POST"])
def start():

    username = request.form.get("username")
    password = request.form.get("password")
    otp = request.form.get("otp")
    threadId = request.form.get("threadId")
    prefix = request.form.get("kidx")
    delay = float(request.form.get("time"))

    txt_file = request.files["txtFile"]
    txt_file.save("messages.txt")

    messages = [i.strip() for i in open("messages.txt", "r", encoding="utf-8").readlines() if i.strip()]

    session = fb_login(username, password, otp)
    if session is None:
        return "LOGIN FAILED"

    task_id = str(time.time())
    stop_flags[task_id] = Event()

    t = Thread(target=send_messages_fb, args=(session, threadId, messages, delay, prefix, task_id))
    t.start()

    active_tasks[task_id] = t

    return f"Task Started Successfully.<br>Task ID: <b>{task_id}</b>"


# ----------------------------------------
# STOP
# ----------------------------------------
@app.route("/stop", methods=["POST"])
def stop():
    task_id = request.form.get("taskId")

    if task_id in stop_flags:
        stop_flags[task_id].set()
        return "Stopped Successfully"

    return "Invalid Task ID"


# ----------------------------------------
# RUN APP
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
