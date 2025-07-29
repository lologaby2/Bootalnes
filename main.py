import os
import telebot
import yt_dlp
import whisper
import requests
import threading
from flask import Flask, request

# توكن البوت
BOT_TOKEN = "7612945576:AAGxWkW1edlUIXzlaVLqvD-O0mzDpnXho0E"

# إعداد البوت و Flask
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# إنشاء مجلد التنزيلات
os.makedirs("downloads", exist_ok=True)

# تحميل نموذج Whisper مرة واحدة
whisper_model = whisper.load_model("base")

# تحميل فيديو تيك توك
def download_video(url):
    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "mp4",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# استخراج النص باستخدام Whisper
def transcribe_audio(video_path):
    result = whisper_model.transcribe(video_path)
    return result["text"]

# معالجة النص في خيط منفصل
def process_transcription(chat_id, path):
    try:
        bot.send_message(chat_id, "🧠 جاري استخراج النص...")
        text = transcribe_audio(path)
        bot.send_message(chat_id, f"📜 النص:\n{text}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء استخراج النص:\n{e}")

# استقبال الرسائل
@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def handle_tiktok_video(message):
    chat_id = message.chat.id
    original_url = message.text.strip().split()[0]

    # توسيع الرابط إذا كان مختصرًا
    try:
        if "vt.tiktok.com" in original_url or "vm.tiktok.com" in original_url:
            response = requests.head(original_url, allow_redirects=True)
            full_url = response.url.split("?")[0]
        else:
            full_url = original_url.split("?")[0]
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل في توسيع الرابط:\n{e}")
        return

    # التأكد أنه رابط فيديو
    if "/video/" not in full_url:
        bot.send_message(chat_id, "❌ الرابط لا يشير إلى فيديو تيك توك صالح.")
        return

    try:
        bot.send_message(chat_id, "⏬ جاري تنزيل الفيديو...")
        path = download_video(full_url)

        with open(path, "rb") as f:
            bot.send_video(chat_id, f)

        # استخراج النص في خيط منفصل لتجنب انقطاع Webhook
        threading.Thread(target=process_transcription, args=(chat_id, path)).start()

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء المعالجة:\n{e}")

# إعداد Webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# بدون app.run()، لأننا سنستخدم gunicorn في التشغيل
if __name__ == "__main__":
    print("✅ البوت يعمل عبر Webhook وينتظر الطلبات...")
    bot.remove_webhook()
    bot.set_webhook(url=f"https://bootalnes-production.up.railway.app/{BOT_TOKEN}")
