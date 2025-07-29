import os
import telebot
import yt_dlp
import whisper
import requests
import threading
from flask import Flask, request

BOT_TOKEN = "7612945576:AAGxWkW1edlUIXzlaVLqvD-O0mzDpnXho0E"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

os.makedirs("downloads", exist_ok=True)

whisper_model = whisper.load_model("base")

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

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# ✅ إعداد Webhook عند التشغيل
bot.remove_webhook()
bot.set_webhook(url=f"https://bootalnes-production.up.railway.app/{BOT_TOKEN}")
