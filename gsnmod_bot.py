# gsnmod_bot.py - نسخة السحابة
import os
import asyncio
import re
from datetime import datetime
from telethon import TelegramClient, events
from telebot import TeleBot, types
import threading

# إعدادات من المتغيرات البيئية
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
CHANNEL = os.environ.get('CHANNEL', 'GSN_MOD')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

# إنشاء الاتصالات
user_client = TelegramClient('session', API_ID, API_HASH)
bot = TeleBot(BOT_TOKEN)

# قاعدة البيانات
versions = []
users = {}
stats = {'downloads': 0, 'users': 0}

# دالة قراءة القناة
async def update_versions():
    global versions
    print("🔄 تحديث النسخ...")
    try:
        channel = await user_client.get_entity(CHANNEL)
        async for msg in user_client.iter_messages(channel, limit=100):
            if msg.text:
                text = msg.text
                ram = None
                ram_match = re.search(r'رام[:\s]*(\d+)|(\d+)\s*رام', text, re.IGNORECASE)
                if ram_match:
                    for g in ram_match.groups():
                        if g and g.isdigit():
                            ram = int(g)
                            break
                
                game = None
                if 'لايت' in text or 'LITE' in text.upper():
                    game = 'PUBG LITE'
                elif 'موبايل' in text or 'MOBILE' in text.upper():
                    game = 'PUBG MOBILE'
                
                if ram and game:
                    versions.append({
                        'id': msg.id,
                        'game': game,
                        'ram': ram,
                        'link': f"https://t.me/{CHANNEL}/{msg.id}",
                        'text': text[:100]
                    })
        print(f"✅ تم تحديث {len(versions)} نسخة")
    except Exception as e:
        print(f"❌ خطأ: {e}")

# أمر /start
@bot.message_handler(commands=['start'])
def start(message):
    users[message.chat.id] = {}
    stats['users'] = len(users)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🎮 PUBG MOBILE", callback_data="mobile"),
        types.InlineKeyboardButton("🎯 PUBG LITE", callback_data="lite")
    )
    
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك في بوت GSNMOD على السحابة!\nاختر اللعبة:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "mobile":
        users[call.message.chat.id]['game'] = 'PUBG MOBILE'
        bot.edit_message_text("أرسل رام جهازك:", call.message.chat.id, call.message.message_id)
    elif call.data == "lite":
        users[call.message.chat.id]['game'] = 'PUBG LITE'
        bot.edit_message_text("أرسل رام جهازك:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def ram_handler(message):
    ram = int(message.text)
    game = users.get(message.chat.id, {}).get('game', '')
    
    results = [v for v in versions if v['game'] == game]
    results.sort(key=lambda x: abs(x['ram'] - ram))
    
    if results:
        v = results[0]
        stats['downloads'] += 1
        bot.send_message(
            message.chat.id,
            f"🎯 أفضل نسخة:\n{v['game']} - رام {v['ram']}GB\n📥 {v['link']}"
        )
    else:
        bot.send_message(message.chat.id, "😢 لا توجد نسخة حالياً")

# تشغيل اليوزر بوت
async def run_user():
    await user_client.start(phone=PHONE_NUMBER)
    print("✅ يوزر بوت متصل")
    await update_versions()
    
    @user_client.on(events.NewMessage(chats=CHANNEL))
    async def handler(e):
        await update_versions()
    
    while True:
        await asyncio.sleep(300)
        await update_versions()

def start_user():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_user())

# التشغيل
if __name__ == "__main__":
    print("🚀 تشغيل بوت GSNMOD على السحابة")
    threading.Thread(target=start_user, daemon=True).start()
    bot.infinity_polling()
