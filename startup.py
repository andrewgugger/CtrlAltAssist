import os
import time
import sys
import telebot
import json
from dotenv import load_dotenv

# --- Terminal Styling ---
BLUE = "\033[38;5;33m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

ART = rf"""{BLUE}{BOLD}
   _______________________________________________
  |  ___________________________________________  |
  | |                                           | |
  | |   CtrlAltAssist  I N I T I A L I Z E R    | |
  | |___________________________________________| |
  |_______________________________________________|
{RESET}"""


def loading_bar(duration=1.0, label="INITIALIZING"):
    slots = 20
    for i in range(slots + 1):
        percent = int((i / slots) * 100)
        bar = "█" * i + "-" * (slots - i)
        sys.stdout.write(f"\r{BOLD}{CYAN}{label}: [{bar}] {percent}%{RESET}")
        sys.stdout.flush()
        time.sleep(duration / slots)
    print("")


def discovery_mode(token):
    """Temporary bot listener that captures an ID and returns it to the main script."""
    captured_id = None  # Storage for the ID we find

    try:

        print(f"\n{YELLOW}📡 DISCOVERY MODE INITIALIZING...{RESET}")
        loading_bar(1.5, "CONNECTING TO TELEGRAM")
        print(f"\n{BLUE}Please wait...{RESET}")
        temp_bot = telebot.TeleBot(token)
        temp_bot.get_updates(offset=-1)  # Clear backlog

        print(f"{CYAN}🟢 CONNECTED! Send a message to your bot on Telegram.{RESET}")

        @temp_bot.message_handler(func=lambda message: True)
        def catch_id(message):
            nonlocal captured_id
            captured_id = message.from_user.id
            print(f"\n{GREEN}✅ SIGNAL RECEIVED!{RESET}")
            print(f"{BOLD}User: {CYAN}{message.from_user.first_name}{RESET}")
            print(f"{BOLD}ID Captured: {YELLOW}{captured_id}{RESET}")

            # This triggers the exit
            print(f"\n{BLUE}Closing secure listener...{RESET}")
            loading_bar(1.5, "CLEANING UP")
            print(f"\n{BLUE}Please wait...{RESET}")
            temp_bot.stop_polling()

        # Start listening
        temp_bot.polling(none_stop=False, timeout=5)

    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")



def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ART)

    # Check of .json file exists
    if not os.path.exists("reminders.json"):
        try:
            with open("reminders.json", "w") as j:
                json.dump([], j)
            loading_bar(0.5, "INITIALIZING JSON DB")
        except Exception as e:
            print(f"{RED}Error creating reminders.json: {e}{RESET}")

    #Check if env file exists
    if os.path.exists(".env"):
        load_dotenv()
        name = os.getenv("YOUR_NAME")
        user_id = os.getenv("ALLOWED_USER_ID")
        bot_name = os.getenv("BOT_NAME")
        print(f"{GREEN}Existing configuration found for {BOLD}{name}{RESET}.")
    else:
        print(f"{BLUE}No configuration found. Starting First-Time Setup...{RESET}")
        print(f"{CYAN}(Tip: Type 'get' in the ID field if you don't know it){RESET}\n")

        # --- Required Inputs ---
        print(f"{CYAN}--- CORE SETTINGS ---{RESET}")
        name = input(f"{BOLD}User Name:{RESET} ")
        bot_name = input(f"{BOLD}Bot Name:{RESET} ")
        model_name = input(f"{BOLD}Model (e.g. gemma3:4b):{RESET} ")
        token = input(f"{BOLD}Telegram Token:{RESET} ")

        user_id = input(f"{BOLD}Allowed User ID (or 'get'):{RESET} ")
        if user_id.lower() == 'get':
            discovery_mode(token)
            user_id = input(f"{BOLD}Enter the ID shown above:{RESET} ")

        # --- Optional Inputs ---
        print(f"\n{CYAN}--- SERVER & TORRENT SETTINGS (Optional) ---{RESET}")
        ssh_target = input(f"SSH Target: ")
        torrent_path = input(f"Torrent Script Path: ")
        qbt_user = input(f"QBT Username: ")
        qbt_pass = input(f"QBT Password: ")

        # --- File Writing ---
        try:
            with open(".env", "w") as f:
                f.write(f"YOUR_NAME={name}\n")
                f.write(f"BOT_NAME={bot_name}\n")
                f.write(f"MODEL_NAME={model_name}\n")
                f.write(f"TELEGRAM_TOKEN={token}\n")
                f.write(f"ALLOWED_USER_ID={user_id}\n")

                if ssh_target: f.write(f"SSH_TARGET={ssh_target}\n")
                if torrent_path: f.write(f"TORRENT_PATH={torrent_path}\n")
                if qbt_user: f.write(f"QBT_USER={qbt_user}\n")
                if qbt_pass: f.write(f"QBT_PASS={qbt_pass}\n")

            loading_bar(1.0, "SAVING CONFIGURATIONS")
            print(f"\n{BLUE}Configurations saved for ID-{user_id}.{RESET}")
        except Exception as e:
            print(f"{RED}Failed to write .env file: {e}{RESET}")
            sys.exit(1)

    # --- Visual Flair ---
    loading_bar(0.6, "MOUNTING ANALYSIS DIR")
    loading_bar(0.8, "SYNCING OLLAMA CORE")

    print(f"\n{GREEN}{BOLD}✅ {bot_name} IS CONFIGURED AND AUTHORIZED.{RESET}")
    print(f"{CYAN}Transitioning to main.py...{RESET}\n")
    time.sleep(0.5)

    # Launching main.py
    loading_bar(1.0, "LAUNCHING")
    os.execl(sys.executable, sys.executable, "main.py")


if __name__ == "__main__":
    main()