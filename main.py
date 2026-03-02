import telebot
import ollama
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re
import json
import os
import uuid
import subprocess
import shlex
from pathlib import Path
import sys
from dotenv import load_dotenv

# telergram bot token and telegram user id from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))
your_name = os.getenv("YOUR_NAME")
bot_name = os.getenv("BOT_NAME")
model = os.getenv("MODEL_NAME")

bot = telebot.TeleBot(TOKEN)
# json file storing all reminders
REMINDERS_FILE = "reminders.json"
# path that the LLM has access to in order to read files (analysis dir).
BASE_DIR = Path(os.getcwd()).joinpath("analysis").resolve()

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# This list will store the conversation history
# We start it with a 'system' message to define bot's personality
chat_history = [
    {
        'role': 'system',
        'content': f"""
            Your name is {bot_name}, you are {your_name}'s virtual assistant. 
            {your_name} knows who you are. 
            Try to answer all questions directly in no more than 4-5 sentences.
            If I ask about my reminders, list them in bullet points.
        """
    }
]


def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    return []


def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=4)


def check_user(message):
    # Check to make sure that only the person with the right user ID can speak with TARS.
    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, f"Access denied. I only talk to {your_name}. ✋")
        return False
    else:
        return True


def send_long_message(chat_id, text):
    # Telegram has limits on how long a message can be.
    # This function split up replies and send them as multiple messages.
    for i in range(0, len(text), 4000):
        bot.send_message(chat_id, text[i:i + 4000])


def get_installed_models():
    try:
        models_data = ollama.list()
        # In the latest library, 'models' is an attribute, and each model has a '.model' property
        return [m.model for m in models_data.models]
    except Exception as e:
        # If the above fails, try the dictionary method as a fallback
        try:
            return [m['name'] for m in ollama.list()['models']]
        except:
            print(f"Error fetching models: {e}")
            return []


@bot.message_handler(commands=['id'])
def get_my_id(message):
    # This is to get userID for intial setup
    bot.reply_to(message, f"Your User ID is: {message.from_user.id}")


@bot.message_handler(commands=['model'])
def change_model(message):
    # command to remove the LLM's chat history.
    if not check_user(message):
        return
    global model
    installed_models = get_installed_models()
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        # No model name provided: List available ones
        models_list = "\n".join([f"• <code>{m}</code>" for m in installed_models])
        response = (
            f"Current Model: <b>{model}</b>\n"
            f"<b>Available Models:</b>\n{models_list}\n\n"
            "To change to a different model, type:\n<code>/model [model-name]</code>\n"
            "Example:\n"
            "/model gemma3:4b\n"
        )
        bot.reply_to(message, response, parse_mode='HTML')
        return

    new_model = parts[1].strip()
    # Check if the requested model actually exists
    if new_model in installed_models:
        model = new_model
        bot.reply_to(message, f"✅ Model switched to: <code>{model}</code>", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ Error: <code>{new_model}</code> is not installed.\n"
                              f"Use /model to see the list of available models.", parse_mode='HTML')


@bot.message_handler(commands=['reset'])
def reset_history(message):
    # command to remove the LLM's chat history.
    if not check_user(message):
        return
    global chat_history
    chat_history = [chat_history[0]]  # Keep only the system prompt
    bot.reply_to(message, "Memory wiped! I'm ready for a fresh start.")


@bot.message_handler(commands=['read'])
def read(message):
    if not check_user(message):
        return
    # Splits '/read filename' and takes everything after the space
    filename = message.text.split(maxsplit=1)[1]

    path = (BASE_DIR / filename).resolve()

    # SECURITY CHECK: Is the resulting path still inside the analysis folder?
    if not path.is_relative_to(BASE_DIR):
        bot.reply_to(message, f"🛑Access Denied: Attempted to escape the analysis directory.")
        return

    try:
        if not os.path.exists(path):
            bot.reply_to(message, f"❌ File not found at: {path}")
            return
        with open(path, "r") as file:
            content = file.read()
        # Update the global chat history with the file content as a System instruction
        global chat_history
        filename = os.path.basename(path)
        chat_history.append({
            'role': 'system',
            'content': f"Here is the content of that file:\n\n{content}\n\n"
                       "Please use this information to answer any specific questions about the file."
        })
        bot.reply_to(message, f"📖 **{filename}** has been loaded into my memory. What would you like to know about it?")
    except Exception as e:
        bot.reply_to(message, f"❌ Error reading file: {e}")


