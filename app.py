#!/usr/bin/env python3
"""
Simple Flask web panel. Shows history and allows submitting tasks which call
the same local sandbox CLI. Designed with an Apple-like look + emojis.
"""
import os
import shlex
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = LOG_DIR / "history.json"

SANDBOX_CMD = os.getenv("SANDBOX_CMD", "sandbox")
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "300"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-me-for-prod")

def run_cmd(cmd, timeout=COMMAND_TIMEOUT):
    try:
        proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout"

def ensure_history():
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]")

def append_history(item):
    ensure_history()
    h = json_load()
    h.insert(0, item)
    HISTORY_FILE.write_text(__import__('json').dumps(h, indent=2))

def json_load():
    ensure_history()
    import json
    return json.loads(HISTORY_FILE.read_text())

@app.route("/")
def index():
    history = json_load()
    return render_template("index.html", history=history)

@app.route("/task", methods=["POST"])
def task():
    task_text = request.form.get("task", "").strip()
    if not task_text:
        flash("Please provide a task", "warning")
        return redirect(url_for("index"))
    cmd = f"{SANDBOX_CMD} agent {shlex.quote(task_text)}"
    rc, out, err = run_cmd(cmd)
    item = {
        "task": task_text,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "exit_code": rc,
        "stdout": out,
        "stderr": err
    }
    append_history(item)
    flash("Task submitted. Scroll to History for results.", "success")
    return redirect(url_for("index"))

@app.route("/api/status")
def status():
    rc, out, err = run_cmd(f"{SANDBOX_CMD} health")
    return jsonify({"exit_code": rc, "stdout": out, "stderr": err})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)