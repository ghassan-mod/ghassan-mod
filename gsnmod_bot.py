import os
import asyncio
import re
import threading
from datetime import datetime
from telethon import TelegramClient, events
from telebot import TeleBot, types

# ===== إعدادات من المتغيرات البيئية =====
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')
CHANNEL = os.environ.get('CHANNEL', 'GSN_MOD')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

# ===== إنشاء الاتصالات =====
user_client = TelegramClient('session', API_ID, API_HASH)
bot = TeleBot(BOT_TOKEN)

# ===== قاعدة البيانات =====
versions = []
users = {}
stats = {'downloads': 0, 'users': 0}

# ===== دالة قراءة القناة =====
async def update_versions():
    global versions
    print("🔄 جاري تحديث النسخ من القناة...")
    try:
        channel = await user_client.get_entity(CHANNEL)
        versions = []
        async for message in user_client.iter_messages(channel, limit=100):
            if message.text:
                text = message.text
                
                # استخراج الرام
                ram = None
                ram_match = re.search(r'رام[:\s]*(\d+)|(\d+)\s*رام', text, re.IGNORECASE)
                if ram_match:
                    for g in ram_match.groups():
                        if g and g.isdigit():
                            ram = int(g)
                            break
                
                # تحديد اللعبة
                game = None
                if 'لايت' in text or 'LITE' in text.upper():
                    game = 'PUBG LITE'
                elif 'موبايل' in text or 'MOBILE' in text.upper():
                    game = 'PUBG MOBILE'
                
                if ram and game:
                    versions.append({
                        'id': message.id,
                        'game': game,
                        'ram': ram,
                        'link': f"https://t.me/{CHANNEL}/{message.id}",
                        'text': text[:100]
                    })
        print(f"✅ تم تحديث {len(versions)} نسخة")
    except Exception as e:
        print(f"❌ خطأ في قراءة القناة: {e}")

# ===== أمر /start =====
@bot.message_handler(commands=['start'])
def start_command(message):
    users[message.chat.id] = {}
    stats['users'] = len(users)
    
    keyboard = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎮 PUBG MOBILE", callback_data="mobile")
    btn2 = types.InlineKeyboardButton("🎯 PUBG LITE", callback_data="lite")
    btn3 = types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{CHANNEL}")
    keyboard.add(btn1, btn2)
    keyboard.add(btn3)
    
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك في بوت GSNMOD على السحابة!\n\nاختر اللعبة المناسبة 👇",
        reply_markup=keyboard
    )

# ===== اختيار اللعبة =====
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "mobile":
        users[call.message.chat.id] = {'game': 'PUBG MOBILE'}
        bot.edit_message_text(
            "🎮 اخترت: PUBG MOBILE\n\n📱 أرسل رام جهازك (رقم فقط):",
            call.message.chat.id,
            call.message.message_id
        )
    elif call.data == "lite":
        users[call.message.chat.id] = {'game': 'PUBG LITE'}
        bot.edit_message_text(
            "🎯 اخترت: PUBG LITE\n\n📱 أرسل رام جهازك (رقم فقط):",
            call.message.chat.id,
            call.message.message_id
        )

# ===== استقبال الرام =====
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def ram_handler(message):
    ram = int(message.text)
    user_data = users.get(message.chat.id, {})
    game = user_data.get('game')
    
    if not game:
        bot.send_message(message.chat.id, "❌ الرجاء اختيار اللعبة أولاً عبر /start")
        return
    
    # فلترة النسخ
    filtered = [v for v in versions if v['game'] == game]
    filtered.sort(key=lambda x: abs(x['ram'] - ram))
    
    if filtered:
        best = filtered[0]
        stats['downloads'] += 1
        
        response = f"""🎯 تم العثور على نسخة مناسبة!

🎮 {game}
💾 رام: {best['ram']}GB
📥 الرابط: {best['link']}

🔗 @{CHANNEL}"""
        
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(
            message.chat.id,
            f"😢 لا توجد نسخة للعبة {game} بالرام {ram}GB حالياً.\n\nتابع قناتنا @{CHANNEL}"
        )

# ===== تشغيل اليوزر بوت =====
async def run_user_bot():
    try:
        await user_client.start(phone=PHONE_NUMBER)
        print("✅ يوزر بوت متصل بنجاح!")
        
        # تحديث أولي
        await update_versions()
        
        # مراقبة القناة للتحديثات
        @user_client.on(events.NewMessage(chats=CHANNEL))
        async def handler(event):
            print("📢 منشور جديد في القناة!")
            await update_versions()
        
        # تحديث دوري كل 5 دقائق
        while True:
            await asyncio.sleep(300)
            await update_versions()
            
    except Exception as e:
        print(f"❌ خطأ في اليوزر بوت: {e}")

def start_user_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_user_bot())

# ===== تشغيل البوت =====
if __name__ == "__main__":
    print("🚀 تشغيل بوت GSNMOD على السحابة...")
    
    # تشغيل اليوزر بوت في خيط منفصل
    user_thread = threading.Thread(target=start_user_thread, daemon=True)
    user_thread.start()
    
    # تشغيل البوت العادي
    bot.infinity_polling()
