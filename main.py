from flask import Flask, render_template, request, jsonify
from threading import Thread, Event
import requests
import time

app = Flask(__name__)

active_tasks = {}
stop_flags = {}

# ----------------------------------------
# FACEBOOK COOKIE LOGIN (NO PASSWORD)
# ----------------------------------------
def fb_session_from_cookie(cookie_string):
    session = requests.Session()

    cookie_pairs = cookie_string.split(";")
    for pair in cookie_pairs:
        try:
            k, v = pair.strip().split("=")
            session.cookies.set(k, v)
        except:
            pass

    # Check login success
    test = session.get("https://www.facebook.com/me")

    if "id" in test.text or "profile" in test.text:
        print("COOKIE LOGIN SUCCESS")
        return session
    
    print("COOKIE LOGIN FAILED")
    return None


# ----------------------------------------
# MESSAGE SENDER THREAD
# ----------------------------------------
def send_messages(session, target_ids, message, delay, task_id):

    for uid in target_ids:

        if stop_flags[task_id].is_set():
            print("STOP PRESSED — EXITING THREAD")
            break

        send_url = f"https://graph.facebook.com/v17.0/t_{uid}/"

        payload = {
            "message": message
        }

        try:
            r = session.post(send_url, data=payload)
            print("Sent to:", uid, r.text)
        except Exception as e:
            print("Error sending:", uid, str(e))

        time.sleep(delay)


# ----------------------------------------
# ROUTES
# ----------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    cookie = request.form.get("cookie")
    message = request.form.get("message")
    delay = float(request.form.get("delay"))
    numbers = request.form.get("numbers")

    target_ids = [x.strip() for x in numbers.split("\n") if x.strip()]

    session = fb_session_from_cookie(cookie)

    if session is None:
        return jsonify({"status": "fail", "msg": "Cookie Login Failed"})

    task_id = str(time.time())
    stop_flags[task_id] = Event()

    t = Thread(target=send_messages, args=(session, target_ids, message, delay, task_id))
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
