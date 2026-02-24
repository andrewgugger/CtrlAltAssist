# 🤖 CtrlAltAssist: A repo for using local LLMs to automate tasks.

TARS is a multi-functional Python assistant inspired by OpenClaw. Powered by **Ollama (Gemma 3)** and **Telegram**, it manages your reminders, cleans your Gmail inbox, handles remote torrenting via SSH, and analyzes local files.

---

## ✨ Features

* **🧠 Local Intelligence:** Uses Ollama (Gemma 3) for private, local LLM processing—no data leaves your machine except for the API calls you define.
* **📧 Gmail Sorter:** Automatically categorizes unread emails into labels `ec_save`, `ec_delete`, or `ec_not_sure` using AI logic.
* **⏰ Smart Reminders:** Set reminders in natural language (e.g., `/remind 10m check the oven`).
* **📂 File Analysis:** Give TARS a file from your `analysis/` folder to have him "read" and discuss its contents.
* **📡 Remote Torrenting:** Securely sends magnet links to a remote server via SSH.
* **🔒 Secure:** Hard-coded access control ensures TARS only speaks to you.

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.10+**
* **Ollama** installed and running (with `gemma3:4b` pulled)
* **Telegram Bot Token** (Get one from [@BotFather](https://t.me/botfather))
* **Enable Gmail API** Enable Gmail API:
  * Go to the Google Cloud Console. 
  * Create a new project. 
  * Search for "Gmail API" and enable it. 
  * Go to Credentials -> Create Credentials -> OAuth client ID. 
  * Select Desktop app. 
  * Download the JSON file, rename it to credentials.json, and place it in your project folder.

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/andrewgugger/CtrlAltAssist.git
cd CtrlAltAssist

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
* Add your telegram token from the [@BotFather](https://t.me/botfather) and user ID to the .env file.
* **Optional:** Add your ssh target (username and server IP or hostname) and the path where your torrent.py file will be kept.


### 4. Commands
* `/help` Displays a list of all the available commands.
* `/reset` This will wipe the chat history.
* `/read filename.txt `It will look for a file matching filename.txt in the
analysis directory and feed it to the local LLM so you can ask it questions.
* `/clean_emails 100` This will sort through 100 unread emails and decide if it should be 
deleted, saved, or kept. **IT WILL NOT DELETE EMAILS**, it will place them in labels `ec_save`, `ec_not_sure`, or `ec_delete`
for you to review. Enter any number of emails you would like it to sort through.
* `/remind 10m buy milk` Set a reminder, use m for minutes, h for hours, and d for days.
You will receive a telegram message of your reminder. You can also ask the LLM what reminders you have set.
* `/clear_reminders` Clears all reminders you had set.
* `/exit` Stops the bot and python script.

---

## ⚠️ Disclaimer

This project is provided "as is" for educational and personal use. By using this software, you acknowledge that:
* **Email Modification:** The Gmail sorter has the permission to modify and label emails. Use with caution to avoid misclassification of important correspondence.
* **Security:** This script executes shell commands via SSH. It is the user's responsibility to ensure their SSH environment and network are secure.
* **Liability:** The author is not responsible for any data loss, server downtime, or security breaches resulting from the use or misuse of this script.

**Use at your own risk.**