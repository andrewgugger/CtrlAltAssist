import subprocess
import time
import qbittorrentapi
import sys
import requests
import os
from dotenv import load_dotenv

# telergram bot token and telegram user id from .env file
load_dotenv()

# --- SETTINGS ---
QBT_USER = os.getenv("QBT_USER")
QBT_PASS = os.getenv("QBT_PASS")

def main():

    #function to send updates
    def send_telegram_update(text):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = int(os.getenv("ALLOWED_USER_ID"))
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url)


    # Check if a magnet link was provided.
    # comment out the below to manually add magnet above
    if len(sys.argv) < 2:
        error = f"❌ Error: No magnet link provided!"
        print(error)
        send_telegram_update(error)
        print('Usage: python3 smart_download.py "MAGNET_LINK_HERE"')
        return
    # Get the link from the command line argument
    MAGNET_LINK = sys.argv[1]

    try:
        # 1. Connect to qBittorrent
        qbt = qbittorrentapi.Client(host='localhost', port=8080, username=QBT_USER, password=QBT_PASS)
        try:
            qbt.auth_log_in()
        except qbittorrentapi.LoginFailed:
            print("❌ QBT Login Failed! Check your password.")
            return

        # 3. Add Torrent with "No Seeding" settings
        update = f"🚀 Adding torrent to queue..."
        print(update)
        send_telegram_update(update)
        # *********************************************
        # ADJUST ratio_limit and seeding_time_limit to stop seeding
        qbt.torrents_add(
            urls=MAGNET_LINK,
            paused=False,
            ratio_limit=1.5, #1.5 will seed 1.5 times as much as you downloaded. Set to 0 to not seed.
            seeding_time_limit=-1 #Set to 0 to not seed. -1 will ignore time limit and keep seeding until ratio is hit.
        )

        # 4. Monitor Progress
        #update = f"📊 Downloading (Monitoring status)..."
        half_way = False
        beginning = False

        while True:
            # Get the most recent torrent
            torrents = qbt.torrents_info(sort='added_on', reverse=True)
            if not torrents:
                break

            t = torrents[0]

            progress = t.progress * 100
            speed = t.dlspeed / 1024 / 1024  # Convert to MB/s

            #sys.stdout.write(f"\rProgress: {progress:.2f}% | Speed: {speed:.2f} MB/s | Status: {t.state}    ")
            #sys.stdout.flush()

            progress_pct = int(progress)  # Get whole number like 25, 26.
            if not beginning:
                beginning = True
                filename = t.name
                send_telegram_update(f"📥 Started downloading: {filename}")

            if (progress_pct >= 50) and (not half_way):
                half_way =True
                filename = t.name
                update_text = f"⏳ Downloading: {filename} \n📊Progress: {progress_pct}% | Speed: {speed:.2f} MB/s"
                send_telegram_update(update_text)

            # 5. Handle Completion (Stop seeding immediately)
            # 'uploading' or 'seeding' means the download is 100% done
            if t.progress == 1.0 or t.state in ['uploading', 'seeding', 'stalledUP']:
                print(f"\n✅ Download 100% complete.")
                filename = t.name
                update = f"✅ {filename} download 100% complete."
                send_telegram_update(update)


                # Optional: Delete the torrent from the list but KEEP the file
                #*************************************
                #UNCOMMENT THE BELOW LINES TO STOP SEEDING AND REMOVE ENTRY.
                # update = f"🧹 Cleaning up qBittorrent (Removing torrent entry)..."
                # print(update)
                # send_telegram_update(update)
                #qbt.torrents_delete(delete_files=False, torrent_hashes=t.hash)

                break

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Script stopped by user.")
        send_telegram_update(f"🛑 Script stopped by user.")
    except Exception as e:
        print(f"\n⚠️  An error occurred: {e}")
        send_telegram_update(f"⚠️  An error occurred: {e}")


if __name__ == "__main__":
    main()