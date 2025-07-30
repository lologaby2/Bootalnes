import os
import telebot
import yt_dlp
import whisper
import requests
import threading
import time
import random

BOT_TOKEN = "7612945576:AAGxWkW1edlUIXzlaVLqvD-O0mzDpnXho0E"
bot = telebot.TeleBot(BOT_TOKEN)

whisper_model = whisper.load_model("base")
os.makedirs("downloads", exist_ok=True)

last_activity = time.time()

def download_video(url):
    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "mp4",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def transcribe_audio(video_path):
    result = whisper_model.transcribe(video_path)
    return result["text"]

def process_transcription(chat_id, path):
    try:
        bot.send_message(chat_id, "🧠 جاري استخراج النص...")
        text = transcribe_audio(path)
        bot.send_message(chat_id, f"📜 النص:\n{text}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء استخراج النص:\n{e}")

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def handle_tiktok_video(message):
    global last_activity
    last_activity = time.time()

    chat_id = message.chat.id
    original_url = message.text.strip().split()[0]

    try:
        if "vt.tiktok.com" in original_url or "vm.tiktok.com" in original_url:
            response = requests.head(original_url, allow_redirects=True)
            full_url = response.url.split("?")[0]
        else:
            full_url = original_url.split("?")[0]
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل في توسيع الرابط:\n{e}")
        return

    if "/video/" not in full_url:
        bot.send_message(chat_id, "❌ الرابط لا يشير إلى فيديو تيك توك صالح.")
        return

    try:
        bot.send_message(chat_id, "⏬ جاري تنزيل الفيديو...")
        path = download_video(full_url)

        with open(path, "rb") as f:
            bot.send_video(chat_id, f)

        threading.Thread(target=process_transcription, args=(chat_id, path)).start()

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء المعالجة:\n{e}")

def auto_shutdown_timer():
    while True:
        if time.time() - last_activity > 600:
            print("🛑 تم إيقاف البوت تلقائيًا بسبب الخمول")
            os._exit(0)
        time.sleep(10)

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=auto_shutdown_timer, daemon=True).start()
    print("✅ البوت يعمل باستخدام Long Polling...")
    bot.polling(none_stop=True, timeout=60)
