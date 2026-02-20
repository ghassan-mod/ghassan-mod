import os
import asyncio
import re
import threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telebot import TeleBot, types

# ===== الإعدادات (مضافة كما طلبت) =====
API_ID = int(os.getenv("API_ID", 39458857))
API_HASH = os.getenv("API_HASH", "3b62c284e0f6b6b0b16ba6d7b46a4a6f")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8540030986:AAGkaPnTE52X0BAkOKfZ3ymsqLurod9UDic")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "967735264023")  # موجود لكن غير مستخدم
SESSION_STRING = os.getenv("SESSION_STRING", "SESSION_STRING_HERE")

CHANNEL = os.getenv("CHANNEL", "GSN_MOD")
ADMIN_ID = int(os.getenv("ADMIN_ID", 1972494449))

# ===== إنشاء العملاء =====
user_client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

bot = TeleBot(BOT_TOKEN)

# ===== بيانات =====
versions = []
users = {}

# ===== قراءة القناة =====
async def update_versions():
    global versions
    print("🔄 تحديث النسخ من القناة...")
    try:
        channel = await user_client.get_entity(CHANNEL)
        versions = []

        async for msg in user_client.iter_messages(channel, limit=100):
            if not msg.text:
                continue

            text = msg.text

            ram = None
            m = re.search(r'(\d+)\s*رام|رام[:\s]*(\d+)', text)
            if m:
                ram = int(next(g for g in m.groups() if g))

            game = None
            if "لايت" in text or "LITE" in text.upper():
                game = "PUBG LITE"
            elif "موبايل" in text or "MOBILE" in text.upper():
                game = "PUBG MOBILE"

            if ram and game:
                versions.append({
                    "game": game,
                    "ram": ram,
                    "link": f"https://t.me/{CHANNEL}/{msg.id}"
                })

        print(f"✅ تم تحميل {len(versions)} نسخة")

    except Exception as e:
        print("❌ خطأ:", e)

# ===== أوامر البوت =====
@bot.message_handler(commands=["start"])
def start(message):
    users[message.chat.id] = {}
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🎮 PUBG MOBILE", callback_data="mobile"),
        types.InlineKeyboardButton("🎯 PUBG LITE", callback_data="lite"),
    )
    kb.add(types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{CHANNEL}"))

    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك في بوت GSNMOD\nاختر اللعبة 👇",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    if call.data == "mobile":
        users[call.message.chat.id]["game"] = "PUBG MOBILE"
    elif call.data == "lite":
        users[call.message.chat.id]["game"] = "PUBG LITE"

    bot.edit_message_text(
        "📱 أرسل رام جهازك (مثال: 4)",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def ram_handler(message):
    ram = int(message.text)
    game = users.get(message.chat.id, {}).get("game")

    if not game:
        bot.send_message(message.chat.id, "❌ اختر اللعبة أولاً عبر /start")
        return

    matches = [v for v in versions if v["game"] == game]
    if not matches:
        bot.send_message(message.chat.id, "❌ لا توجد نسخ حالياً")
        return

    best = min(matches, key=lambda x: abs(x["ram"] - ram))

    bot.send_message(
        message.chat.id,
        f"""🎯 النسخة المناسبة لك:

🎮 {game}
💾 رام: {best['ram']}GB
📥 الرابط:
{best['link']}

🔗 @{CHANNEL}"""
    )

# ===== تشغيل اليوزر بوت =====
async def run_user():
    await user_client.start()
    print("✅ يوزر بوت شغال")
    await update_versions()

    @user_client.on(events.NewMessage(chats=CHANNEL))
    async def watcher(event):
        print("📢 منشور جديد")
        await update_versions()

    while True:
        await asyncio.sleep(300)

def start_user():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_user())

# ===== التشغيل =====
if __name__ == "__main__":
    threading.Thread(target=start_user, daemon=True).start()
    bot.infinity_polling()