@bot.message_handler(commands=['torrent'])
def handle_torrent(message):
    if not check_user(message):
        return

    # 2. Extract the magnet link
    try:
        # Splits '/torrent <link>' and takes everything after the space
        magnet_link = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Please provide a magnet link.\nUsage: `/torrent magnet:?xt=...`",
                     parse_mode='Markdown')
        return

    bot.reply_to(message, "📡 Sending request to Server...")

    # We wrap the magnet link in shlex.quote to handle special characters safely
    safe_magnet = shlex.quote(magnet_link)
    torrent_path = os.getenv("TORRENT_PATH")
    remote_command = f"nohup sudo /usr/bin/python3 {torrent_path} {safe_magnet} > /dev/null 2>&1 &"

    # 4. Execute via SSH
    # *****************
    # This assumes your client is already set up to SSH into server without a password prompt
    # *****************
    ssh_target = os.getenv("SSH_TARGET")

    try:
        # Run the command and capture output
        result = subprocess.run(
            ["ssh", ssh_target, remote_command],
            capture_output=True,
            text=True,
            timeout=15  # Adjust timeout if server is slow to respond
        )

        if result.returncode == 0:
            bot.send_message(message.chat.id, f"✅ **Server received the request:**\n\n{result.stdout}",
                             parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **Server Error:**\n{result.stderr}")

    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, "⏳ Error: SSH connection to server timed out.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ System Error: {str(e)}")


# --- Helper function to send the reminder ---
def send_reminder_callback(chat_id, task_text, reminder_id):
    bot.send_message(chat_id, f"⏰ **REMINDER:** {task_text}")
    # 2. Remove from JSON
    reminders = load_reminders()
    # Keep only the reminders that DON'T match this ID
    updated_reminders = [r for r in reminders if r.get('id') != reminder_id]
    save_reminders(updated_reminders)


@bot.message_handler(commands=['clear_reminders'])
def clear_reminders(message):
    if not check_user(message):
        return
    # clears scheduled reminders
    scheduler.remove_all_jobs()
    # saves an empty list for reminders
    save_reminders([])
    bot.reply_to(message, "Done! Your reminder list has been wiped clean. 🧹")


@bot.message_handler(commands=['exit'])
def exit(message):
    # stops entire python script
    if not check_user(message):
        return
    bot.reply_to(message, "🔌 Shutting down...")
    # 1. Stop the scheduler
    scheduler.shutdown()
    # 2. Stop the bot's polling loop
    bot.stop_polling()
    sys.exit(0)  # This stops the entire Python process


@bot.message_handler(commands=['clean_emails'])
def run_email_sorter(message):
    if not check_user(message):
        return
    # 2. Extract the number (e.g., "/clean_emails 20" becomes "20")
    try:
        # We split the message: ['/clean_emails', '20'] and take the second item
        num_emails = message.text.split()[1]
    except IndexError:
        # If you just type /clean_emails without a number
        bot.reply_to(message, "Please provide a number: `/clean_emails 20`", parse_mode='Markdown')
        return

    bot.reply_to(message, f"🧹 Cleaning {num_emails} emails...")
    # 3. Run the script (this runs 'python email_sorter.py 20' in the background)
    subprocess.Popen(['python', 'email_sorter.py', num_emails])
    bot.send_message(message.chat.id, "✅ Script started! I'll keep chatting while it runs.")


