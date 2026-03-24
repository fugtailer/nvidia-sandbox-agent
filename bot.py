#!/usr/bin/env python3
"""
Telegram bot that forwards tasks to the sandbox agent (sandbox-cli.py) and
returns nicely formatted, emoji-rich responses.
"""

import os
import json
import shlex
import subprocess
import logging
from pathlib import Path
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / "bot.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SHELL_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "300"))
SANDBOX_CMD = os.getenv("SANDBOX_CMD", "sandbox")  # launcher installed by install.sh

def run_shell(command: str, timeout: int = SHELL_TIMEOUT):
    try:
        proc = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out."

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🍏 Welcome to NVIDIA Sandbox Agent\nSend /help for commands.")

def help_cmd(update: Update, context: CallbackContext):
    text = (
        "🛠️ *Commands*\n"
        "/health - Check system health\n"
        "/exec <command> - Execute a shell command (use carefully)\n"
        "/agent <task> - Let AI generate and run commands for a task\n"
        "\n"
        "🔒 *Security:* Don't send secrets over chat. Admin-only features are not enabled by default."
    )
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def health(update: Update, context: CallbackContext):
    rc, out, err = run_shell(f"{SANDBOX_CMD} health")
    emoji = "✅" if rc == 0 else "⚠️"
    message = f"{emoji} *Health check* (exit {rc})\n\n```\n{out}\n{err}\n```"
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def exec_cmd(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("⚠️ Usage: /exec <command>")
        return
    command = " ".join(context.args)
    update.message.reply_text(f"⏳ Running: `{{command}}`", parse_mode=ParseMode.MARKDOWN)
    logging.info("User %s executed: %s", update.effective_user.username, command)
    rc, out, err = run_shell(command)
    header = "✅ Success" if rc == 0 else "❌ Failed"
    text = f"{{header}} (exit {{rc}})\n\n*stdout*\n```\n{{out}}\n```\n*stderr*\n```\n{{err}}\n```"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def agent_cmd(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("⚠️ Usage: /agent <task description>")
        return
    task = " ".join(context.args)
    update.message.reply_text(f"🤖 Agent received task: *{{task}}*\nGenerating commands...", parse_mode=ParseMode.MARKDOWN)
    rc, out, err = run_shell(f"{{SANDBOX_CMD}} agent {{shlex.quote(task)}}")
    if rc != 0:
        text = f"❌ Agent failed (exit {{rc}})\n```\n{{err}}\n```"
    else:
        text = f"✅ Agent finished (exit {{rc}})\n\n```\n{{out}}\n```"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def echo(update: Update, context: CallbackContext):
    update.message.reply_text("📩 I received your message. Use /help for commands.")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set.")
        return
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("health", health))
    dp.add_handler(CommandHandler("exec", exec_cmd, pass_args=True))
    dp.add_handler(CommandHandler("agent", agent_cmd, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    print("Bot started. Polling for updates...")
    updater.idle()

if __name__ == "__main__":
    main()