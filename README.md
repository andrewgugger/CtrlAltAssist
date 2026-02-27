# 🤖 CtrlAltAssist: A repo for using local LLMs to automate tasks.

TARS is a multi-functional AI agent inspired by OpenClaw. Powered by **Python**, **Ollama (Gemma 3)** and **Telegram**, it manages your reminders, cleans your Gmail inbox, handles remote torrenting via SSH, and analyzes local files.

---

## ✨ Features

* **🧠 Local Intelligence:** Uses Ollama (Gemma 3) for private, local LLM processing—no data leaves your machine except for the API calls you define.
* **📧 Gmail Sorter:** Automatically categorizes unread emails into labels `ec_save`, `ec_delete`, or `ec_not_sure` using AI logic.
* **⏰ Smart Reminders:** Set reminders using a command and ask about them using natural language. (e.g., `/remind 10m check the oven` and `What are my reminders for today?`).
* **📂 File Analysis:** Give your agent a file from your `analysis/` folder to have it "read" and discuss its contents.
* **📡 Remote Torrenting:** Securely sends magnet links to a remote server via SSH.
* **🔒 Secure:** Hard-coded access control ensures your AI agent only speaks to you.

---

## 🚀 Getting Started

### 1. Installation
```bash
# Clone the repo
git clone https://github.com/andrewgugger/CtrlAltAssist.git
cd CtrlAltAssist

# Install dependencies
pip install -r requirements.txt
```

### 2. Prerequisites
* **Python 3.10+**
* **Ollama** installed and running (with `gemma3:4b` pulled)
* **Telegram Bot Token** (Get one from [@BotFather](https://t.me/botfather))
* **Enable Gmail API**:
  * Go to the Google Cloud Console. 
  * Create a new project. 
  * Search for "Gmail API" and enable it. 
  * Go to Credentials -> Create Credentials -> OAuth client ID. 
  * Select Desktop app. 
  * Download the JSON file, rename it to credentials.json, and place it in your project folder.
* **The below steps are only required to enable torrenting**:
  * Configure qBittorrent CLI on remote server.
  * Create a user with restricted access that is only able to execute the python script, add these lines to the sudoers file:
  ```bash
  username ALL=(ALL) !ALL
  username ALL=(root) NOPASSWD: /usr/bin/python3 /path/to/torrent.py *
  ```


### 3. Configuration
* Add your telegram token from the [@BotFather](https://t.me/botfather) and user ID to the .env file.
* **The below configuration steps are optional. They are only required to enable the torrent functionality.**
  * Add your ssh target (username and server IP or hostname) and the path where your torrent.py file will be kept to the .env file.
  * Add your qBittorrent username and password to the .env file.
  * Place the torrent.py script and a copy of .env file on a remote server where you will torrent.
  * Currently, the script begins seeding after torrenting, maintaining a ratio limit of 1.5. This can be adjusted in the variables
  `ratio_limit` and `seeding_time_limit`.

### 4. Commands
* `/help` Displays a list of all the available commands.
* `/reset` This will wipe the chat history.
* `/read filename.txt `It will look for a file matching filename.txt in the
analysis directory and feed it to the local LLM so you can ask it questions about the file's contents.
* `/clean_emails 100` This will sort through 100 unread emails and decide if it should be 
deleted, saved, or kept. **IT WILL NOT DELETE EMAILS**, it will place them in labels `ec_save`, `ec_not_sure`, or `ec_delete`
for you to review. Enter any number of emails you would like it to sort through.
* `/remind 10m buy milk` Set a reminder, use m for minutes, h for hours, and d for days.
You will receive a telegram message of your reminder. You can also ask the LLM what reminders you have set using natural language.
* `/clear_reminders` Clears all reminders you had set.
* `/exit` Stops the bot and python script.

---

## 🚀 Project Roadmap

| Feature                       | Status                                                                | Description                                                      |
|:------------------------------|:----------------------------------------------------------------------|:-----------------------------------------------------------------|
| **Change Model**              | ![Planned](https://img.shields.io/badge/Status-Planned-lightgrey)     | Allows the user to switch the local LLM they are using from the chat. |
| **Natural Language Reminder** | ![In Progress](https://img.shields.io/badge/Status-Planned-lightgrey) | Enable users to set reminders using natural language.            |
| **Start-up Script**           | ![In Progress](https://img.shields.io/badge/Status-Planned-lightgrey) | Run a startup script to help users with installation.            |

---
## ⚠️ Disclaimer

This project is provided "as is" for educational and personal use. By using this software, you acknowledge that:
* **Email Modification:** The Gmail sorter has the permission to modify and label emails. Use with caution to avoid misclassification of important correspondence.
* **Security:** This script executes shell commands via SSH. It is the user's responsibility to ensure their SSH environment and network are secure.
* **Liability:** The author is not responsible for any data loss, server downtime, or security breaches resulting from the use or misuse of this script.

**Use at your own risk.**