@bot.message_handler(commands=['remind'])
def set_reminder(message):
    if not check_user(message):
        return
    try:
        match = re.match(r'/remind\s+(\d+)([mhd])\s+(.*)', message.text)
        if not match:
            bot.reply_to(message, "Use: `/remind 10m buy milk`")
            return

        amount, unit, task = int(match.group(1)), match.group(2), match.group(3)

        # Calculate time
        delta = {'m': 'minutes', 'h': 'hours', 'd': 'days'}[unit]
        run_time = datetime.now() + timedelta(**{delta: amount})
        reminder_id = str(uuid.uuid4())  # Generate a unique ID
        # SAVE TO JSON
        reminders = load_reminders()
        reminders.append({
            "id": reminder_id,
            "chat_id": message.chat.id,
            "task": task,
            "due_time": run_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_reminders(reminders)
        # Schedule the live timer
        scheduler.add_job(send_reminder_callback, 'date', run_date=run_time, args=[message.chat.id, task, reminder_id])
        bot.reply_to(message, f"✅ Saved! Reminder set for {run_time.strftime('%H:%M')}.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


@bot.message_handler(commands=['help', 'start'])
def send_help(message):
    if not check_user(message):
        return
    help_text = (
        f"👋 <b>Hi! I'm {bot_name}, your AI Assistant.</b>\n\n"
        "<b>Commands:</b>\n"
        "/reset ➡️ Wipe chat history\n\n"

        "/read file.txt ➡️ Read a file in the analysis directory.\n\n"

        "<b>How to torrent:</b>\n"
        "/torrent {magnet link} ➡️ provide the magnet link for the file you would like to torrent.\n\n"

        "<b>How to clean emails:</b>\n"
        "/clean_emails 10 ➡️ this will sort through 10 emails, enter as many as you'd like.\n\n"

        "<b>How to set a reminder:</b>\n"
        "/remind 10m buy milk ➡️ Use m for minutes, h for hours, and d for days.\n"
        "/clear_reminders ➡️ Clear the JSON file\n\n"

        "<b>How to change the current model:</b>\n"
        f"Current Model: <b>{model}</b>\n"
        "/model ➡️ see all the models available.\n"
        "/model [name-name] ➡️ To change to a different model\n\n"

        "/exit ➡️ Stop the bot and end the python script.\n\n"

        "Or simply type a message to chat with me!"
    )
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global chat_history

    if not check_user(message):
        return

    # 1. Prepare dynamic context (Time and Reminders)
    reminders = load_reminders()
    current_time = datetime.now().strftime("%A, %B %d, %Y %H:%M")
    reminder_context = f"Current Time: {current_time}\n"

    if reminders:
        reminder_context += "Active Reminders (list each one in bullet points if asked):\n" + "\n".join(
            [f"- {r['task']} at {r['due_time']}" for r in reminders])
    else:
        reminder_context += "No active reminders."

    # 2. Add the User's question to history
    # We wrap the user question with the current time/reminder context so TARS is always up to date
    prompt_with_context = f"--- SYSTEM CONTEXT ---\n{reminder_context}\n----------------------\n{message.text}"
    chat_history.append({'role': 'user', 'content': prompt_with_context})

    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # 3. Call Ollama with the full history (which now includes the file if /read was used)
        response = ollama.chat(
            model=model,
            messages=chat_history,
        )

        ai_reply = response['message']['content']

        # 4. Add TARS's reply to history
        chat_history.append({'role': 'assistant', 'content': ai_reply})

        # 5. Prevent history from bloating (Keep system prompt + last 12 messages)
        if len(chat_history) > 15:
            chat_history = [chat_history[0]] + chat_history[-14:]

        send_long_message(message.chat.id, ai_reply)

    except Exception as e:
        bot.reply_to(message, f"⚠️ LLM Error: {str(e)}")


print(f"{bot_name} is online...")
# Re-schedule missed/future reminders on startup
for r in load_reminders():
    due = datetime.strptime(r['due_time'], "%Y-%m-%d %H:%M:%S")
    if due > datetime.now():
        scheduler.add_job(send_reminder_callback, 'date', run_date=due, args=[r['chat_id'], r['task'], r.get('id')])

print(f"{bot_name} is ready and reminders are loaded!")
# bot.infinity_polling()
bot.infinity_polling(timeout=10, long_polling_timeout=20)
# timeout is when asking telegram for new messages, it will wait 10 seconds for a response from the server before trying again.
# long_polling_timeout, without it the bot asks for new messages 100 times a second, however this will have telegram hold our request for x seconds.
# If something comes in those x seconds it sends immediately, if not it will send an empty response after 5 seconds.