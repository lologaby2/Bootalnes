import os
import time
import telebot
import yt_dlp
import whisper
import requests
import threading
import sys

# توكن البوت
BOT_TOKEN = "7612945576:AAGxWkW1edlUIXzlaVLqvD-O0mzDpnXho0E"
bot = telebot.TeleBot(BOT_TOKEN)

# إنشاء مجلد التنزيلات
os.makedirs("downloads", exist_ok=True)

# تحميل نموذج Whisper مرة واحدة
whisper_model = whisper.load_model("base")

# آخر وقت نشاط
last_activity = time.time()

# مؤقت إيقاف تلقائي بعد 10 دقائق خمول
def auto_shutdown_timer():
    global last_activity
    while True:
        if time.time() - last_activity > 600:
            print("⏹️ تم الإيقاف التلقائي بعد 10 دقائق من الخمول.")
            sys.exit()
        time.sleep(30)

threading.Thread(target=auto_shutdown_timer, daemon=True).start()

# تحميل الفيديو
def download_video(url):
    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "mp4",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# تحويل الفيديو إلى نص
def transcribe_audio(video_path):
    result = whisper_model.transcribe(video_path)
    return result["text"]

# المعالجة في خيط منفصل
def process_transcription(chat_id, path):
    try:
        bot.send_message(chat_id, "🧠 جاري استخراج النص...")
        text = transcribe_audio(path)
        bot.send_message(chat_id, f"📜 النص:\n{text}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء استخراج النص:\n{e}")

# التعامل مع رابط تيك توك
@bot.message_handler(func=lambda msg: "tiktok.com/" in msg.text)
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

# بدء البوت بلونغ بولينغ
if __name__ == "__main__":
    print("✅ البوت يعمل الآن عبر polling وينتظر الرسائل...")
    bot.infinity_polling()
