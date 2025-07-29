import os
import telebot
import yt_dlp
import whisper
from flask import Flask, request

BOT_TOKEN = "7612945576:AAGxWkW1edlUIXzlaVLqvD-O0mzDpnXho0E"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
os.makedirs("downloads", exist_ok=True)

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
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text and "/video/" in message.text)
def handle_tiktok_video(message):
    url = message.text.strip()
    chat_id = message.chat.id
    try:
        bot.send_message(chat_id, "⏬ جاري تنزيل الفيديو...")
        path = download_video(url)
        with open(path, "rb") as f:
            bot.send_video(chat_id, f)

        bot.send_message(chat_id, "🧠 جاري استخراج النص...")
        text = transcribe_audio(path)
        bot.send_message(chat_id, f"📜 النص:\n{text}")

        bot.send_message(chat_id, "✅ تم التنفيذ، سيتم إيقاف البوت.")
        os._exit(0)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء المعالجة:\n{e}")
        os._exit(1)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    print("✅ البوت جاهز للعمل عند الطلب...")
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR-PROJECT.up.railway.app/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
