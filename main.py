import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from datetime import datetime
import traceback
import time

# --- تنظیمات لاگینگ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وب سرور ساده ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("✅ VPN Bot is Running!".encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def run_web():
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Web server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Web server error: {e}")

# --- توکن و آیدی ادمین ---
TOKEN = '8305364438:AAGAT39wGQey9tzxMVafEiRRXz1eGNvpfhY'
ADMIN_ID = 5993860770

# --- مسیر دیتابیس ---
DB_FILE = 'data.json'

# --- پلن‌های پیش‌فرض ---
DEFAULT_PLANS = {
    "🚀 قوی": [
        {"id": 1, "name": "⚡️ پلن قوی 20GB", "price": 80, "volume": "20GB", "days": 30, "users": 1},
        {"id": 2, "name": "🔥 پلن قوی 50GB", "price": 140, "volume": "50GB", "days": 30, "users": 1}
    ],
    "💎 ارزان": [
        {"id": 3, "name": "💎 پلن اقتصادی 10GB", "price": 45, "volume": "10GB", "days": 30, "users": 1},
        {"id": 4, "name": "💎 پلن اقتصادی 20GB", "price": 75, "volume": "20GB", "days": 30, "users": 1}
    ],
    "🎯 به صرفه": [
        {"id": 5, "name": "🎯 پلن ویژه 30GB", "price": 110, "volume": "30GB", "days": 30, "users": 1},
        {"id": 6, "name": "🎯 پلن ویژه 60GB", "price": 190, "volume": "60GB", "days": 30, "users": 1}
    ],
    "👥 چند کاربره": [
        {"id": 7, "name": "👥 2 کاربره 40GB", "price": 150, "volume": "40GB", "days": 30, "users": 2},
        {"id": 8, "name": "👥 3 کاربره 60GB", "price": 210, "volume": "60GB", "days": 30, "users": 3}
    ]
}

# --- دکمه‌های پیش‌فرض منوی اصلی ---
DEFAULT_MENU_BUTTONS = [
    {"text": "💰 خرید اشتراک", "action": "buy"},
    {"text": "🎁 تست رایگان", "action": "test"},
    {"text": "📂 سرویس‌ها", "action": "services"},
    {"text": "⏳ تمدید", "action": "renew"},
    {"text": "👤 مشخصات من", "action": "profile"},
    {"text": "👤 پشتیبانی", "action": "support"},
    {"text": "📚 آموزش", "action": "guide"},
    {"text": "🤝 دعوت دوستان", "action": "invite"},
    {"text": "⭐ رضایت مشتریان", "action": "testimonials"}
]

# --- متن‌های پیش‌فرض برای همه بخش‌ها ---
DEFAULT_TEXTS = {
    "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته\n✅ نصب آسان",
    "support": "🆘 پشتیبانی: {support}",
    "guide": "📚 آموزش: {guide}",
    "test": "🎁 درخواست تست شما ثبت شد",
    "force": "🔒 برای استفاده از ربات باید در کانال زیر عضو شوید:\n{link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید.",
    "invite": "🤝 لینک دعوت شما:\n{link}\n\nبه ازای هر دعوت 1 روز هدیه",
    "testimonials": "⭐ **نظرات مشتریان ما** ⭐\n\n🔹 علی: عالی بود، سرعت خیلی خوبه 👍\n🔹 سارا: پشتیبانی عالی و سریع 👌\n🔹 رضا: از همه نظر راضی هستم ❤️\n🔹 مریم: قیمت منصفانه و کیفیت بالا 💯\n\n📢 برای دیدن نظرات بیشتر و ارسال نظر خود، به کانال ما بپیوندید:",
    "testimonials_channel": "@Testimonials_Channel",
    "payment_info": "💳 اطلاعات پرداخت\n━━━━━━━━━━━━━━\n👤 نام اکانت: {account}\n📦 پلن: {plan_name}\n📊 حجم: {volume}\n👥 {users_text}\n⏳ مدت: {days_text}\n💰 مبلغ: {price:,} تومان\n━━━━━━━━━━━━━━\n💳 شماره کارت:\n<code>{card_number}</code>\n👤 {card_name}\n━━━━━━━━━━━━━━\nپس از واریز، عکس فیش را بفرستید",
    "maintenance": "🔧 ربات در حال تعمیرات است. لطفاً بعداً مراجعه کنید.",
    "config_sent": "🎉 سرویس شما آماده است!\n━━━━━━━━━━━━━━━━━━━━\n👤 نام کاربری سرویس : {name}\n⏳ مدت زمان: {days_text}\n🗜 حجم سرویس: {volume}\n━━━━━━━━━━━━━━━━━━━━\nلینک اتصال:\n<code>{config}</code>\n━━━━━━━━━━━━━━━━━━━━\n🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر و انتخاب سیستم عامل خود را دریافت کنید\n\n🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه لینک‌ها رو استخراج کنید.\n\n🔵 کافیه لینک ساب خودتون رو بهش بدید تا تمامی کانفیگ‌هاش رو براتون خروجی بگیره.",
    "admin_panel": "🛠 پنل مدیریت",
    "back_button": "🔙 برگشت",
    "cancel": "❌ انصراف",
    "btn_admin": "⚙️ مدیریت"
}

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info("✅ Database loaded successfully")
                
                if "users" not in data:
                    data["users"] = {}
                if "brand" not in data:
                    data["brand"] = "تک نت وی‌پی‌ان"
                if "card" not in data:
                    data["card"] = {"number": "6277601368776066", "name": "محمد رضوانی"}
                if "support" not in data:
                    data["support"] = "@Support_Admin"
                if "guide" not in data:
                    data["guide"] = "@Guide_Channel"
                if "testimonials_channel" not in data:
                    data["testimonials_channel"] = "@Testimonials_Channel"
                if "force_join" not in data:
                    data["force_join"] = {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""}
                if "bot_status" not in data:
                    data["bot_status"] = {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]}
                if "categories" not in data or not data["categories"]:
                    data["categories"] = DEFAULT_PLANS.copy()
                if "menu_buttons" not in data:
                    data["menu_buttons"] = DEFAULT_MENU_BUTTONS.copy()
                if "texts" not in data:
                    data["texts"] = DEFAULT_TEXTS.copy()
                else:
                    for key, value in DEFAULT_TEXTS.items():
                        if key not in data["texts"]:
                            data["texts"][key] = value
                
                return data
    except Exception as e:
        logger.error(f"❌ Error loading database: {e}")
    
    logger.info("📁 Creating default database")
    return {
        "users": {},
        "brand": "تک نت وی‌پی‌ان",
        "card": {"number": "6277601368776066", "name": "محمد رضوانی"},
        "support": "@Support_Admin",
        "guide": "@Guide_Channel",
        "testimonials_channel": "@Testimonials_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "menu_buttons": DEFAULT_MENU_BUTTONS.copy(),
        "force_join": {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""},
        "bot_status": {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]},
        "texts": DEFAULT_TEXTS.copy()
    }

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("💾 Database saved successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving database: {e}")
        return False

db = load_db()
user_data = {}

def get_main_menu(uid):
    buttons = db["menu_buttons"]
    kb = []
    row = []
    for i, btn in enumerate(buttons):
        row.append(btn["text"])
        if (i + 1) % 2 == 0 or i == len(buttons) - 1:
            kb.append(row)
            row = []
    if str(uid) == str(ADMIN_ID):
        kb.append([db["texts"]["btn_admin"]])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    return ReplyKeyboardMarkup([[db["texts"]["back_button"]]], resize_keyboard=True)

def get_admin_menu():
    kb = [
        ['📋 مدیریت منو', '📦 مدیریت دسته‌ها'],
        ['➕ پلن جدید', '➖ حذف پلن', '✏️ ویرایش پلن'],
        ['💳 ویرایش کارت', '📝 ویرایش متن‌ها'],
        ['👤 ویرایش پشتیبان', '📢 ویرایش کانال آموزش'],
        ['📢 ویرایش کانال نظرات', '🏷 ویرایش برند'],
        ['🔒 عضویت اجباری', '🔛 وضعیت ربات'],
        ['📊 آمار', '📦 بکاپ‌گیری'],
        ['🔄 بازیابی بکاپ', '📨 ارسال همگانی'],
        [db["texts"]["back_button"]]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def check_join(user_id, context):
    if not db["force_join"]["enabled"]:
        return True
    channel_id = db["force_join"].get("channel_id", "")
    channel_username = db["force_join"].get("channel_username", "")
    if not channel_id and not channel_username:
        return True
    if channel_id:
        try:
            member = context.bot.get_chat_member(chat_id=int(channel_id), user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    if channel_username:
        try:
            member = context.bot.get_chat_member(chat_id=channel_username, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    return False

def start(update, context):
    try:
        if not update or not update.message:
            return
            
        uid = str(update.effective_user.id)
        
        args = context.args
        if args and args[0].isdigit() and args[0] != uid:
            inviter_id = args[0]
            if inviter_id in db["users"] and uid not in db["users"]:
                if "invited_users" not in db["users"][inviter_id]:
                    db["users"][inviter_id]["invited_users"] = []
                if uid not in db["users"][inviter_id]["invited_users"]:
                    db["users"][inviter_id]["invited_users"].append(uid)
        
        if uid not in db["users"]:
            db["users"][uid] = {
                "purchases": [], 
                "tests": [], 
                "test_count": 0,
                "invited_by": args[0] if args and args[0].isdigit() and args[0] != uid else None,
                "invited_users": [], 
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            save_db(db)
        
        user_data[uid] = {}
        
        if not db["bot_status"]["enabled"] and str(uid) != str(ADMIN_ID):
            update.message.reply_text(db["bot_status"]["message"])
            return
        
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"] and str(uid) != str(ADMIN_ID):
            if not check_join(uid, context):
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                msg = db["texts"]["force"].format(link=db["force_join"]["channel_link"])
                update.message.reply_text(msg, reply_markup=btn)
                return
        
        welcome = db["texts"]["welcome"].format(brand=db["brand"])
        update.message.reply_text(welcome, reply_markup=get_main_menu(uid))
        
    except Exception as e:
        logger.error(f"Error in start: {e}")
        try:
            if update and update.message:
                update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

def handle_msg(update, context):
    try:
        if not update or not update.message:
            return
            
        text = update.message.text
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')
        texts = db["texts"]

        # دیباگ - نمایش مرحله فعلی
        logger.info(f"👤 {uid} - مرحله: {step} - متن: {text}")

        if not db["bot_status"]["enabled"] and str(uid) != str(ADMIN_ID):
            update.message.reply_text(db["bot_status"]["message"])
            return

        if db["force_join"]["enabled"] and db["force_join"]["channel_link"] and str(uid) != str(ADMIN_ID):
            if not check_join(uid, context) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                update.message.reply_text(db["texts"]["force"].format(link=db["force_join"]["channel_link"]), reply_markup=btn)
                return

        if text == texts["back_button"] or text == '🔙 برگشت':
            user_data[uid] = {}
            start(update, context)
            return

        if text == '/start':
            start(update, context)
            return
        
        for btn in db["menu_buttons"]:
            if text == btn["text"]:
                action = btn["action"]
                if action == "buy":
                    categories = list(db["categories"].keys())
                    keyboard = []
                    for cat in categories:
                        keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
                    keyboard.append([InlineKeyboardButton(texts["back_button"], callback_data="back_to_main")])
                    update.message.reply_text("📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                
                elif action == "test":
                    try:
                        if "test_count" not in db["users"][uid]:
                            db["users"][uid]["test_count"] = 0
                        
                        if db["users"][uid]["test_count"] >= 1:
                            update.message.reply_text("❌ شما قبلاً یک بار تست دریافت کرده‌اید و امکان دریافت تست مجدد وجود ندارد.")
                            return
                        
                        db["users"][uid]["test_count"] += 1
                        if "tests" not in db["users"][uid]:
                            db["users"][uid]["tests"] = []
                        db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
                        save_db(db)
                        
                        update.message.reply_text(db["texts"]["test"])
                        
                        admin_btn = InlineKeyboardMarkup([[
                            InlineKeyboardButton("📤 ارسال تست", callback_data=f"test_{uid}_{name}")
                        ]])
                        
                        admin_msg = f"🎁 درخواست تست جدید\n👤 {name}\n🆔 {uid}"
                        context.bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_btn)
                        
                    except Exception as e:
                        logger.error(f"❌ Error in test action: {e}")
                        update.message.reply_text("❌ خطا در ثبت تست. لطفاً دوباره تلاش کنید.")
                    return
                
                elif action == "services":
                    purchases = db["users"][uid].get("purchases", [])
                    tests = db["users"][uid].get("tests", [])
                    msg = "📂 سرویس‌های شما:\n━━━━━━━━━━\n"
                    if purchases:
                        msg += "✅ خریدها:\n"
                        for i, p in enumerate(purchases[-10:], 1):
                            msg += f"{i}. {p}\n"
                    else:
                        msg += "❌ خریدی ندارید\n"
                    if tests:
                        msg += "\n🎁 تست‌ها:\n"
                        for i, t in enumerate(tests[-5:], 1):
                            msg += f"{i}. {t}\n"
                    update.message.reply_text(msg)
                    return
                
                elif action == "renew":
                    purchases = db["users"][uid].get("purchases", [])
                    if not purchases:
                        update.message.reply_text("❌ شما سرویسی برای تمدید ندارید.")
                        return
                    keyboard = []
                    for i, p in enumerate(purchases[-5:]):
                        keyboard.append([InlineKeyboardButton(f"🔄 {p[:30]}...", callback_data=f"renew_{i}")])
                    keyboard.append([InlineKeyboardButton(texts["back_button"], callback_data="back_to_main")])
                    update.message.reply_text("🔁 سرویس مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                
                elif action == "profile":
                    user = db["users"][uid]
                    purchases_count = len(user.get("purchases", []))
                    tests_count = len(user.get("tests", []))
                    invited_count = len(user.get("invited_users", []))
                    bot_username = context.bot.get_me().username
                    invite_link = f"https://t.me/{bot_username}?start={uid}"
                    profile_text = (
                        f"👤 <b>مشخصات کاربر</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"نام: {update.effective_user.first_name}\n"
                        f"🆔 آیدی عددی: <code>{uid}</code>\n"
                        f"👤 یوزرنیم: @{update.effective_user.username or 'ندارد'}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 تعداد خریدها: {purchases_count}\n"
                        f"🎁 تعداد تست‌ها: {tests_count}\n"
                        f"👥 زیرمجموعه‌ها: {invited_count}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔗 لینک دعوت اختصاصی:\n"
                        f"<code>{invite_link}</code>"
                    )
                    update.message.reply_text(profile_text, parse_mode='HTML')
                    return
                
                elif action == "support":
                    update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
                    return
                
                elif action == "guide":
                    update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
                    return
                
                elif action == "invite":
                    bot_username = context.bot.get_me().username
                    link = f"https://t.me/{bot_username}?start={uid}"
                    msg = db["texts"]["invite"].format(link=link)
                    update.message.reply_text(msg)
                    return
                
                elif action == "testimonials":
                    channel = db.get("testimonials_channel", "@Testimonials_Channel")
                    btn = InlineKeyboardMarkup([[
                        InlineKeyboardButton("📢 کانال نظرات", url=f"https://t.me/{channel.replace('@', '')}")
                    ]])
                    update.message.reply_text(
                        db["texts"]["testimonials"],
                        reply_markup=btn,
                        parse_mode='Markdown'
                    )
                    return

        if str(uid) == str(ADMIN_ID):
            if text == db["texts"]["btn_admin"]:
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu())
                return

            if text == '📋 مدیریت منو':
                keyboard = [['➕ دکمه جدید', '➖ حذف دکمه'], ['✏️ ویرایش دکمه', '🔁 ترتیب دکمه‌ها'], ['🔙 برگشت']]
                menu_text = "📋 دکمه‌های فعلی منو:\n"
                for i, btn in enumerate(db["menu_buttons"], 1):
                    menu_text += f"{i}. {btn['text']} (عملکرد: {btn['action']})\n"
                update.message.reply_text(menu_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return

            if text == '➕ دکمه جدید':
                user_data[uid] = {'step': 'new_menu_button_text'}
                update.message.reply_text("📝 متن دکمه جدید را بفرستید:", reply_markup=back_btn())
                return

            if step == 'new_menu_button_text':
                user_data[uid]['button_text'] = text
                user_data[uid]['step'] = 'new_menu_button_action'
                actions = [
                    ['buy', 'test', 'services'],
                    ['renew', 'profile', 'support'],
                    ['guide', 'invite', 'testimonials'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "🔧 عملکرد دکمه را انتخاب کنید:\n"
                    "buy: خرید\n"
                    "test: تست\n"
                    "services: سرویس‌ها\n"
                    "renew: تمدید\n"
                    "profile: مشخصات\n"
                    "support: پشتیبانی\n"
                    "guide: آموزش\n"
                    "invite: دعوت\n"
                    "testimonials: رضایت مشتریان",
                    reply_markup=ReplyKeyboardMarkup(actions, resize_keyboard=True)
                )
                return

            if step == 'new_menu_button_action':
                valid_actions = ['buy', 'test', 'services', 'renew', 'profile', 'support', 'guide', 'invite', 'testimonials']
                if text in valid_actions:
                    db["menu_buttons"].append({"text": user_data[uid]['button_text'], "action": text})
                    save_db(db)
                    update.message.reply_text("✅ دکمه جدید اضافه شد!", reply_markup=get_admin_menu())
                    user_data[uid] = {}
                else:
                    update.message.reply_text("❌ عملکرد نامعتبر!")
                return

            if text == '➖ حذف دکمه':
                keyboard = []
                for i, btn in enumerate(db["menu_buttons"]):
                    keyboard.append([InlineKeyboardButton(f"❌ {btn['text']}", callback_data=f"del_menu_{i}")])
                keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("🗑 دکمه مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if text == '✏️ ویرایش دکمه':
                keyboard = []
                for i, btn in enumerate(db["menu_buttons"]):
                    keyboard.append([InlineKeyboardButton(f"✏️ {btn['text']}", callback_data=f"edit_menu_{i}")])
                keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("✏️ دکمه مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if step == 'edit_menu':
                try:
                    index = user_data[uid]['menu_index']
                    db["menu_buttons"][index]['text'] = text
                    save_db(db)
                    update.message.reply_text("✅ متن دکمه با موفقیت ویرایش شد!", reply_markup=get_admin_menu())
                    user_data[uid] = {}
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
                return

            # ========== بخش ترتیب دکمه‌ها (رفع مشکل) ==========
            if text == '🔁 ترتیب دکمه‌ها':
                menu_text = "🔁 ترتیب فعلی دکمه‌ها:\n"
                for i, btn in enumerate(db["menu_buttons"], 1):
                    menu_text += f"{i}. {btn['text']}\n"
                
                menu_text += "\nبرای تغییر ترتیب، شماره دکمه‌ها رو با ویرگول جدا کنید.\n"
                menu_text += f"مثال: {','.join(str(x) for x in range(1, len(db['menu_buttons'])+1))}"
                
                user_data[uid] = {'step': 'reorder_menu'}
                logger.info(f"🔄 کاربر {uid} وارد مرحله ترتیب دکمه‌ها شد")
                update.message.reply_text(menu_text, reply_markup=back_btn())
                return

            if step == 'reorder_menu':
                try:
                    logger.info(f"🔄 کاربر {uid} در مرحله ترتیب - متن دریافتی: {text}")
                    
                    # پاکسازی متن
                    cleaned_text = text.replace('.', ',').replace('،', ',').replace(' ', '')
                    logger.info(f"🔄 متن پاکسازی شده: {cleaned_text}")
                    
                    # تبدیل به لیست اعداد
                    parts = []
                    for x in cleaned_text.split(','):
                        x = x.strip()
                        if x.isdigit():
                            parts.append(x)
                    
                    logger.info(f"🔄 اعداد استخراج شده: {parts}")
                    
                    if len(parts) != len(db["menu_buttons"]):
                        update.message.reply_text(
                            f"❌ تعداد اعداد با تعداد دکمه‌ها هماهنگ نیست!\n"
                            f"تعداد دکمه‌ها: {len(db['menu_buttons'])}\n"
                            f"تعداد اعداد: {len(parts)}"
                        )
                        return
                    
                    new_order = [int(x) for x in parts]
                    
                    if sorted(new_order) != list(range(1, len(db["menu_buttons"]) + 1)):
                        update.message.reply_text(f"❌ اعداد باید از ۱ تا {len(db['menu_buttons'])} باشند!")
                        return
                    
                    # مرتب‌سازی مجدد
                    new_buttons = []
                    for index in new_order:
                        new_buttons.append(db["menu_buttons"][index - 1])
                    
                    db["menu_buttons"] = new_buttons
                    save_db(db)
                    
                    # نمایش ترتیب جدید
                    new_order_text = "✅ ترتیب جدید:\n"
                    for i, btn in enumerate(db["menu_buttons"], 1):
                        new_order_text += f"{i}. {btn['text']}\n"
                    
                    logger.info(f"✅ ترتیب جدید با موفقیت اعمال شد")
                    update.message.reply_text(new_order_text, reply_markup=get_admin_menu())
                    user_data[uid] = {}
                    
                except Exception as e:
                    logger.error(f"❌ خطا در ترتیب دکمه‌ها: {e}")
                    update.message.reply_text(f"❌ خطا: لطفاً اعداد را با ویرگول جدا کنید. مثال: 1,2,3,4")
                return

            if text == '📦 مدیریت دسته‌ها':
                keyboard = [['➕ دسته جدید', '➖ حذف دسته'], ['✏️ ویرایش دسته', '🔁 ترتیب دسته‌ها'], ['🔙 برگشت']]
                cats_text = "📦 دسته‌بندی‌های فعلی:\n"
                for i, cat in enumerate(db["categories"].keys(), 1):
                    cats_text += f"{i}. {cat}\n"
                update.message.reply_text(cats_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return

            if text == '➕ دسته جدید':
                user_data[uid] = {'step': 'new_category'}
                update.message.reply_text("📝 نام دسته‌بندی جدید را بفرستید:", reply_markup=back_btn())
                return

            if step == 'new_category':
                if text not in db["categories"]:
                    db["categories"][text] = []
                    save_db(db)
                    update.message.reply_text(f"✅ دسته‌بندی {text} اضافه شد!", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ این دسته قبلاً وجود دارد!")
                user_data[uid] = {}
                return

            if text == '➖ حذف دسته':
                keyboard = []
                for cat in db["categories"].keys():
                    keyboard.append([InlineKeyboardButton(f"❌ {cat}", callback_data=f"del_cat_{cat}")])
                keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("🗑 دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if text == '✏️ ویرایش دسته':
                keyboard = []
                for cat in db["categories"].keys():
                    keyboard.append([InlineKeyboardButton(f"✏️ {cat}", callback_data=f"edit_cat_{cat}")])
                keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("✏️ دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if step == 'edit_category':
                try:
                    old_cat = user_data[uid]['old_cat']
                    if text not in db["categories"]:
                        db["categories"][text] = db["categories"].pop(old_cat)
                        save_db(db)
                        update.message.reply_text(f"✅ دسته‌بندی با موفقیت به '{text}' تغییر نام یافت!", reply_markup=get_admin_menu())
                        user_data[uid] = {}
                    else:
                        update.message.reply_text("❌ این نام قبلاً وجود دارد!")
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
                return

            if text == '💳 ویرایش کارت':
                keyboard = [['شماره کارت', 'نام صاحب کارت'], ['🔙 برگشت']]
                current = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(current, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return

            if text == 'شماره کارت':
                user_data[uid] = {'step': 'card_num'}
                update.message.reply_text("💳 شماره کارت 16 رقمی را بفرستید:", reply_markup=back_btn())
                return

            if text == 'نام صاحب کارت':
                user_data[uid] = {'step': 'card_name'}
                update.message.reply_text("👤 نام صاحب کارت را بفرستید:", reply_markup=back_btn())
                return

            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'support'}
                update.message.reply_text("👤 آیدی پشتیبان را بفرستید:", reply_markup=back_btn())
                return

            if text == '📢 ویرایش کانال آموزش':
                user_data[uid] = {'step': 'edit_guide'}
                current = db.get("guide", "@Guide_Channel")
                update.message.reply_text(
                    f"📢 آیدی فعلی کانال آموزش: {current}\n\nآیدی جدید را بفرستید (مثال: @Channel_ID):",
                    reply_markup=back_btn()
                )
                return

            if step == 'edit_guide':
                db["guide"] = text
                save_db(db)
                update.message.reply_text("✅ کانال آموزش با موفقیت ویرایش شد!", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '📢 ویرایش کانال نظرات':
                user_data[uid] = {'step': 'testimonials_channel'}
                current = db.get("testimonials_channel", "@Testimonials_Channel")
                update.message.reply_text(
                    f"📢 آیدی فعلی کانال نظرات: {current}\n\nآیدی جدید را بفرستید (مثال: @Channel_ID):",
                    reply_markup=back_btn()
                )
                return

            if step == 'testimonials_channel':
                db["testimonials_channel"] = text
                save_db(db)
                update.message.reply_text("✅ کانال نظرات با موفقیت ویرایش شد!", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'brand'}
                update.message.reply_text("🏷 نام جدید برند را بفرستید:", reply_markup=back_btn())
                return

            if text == '📝 ویرایش متن‌ها':
                keyboard = [
                    ['خوش‌آمدگویی', 'پشتیبانی', 'آموزش'],
                    ['تست رایگان', 'عضویت اجباری', 'دعوت دوستان'],
                    ['اطلاعات پرداخت', 'تعمیرات', 'کانفیگ'],
                    ['رضایت مشتریان'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text("📝 کدام متن را ویرایش کنیم؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return

            text_map = {
                'خوش‌آمدگویی': 'welcome',
                'پشتیبانی': 'support',
                'آموزش': 'guide',
                'تست رایگان': 'test',
                'عضویت اجباری': 'force',
                'دعوت دوستان': 'invite',
                'اطلاعات پرداخت': 'payment_info',
                'تعمیرات': 'maintenance',
                'کانفیگ': 'config_sent',
                'رضایت مشتریان': 'testimonials'
            }
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                current_text = db["texts"][text_map[text]]
                update.message.reply_text(f"📝 متن فعلی:\n{current_text}\n\nمتن جدید را بفرستید:", reply_markup=back_btn())
                return

            if step and step.startswith('edit_'):
                key = step.replace('edit_', '')
                db["texts"][key] = text
                save_db(db)
                update.message.reply_text("✅ متن ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '🔒 عضویت اجباری':
                keyboard = [['✅ فعال', '❌ غیرفعال'], ['🔗 تنظیم لینک کانال'], ['🔙 برگشت']]
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                channel = db["force_join"]["channel_username"] or "تنظیم نشده"
                update.message.reply_text(
                    f"🔒 وضعیت عضویت اجباری:\nوضعیت: {status}\nکانال: {channel}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ فعال':
                if db["force_join"]["channel_link"]:
                    db["force_join"]["enabled"] = True
                    save_db(db)
                    update.message.reply_text("✅ عضویت اجباری فعال شد", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ ابتدا لینک کانال را تنظیم کنید")
                return

            if text == '❌ غیرفعال':
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ عضویت اجباری غیرفعال شد", reply_markup=get_admin_menu())
                return

            if text == '🔗 تنظیم لینک کانال':
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text("🔗 لینک کانال را بفرستید:\nمثال: https://t.me/mychannel", reply_markup=back_btn())
                return

            if text == '🔛 وضعیت ربات':
                keyboard = [['✅ روشن', '❌ خاموش'], ['✏️ ویرایش متن تعمیرات'], ['🔙 برگشت']]
                status = "✅ روشن" if db["bot_status"]["enabled"] else "❌ خاموش"
                update.message.reply_text(f"🔛 وضعیت ربات: {status}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return

            if text == '✅ روشن':
                db["bot_status"]["enabled"] = True
                save_db(db)
                update.message.reply_text("✅ ربات روشن شد", reply_markup=get_admin_menu())
                return

            if text == '❌ خاموش':
                db["bot_status"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ ربات خاموش شد", reply_markup=get_admin_menu())
                return

            if text == '✏️ ویرایش متن تعمیرات':
                user_data[uid] = {'step': 'edit_maintenance'}
                update.message.reply_text(f"📝 متن فعلی:\n{db['bot_status']['message']}\n\nمتن جدید را بفرستید:", reply_markup=back_btn())
                return

            if step == 'edit_maintenance':
                db["bot_status"]["message"] = text
                save_db(db)
                update.message.reply_text("✅ متن تعمیرات ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'set_link':
                db["force_join"]["channel_link"] = text
                if 't.me/' in text:
                    username = text.split('t.me/')[-1].split('/')[0].replace('@', '')
                    db["force_join"]["channel_username"] = f"@{username}"
                    try:
                        chat = context.bot.get_chat(f"@{username}")
                        db["force_join"]["channel_id"] = str(chat.id)
                        update.message.reply_text(f"✅ کانال شناسایی شد: {chat.title}")
                    except:
                        update.message.reply_text("⚠️ لینک ذخیره شد، اما ربات در کانال ادمین نیست!")
                save_db(db)
                update.message.reply_text("✅ لینک کانال ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '📊 آمار':
                total_users = len(db["users"])
                total_purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                total_tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                today = datetime.now().strftime("%Y-%m-%d")
                today_users = sum(1 for u in db["users"].values() if u.get("date", "").startswith(today))
                stats = f"📊 آمار ربات\n━━━━━━━━━━\n👥 کل کاربران: {total_users}\n🆕 کاربران جدید امروز: {today_users}\n💰 تعداد خریدها: {total_purchases}\n🎁 تعداد تست‌ها: {total_tests}"
                update.message.reply_text(stats)
                return

            if text == '📦 بکاپ‌گیری':
                try:
                    backup_files = []
                    
                    with open('users_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"users": db["users"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    backup_files.append(('users_backup.json', '👤 اطلاعات کاربران'))
                    
                    with open('plans_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"categories": db["categories"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    backup_files.append(('plans_backup.json', '📦 پلن‌ها'))
                    
                    with open('card_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"card": db["card"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    backup_files.append(('card_backup.json', '💳 کارت'))
                    
                    with open('texts_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"texts": db["texts"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    backup_files.append(('texts_backup.json', '📝 متن‌ها'))
                    
                    with open('menu_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"menu": db["menu_buttons"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    backup_files.append(('menu_backup.json', '📋 منو'))
                    
                    settings = {
                        "brand": db["brand"], 
                        "support": db["support"], 
                        "guide": db["guide"],
                        "testimonials_channel": db.get("testimonials_channel", ""),
                        "force_join": db["force_join"], 
                        "bot_status": db["bot_status"],
                        "date": str(datetime.now())
                    }
                    with open('settings_backup.json', 'w', encoding='utf-8') as f:
                        json.dump(settings, f, ensure_ascii=False, indent=4)
                    backup_files.append(('settings_backup.json', '⚙️ تنظیمات'))
                    
                    update.message.reply_text("📦 در حال آماده‌سازی بکاپ‌ها...")
                    
                    for filename, description in backup_files:
                        with open(filename, 'rb') as f:
                            context.bot.send_document(
                                chat_id=uid,
                                document=f,
                                filename=filename,
                                caption=f"📁 {description}\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                        os.remove(filename)
                    
                    update.message.reply_text("✅ بکاپ‌گیری با موفقیت انجام شد!")
                    
                except Exception as e:
                    logger.error(f"❌ Error in backup: {e}")
                    update.message.reply_text(f"❌ خطا در بکاپ‌گیری: {e}")
                return

            if text == '🔄 بازیابی بکاپ':
                user_data[uid] = {
                    'step': 'restore_waiting',
                    'restore_files': {},
                    'expected_file': 'users_backup.json'
                }
                msg = (
                    "🔄 **بازیابی بکاپ**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "لطفاً فایل‌ها را به ترتیب زیر ارسال کنید:\n\n"
                    "1️⃣ اول `users_backup.json` (اطلاعات کاربران)\n"
                    "2️⃣ بعد `plans_backup.json` (پلن‌ها)\n"
                    "3️⃣ بعد `card_backup.json` (کارت بانکی)\n"
                    "4️⃣ بعد `texts_backup.json` (متن‌ها)\n"
                    "5️⃣ بعد `menu_backup.json` (منوی اصلی)\n"
                    "6️⃣ آخر `settings_backup.json` (تنظیمات)\n\n"
                    "✅ **بعد از اتمام بازیابی، لطفاً ربات را یک بار ری‌استارت کنید.**"
                )
                update.message.reply_text(msg, parse_mode='Markdown')
                return

            if text == '📨 ارسال همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text("📨 پیام همگانی را بفرستید:", reply_markup=back_btn())
                return

            # ========== بخش افزودن پلن جدید ==========
            if text == '➕ پلن جدید':
                categories = list(db["categories"].keys())
                kb = [[c] for c in categories] + [['🔙 برگشت']]
                user_data[uid] = {'step': 'new_cat'}
                update.message.reply_text("📂 دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if step == 'new_cat' and text in db["categories"]:
                user_data[uid]['cat'] = text
                user_data[uid]['step'] = 'new_name'
                update.message.reply_text("📝 نام پلن را وارد کنید:", reply_markup=back_btn())
                return

            if step == 'new_name':
                user_data[uid]['name'] = text
                user_data[uid]['step'] = 'new_vol'
                update.message.reply_text("📦 حجم پلن را وارد کنید (مثال: 50GB):")
                return

            if step == 'new_vol':
                user_data[uid]['vol'] = text
                user_data[uid]['step'] = 'new_users'
                update.message.reply_text("👥 تعداد کاربران را وارد کنید (عدد یا 'نامحدود'):")
                return

            if step == 'new_users':
                if text.isdigit() or text == "نامحدود":
                    user_data[uid]['users'] = text if text == "نامحدود" else int(text)
                    user_data[uid]['step'] = 'new_days'
                    update.message.reply_text("⏳ مدت اعتبار را به روز وارد کنید (عدد یا 'نامحدود'):")
                else:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر یا کلمه 'نامحدود' وارد کنید!")
                return

            if step == 'new_days':
                if text.isdigit() or text == "نامحدود":
                    user_data[uid]['days'] = text if text == "نامحدود" else int(text)
                    user_data[uid]['step'] = 'new_price'
                    update.message.reply_text("💰 قیمت را به هزار تومان وارد کنید (عدد):")
                else:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر یا کلمه 'نامحدود' وارد کنید!")
                return

            if step == 'new_price':
                try:
                    price = int(text)
                    max_id = 0
                    for plans in db["categories"].values():
                        for p in plans:
                            if p["id"] > max_id:
                                max_id = p["id"]
                    
                    new_plan = {
                        "id": max_id + 1,
                        "name": user_data[uid]['name'],
                        "price": price,
                        "volume": user_data[uid]['vol'],
                        "days": user_data[uid]['days'],
                        "users": user_data[uid]['users']
                    }
                    
                    category = user_data[uid]['cat']
                    db["categories"][category].append(new_plan)
                    save_db(db)
                    
                    # نمایش اطلاعات پلن اضافه شده
                    users_display = new_plan['users'] if new_plan['users'] != "نامحدود" else "نامحدود"
                    days_display = new_plan['days'] if new_plan['days'] != "نامحدود" else "نامحدود"
                    
                    plan_info = (
                        f"✅ پلن جدید با موفقیت اضافه شد!\n\n"
                        f"📌 دسته: {category}\n"
                        f"📝 نام: {new_plan['name']}\n"
                        f"📦 حجم: {new_plan['volume']}\n"
                        f"👥 کاربران: {users_display}\n"
                        f"⏳ مدت: {days_display} روز\n"
                        f"💰 قیمت: {new_plan['price'] * 1000:,} تومان"
                    )
                    
                    update.message.reply_text(plan_info, reply_markup=get_admin_menu())
                    user_data[uid] = {}
                    
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
                return

            if text == '➖ حذف پلن':
                # این بخش در handle_cb هست
                pass

            # ========== بخش ویرایش پلن (کاملاً جداسازی شده با دیباگ) ==========
            if text == '✏️ ویرایش پلن':
                # این بخش در handle_cb هست
                pass

            if step == 'edit_plan_select_field':
                logger.info(f"✏️ کاربر {uid} در مرحله انتخاب فیلد ویرایش - متن: {text}")
                try:
                    plan = user_data[uid]['plan']
                    cat = user_data[uid]['cat']
                    
                    if text == 'نام':
                        logger.info(f"✏️ کاربر گزینه نام را انتخاب کرد")
                        user_data[uid]['edit_field'] = 'name'
                        user_data[uid]['step'] = 'edit_plan_enter_value'
                        update.message.reply_text(f"📝 نام جدید برای پلن '{plan['name']}' را وارد کنید:", reply_markup=back_btn())
                        return
                    
                    elif text == 'حجم':
                        logger.info(f"✏️ کاربر گزینه حجم را انتخاب کرد")
                        user_data[uid]['edit_field'] = 'volume'
                        user_data[uid]['step'] = 'edit_plan_enter_value'
                        update.message.reply_text(f"📦 حجم جدید برای پلن '{plan['name']}' (مثال: 50GB):", reply_markup=back_btn())
                        return
                    
                    elif text == 'کاربران':
                        logger.info(f"✏️ کاربر گزینه کاربران را انتخاب کرد")
                        user_data[uid]['edit_field'] = 'users'
                        user_data[uid]['step'] = 'edit_plan_enter_value'
                        update.message.reply_text(f"👥 تعداد کاربران جدید (عدد یا 'نامحدود'):", reply_markup=back_btn())
                        return
                    
                    elif text == 'مدت':
                        logger.info(f"✏️ کاربر گزینه مدت را انتخاب کرد")
                        user_data[uid]['edit_field'] = 'days'
                        user_data[uid]['step'] = 'edit_plan_enter_value'
                        update.message.reply_text(f"⏳ مدت اعتبار جدید (روز یا 'نامحدود'):", reply_markup=back_btn())
                        return
                    
                    elif text == 'قیمت':
                        logger.info(f"✏️ کاربر گزینه قیمت را انتخاب کرد")
                        user_data[uid]['edit_field'] = 'price'
                        user_data[uid]['step'] = 'edit_plan_enter_value'
                        update.message.reply_text(f"💰 قیمت جدید (هزار تومان):", reply_markup=back_btn())
                        return
                    
                    elif text == '🔙 برگشت':
                        logger.info(f"✏️ کاربر انصراف داد")
                        user_data[uid] = {}
                        update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu())
                        return
                    
                    else:
                        update.message.reply_text("❌ گزینه نامعتبر!", reply_markup=back_btn())
                        return
                        
                except Exception as e:
                    logger.error(f"❌ Error in edit_plan_select_field: {e}")
                    update.message.reply_text(f"❌ خطا: {e}")
                    return

            if step == 'edit_plan_enter_value':
                logger.info(f"✏️ کاربر {uid} در مرحله دریافت مقدار جدید - متن: {text}")
                try:
                    plan = user_data[uid]['plan']
                    cat = user_data[uid]['cat']
                    field = user_data[uid]['edit_field']
                    
                    found = False
                    for i, p in enumerate(db["categories"][cat]):
                        if p["id"] == plan["id"]:
                            found = True
                            logger.info(f"✏️ پلن پیدا شد: {p['name']}")
                            
                            if field == 'users':
                                if text.isdigit() or text == "نامحدود":
                                    db["categories"][cat][i][field] = text if text == "نامحدود" else int(text)
                                    save_db(db)
                                    
                                    users_display = db["categories"][cat][i]['users'] if db["categories"][cat][i]['users'] != "نامحدود" else "نامحدود"
                                    days_display = db["categories"][cat][i]['days'] if db["categories"][cat][i]['days'] != "نامحدود" else "نامحدود"
                                    
                                    result_msg = (
                                        f"✅ پلن با موفقیت ویرایش شد!\n\n"
                                        f"📌 دسته: {cat}\n"
                                        f"📝 نام: {db['categories'][cat][i]['name']}\n"
                                        f"📦 حجم: {db['categories'][cat][i]['volume']}\n"
                                        f"👥 کاربران: {users_display}\n"
                                        f"⏳ مدت: {days_display} روز\n"
                                        f"💰 قیمت: {db['categories'][cat][i]['price'] * 1000:,} تومان"
                                    )
                                    
                                    update.message.reply_text(result_msg, reply_markup=get_admin_menu())
                                    user_data[uid] = {}
                                    logger.info(f"✅ ویرایش کاربران با موفقیت انجام شد")
                                else:
                                    update.message.reply_text("❌ لطفاً عدد یا 'نامحدود' وارد کنید!")
                            
                            elif field == 'days':
                                if text.isdigit() or text == "نامحدود":
                                    db["categories"][cat][i][field] = text if text == "نامحدود" else int(text)
                                    save_db(db)
                                    
                                    users_display = db["categories"][cat][i]['users'] if db["categories"][cat][i]['users'] != "نامحدود" else "نامحدود"
                                    days_display = db["categories"][cat][i]['days'] if db["categories"][cat][i]['days'] != "نامحدود" else "نامحدود"
                                    
                                    result_msg = (
                                        f"✅ پلن با موفقیت ویرایش شد!\n\n"
                                        f"📌 دسته: {cat}\n"
                                        f"📝 نام: {db['categories'][cat][i]['name']}\n"
                                        f"📦 حجم: {db['categories'][cat][i]['volume']}\n"
                                        f"👥 کاربران: {users_display}\n"
                                        f"⏳ مدت: {days_display} روز\n"
                                        f"💰 قیمت: {db['categories'][cat][i]['price'] * 1000:,} تومان"
                                    )
                                    
                                    update.message.reply_text(result_msg, reply_markup=get_admin_menu())
                                    user_data[uid] = {}
                                    logger.info(f"✅ ویرایش مدت با موفقیت انجام شد")
                                else:
                                    update.message.reply_text("❌ لطفاً عدد یا 'نامحدود' وارد کنید!")
                            
                            elif field == 'price':
                                try:
                                    val = int(text)
                                    db["categories"][cat][i][field] = val
                                    save_db(db)
                                    
                                    users_display = db["categories"][cat][i]['users'] if db["categories"][cat][i]['users'] != "نامحدود" else "نامحدود"
                                    days_display = db["categories"][cat][i]['days'] if db["categories"][cat][i]['days'] != "نامحدود" else "نامحدود"
                                    
                                    result_msg = (
                                        f"✅ پلن با موفقیت ویرایش شد!\n\n"
                                        f"📌 دسته: {cat}\n"
                                        f"📝 نام: {db['categories'][cat][i]['name']}\n"
                                        f"📦 حجم: {db['categories'][cat][i]['volume']}\n"
                                        f"👥 کاربران: {users_display}\n"
                                        f"⏳ مدت: {days_display} روز\n"
                                        f"💰 قیمت: {db['categories'][cat][i]['price'] * 1000:,} تومان"
                                    )
                                    
                                    update.message.reply_text(result_msg, reply_markup=get_admin_menu())
                                    user_data[uid] = {}
                                    logger.info(f"✅ ویرایش قیمت با موفقیت انجام شد")
                                except:
                                    update.message.reply_text("❌ لطفاً عدد وارد کنید!")
                            
                            else:
                                db["categories"][cat][i][field] = text
                                save_db(db)
                                
                                users_display = db["categories"][cat][i]['users'] if db["categories"][cat][i]['users'] != "نامحدود" else "نامحدود"
                                days_display = db["categories"][cat][i]['days'] if db["categories"][cat][i]['days'] != "نامحدود" else "نامحدود"
                                
                                result_msg = (
                                    f"✅ پلن با موفقیت ویرایش شد!\n\n"
                                    f"📌 دسته: {cat}\n"
                                    f"📝 نام: {db['categories'][cat][i]['name']}\n"
                                    f"📦 حجم: {db['categories'][cat][i]['volume']}\n"
                                    f"👥 کاربران: {users_display}\n"
                                    f"⏳ مدت: {days_display} روز\n"
                                    f"💰 قیمت: {db['categories'][cat][i]['price'] * 1000:,} تومان"
                                )
                                
                                update.message.reply_text(result_msg, reply_markup=get_admin_menu())
                                user_data[uid] = {}
                                logger.info(f"✅ ویرایش {field} با موفقیت انجام شد")
                            break
                    
                    if not found:
                        logger.error(f"❌ پلن با id {plan['id']} در دسته {cat} پیدا نشد")
                        update.message.reply_text("❌ خطا در ویرایش پلن!")
                        user_data[uid] = {}
                        
                except Exception as e:
                    logger.error(f"❌ Error in edit_plan_enter_value: {e}")
                    update.message.reply_text(f"❌ خطا: {e}")
                return

            if step == 'card_num':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ شماره کارت ذخیره شد", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ شماره کارت باید 16 رقم باشد!")
                user_data[uid] = {}
                return

            if step == 'card_name':
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ نام صاحب کارت ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'support':
                db["support"] = text
                save_db(db)
                update.message.reply_text("✅ آیدی پشتیبان ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'brand':
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ نام برند ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'broadcast':
                success, failed = 0, 0
                for uid2 in db["users"]:
                    try:
                        context.bot.send_message(int(uid2), text)
                        success += 1
                    except:
                        failed += 1
                update.message.reply_text(f"✅ ارسال همگانی انجام شد.\n✓ موفق: {success}\n✗ ناموفق: {failed}")
                user_data[uid] = {}
                return

            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                vol = user_data[uid].get('vol', 'نامحدود')
                days = user_data[uid].get('days', 'نامحدود')
                
                service_record = f"🚀 {name} | {vol} | {datetime.now().strftime('%Y-%m-%d')}"
                if str(target) not in db["users"]:
                    db["users"][str(target)] = {"purchases": []}
                if "purchases" not in db["users"][str(target)]:
                    db["users"][str(target)]["purchases"] = []
                db["users"][str(target)]["purchases"].append(service_record)
                save_db(db)
                
                days_display = days if days != "نامحدود" else "نامحدود"
                
                msg = db["texts"]["config_sent"].format(
                    name=name,
                    days_text=days_display,
                    volume=vol,
                    config=update.message.text
                )
                
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📚 آموزش اتصال", url=f"https://t.me/{db['guide'].replace('@', '')}")
                ]])
                
                try:
                    context.bot.send_message(int(target), msg, parse_mode='HTML', reply_markup=btn)
                    update.message.reply_text("✅ کانفیگ ارسال شد.")
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
                
                user_data[uid] = {}
                return

        if step == 'wait_name':
            user_data[uid]['account'] = text
            p = user_data[uid]['plan']
            
            price_toman = p['price'] * 1000
            users_text = f"👥 {p['users']} کاربره" if p['users'] != "نامحدود" and p['users'] > 1 else "👤 تک کاربره"
            if p['users'] == "نامحدود":
                users_text = "👥 نامحدود کاربر"
            days_text = "نامحدود" if p['days'] == "نامحدود" else f"{p['days']} روز"
            
            msg = db["texts"]["payment_info"].format(
                account=text,
                plan_name=p['name'],
                volume=p['volume'],
                users_text=users_text,
                days_text=days_text,
                price=price_toman,
                card_number=db['card']['number'],
                card_name=db['card']['name']
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="receipt"),
                InlineKeyboardButton(texts["back_button"], callback_data="back_to_categories")
            ]])
            
            update.message.reply_text(msg, parse_mode='HTML', reply_markup=btn)

    except Exception as e:
        logger.error(f"Error in handle_msg: {e}")
        logger.error(traceback.format_exc())
        try:
            if update and update.message:
                update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

def handle_cb(update, context):
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        query.answer()
        logger.info(f"🔔 کالبک از {uid}: {query.data}")

        if query.data == "join_check":
            if check_join(uid, context):
                query.message.delete()
                welcome = db["texts"]["welcome"].format(brand=db["brand"])
                context.bot.send_message(uid, welcome, reply_markup=get_main_menu(uid))
            else:
                query.message.reply_text("❌ شما هنوز عضو کانال نشده‌اید!")
            return

        if query.data == "back_to_main":
            query.message.delete()
            welcome = db["texts"]["welcome"].format(brand=db["brand"])
            context.bot.send_message(uid, welcome, reply_markup=get_main_menu(uid))
            return

        if query.data == "back_to_admin":
            query.message.delete()
            context.bot.send_message(uid, "🛠 پنل مدیریت:", reply_markup=get_admin_menu())
            return

        if query.data == "back_to_categories":
            query.message.delete()
            categories = list(db["categories"].keys())
            keyboard = []
            for cat in categories:
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
            keyboard.append([InlineKeyboardButton(db["texts"]["back_button"], callback_data="back_to_main")])
            context.bot.send_message(uid, "📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if query.data.startswith("cat_"):
            cat = query.data[4:]
            plans = db["categories"].get(cat, [])
            if not plans:
                query.message.reply_text("❌ این دسته‌بندی پلنی ندارد.")
                return
            
            keyboard = []
            for p in plans:
                price_toman = p['price'] * 1000
                users_display = p['users'] if p['users'] != "نامحدود" else "نامحدود"
                days_display = p['days'] if p['days'] != "نامحدود" else "نامحدود"
                
                btn_text = f"{p['name']} | {p['volume']} | 👥 {users_display} | ⏳ {days_display} روز | {price_toman:,} تومان"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{p['id']}")])
            
            keyboard.append([InlineKeyboardButton(db["texts"]["back_button"], callback_data="back_to_categories")])
            query.message.edit_text(f"📦 {cat}\nلطفاً پلن مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if query.data.startswith("buy_"):
            try:
                plan_id = int(query.data.split("_")[1])
                plan = None
                for cat, plans in db["categories"].items():
                    for p in plans:
                        if p["id"] == plan_id:
                            plan = p
                            break
                    if plan:
                        break
                if plan:
                    user_data[uid] = {'step': 'wait_name', 'plan': plan}
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(db["texts"]["back_button"], callback_data="back_to_categories")
                    ]])
                    query.message.edit_text("📝 لطفاً نام دلخواه برای اکانت خود وارد کنید:", reply_markup=keyboard)
                else:
                    query.message.reply_text("❌ پلن مورد نظر یافت نشد.")
            except Exception as e:
                query.message.reply_text(f"❌ خطا: {e}")
            return

        if query.data == "receipt":
            if uid in user_data and 'plan' in user_data[uid] and 'account' in user_data[uid]:
                user_data[uid]['step'] = 'wait_photo'
                query.message.reply_text("📸 لطفاً عکس فیش واریزی را ارسال کنید:", reply_markup=back_btn())
            else:
                query.message.reply_text("❌ اطلاعات خرید یافت نشد.")
                if uid in user_data:
                    del user_data[uid]
            return

        if query.data.startswith("renew_"):
            try:
                index = int(query.data.split("_")[1])
                purchases = db["users"][uid].get("purchases", [])
                
                if index < len(purchases):
                    service = purchases[index]
                    logger.info(f"🔄 تلاش برای تمدید سرویس: {service}")
                    
                    service_volume = None
                    volume_list = ["10GB", "20GB", "30GB", "40GB", "50GB", "60GB", "100GB"]
                    
                    for vol in volume_list:
                        if vol in service:
                            service_volume = vol
                            break
                    
                    similar_plan = None
                    
                    if service_volume:
                        for cat, plans in db["categories"].items():
                            for p in plans:
                                if p['volume'] == service_volume:
                                    similar_plan = p
                                    logger.info(f"✅ پلن مشابه با حجم پیدا شد: {p['name']}")
                                    break
                            if similar_plan:
                                break
                    
                    if not similar_plan:
                        for cat, plans in db["categories"].items():
                            for p in plans:
                                for word in p['name'].split():
                                    if len(word) > 3 and word in service:
                                        similar_plan = p
                                        logger.info(f"✅ پلن مشابه با اسم پیدا شد: {p['name']}")
                                        break
                                if similar_plan:
                                    break
                            if similar_plan:
                                break
                    
                    if not similar_plan:
                        all_plans = []
                        for cat, plans in db["categories"].items():
                            all_plans.extend(plans)
                        
                        if all_plans:
                            similar_plan = min(all_plans, key=lambda x: x['price'])
                            logger.info(f"✅ ارزان‌ترین پلن به عنوان پیش‌فرض انتخاب شد: {similar_plan['name']}")
                    
                    if similar_plan:
                        user_data[uid] = {'step': 'wait_name', 'plan': similar_plan}
                        keyboard = InlineKeyboardMarkup([[
                            InlineKeyboardButton(db["texts"]["back_button"], callback_data="back_to_categories")
                        ]])
                        
                        price_toman = similar_plan['price'] * 1000
                        service_short = service[:50] + "..." if len(service) > 50 else service
                        
                        msg = (
                            f"🔄 **تمدید سرویس**\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📌 سرویس قبلی:\n`{service_short}`\n\n"
                            f"📦 پلن پیشنهادی: {similar_plan['name']}\n"
                            f"💰 قیمت: {price_toman:,} تومان\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📝 لطفاً نام اکانت را وارد کنید:"
                        )
                        
                        query.message.edit_text(msg, parse_mode='Markdown', reply_markup=keyboard)
                    else:
                        query.message.reply_text(
                            "❌ پلن مشابه برای تمدید یافت نشد.\n"
                            "لطفاً از خرید جدید استفاده کنید یا با پشتیبانی تماس بگیرید."
                        )
                        if uid in user_data:
                            del user_data[uid]
                else:
                    query.message.reply_text("❌ سرویس مورد نظر یافت نشد.")
            except Exception as e:
                logger.error(f"❌ Error in renew: {e}")
                query.message.reply_text(f"❌ خطا در تمدید: {e}")
            return

        if query.data.startswith("del_menu_"):
            if str(uid) == str(ADMIN_ID):
                index = int(query.data.split("_")[2])
                if 0 <= index < len(db["menu_buttons"]):
                    deleted = db["menu_buttons"].pop(index)
                    save_db(db)
                    query.message.edit_text(f"✅ دکمه '{deleted['text']}' حذف شد.")
                else:
                    query.message.edit_text("❌ خطا در حذف دکمه.")
            return

        if query.data.startswith("edit_menu_"):
            if str(uid) == str(ADMIN_ID):
                index = int(query.data.split("_")[2])
                user_data[uid] = {'step': 'edit_menu', 'menu_index': index}
                query.message.edit_text("📝 متن جدید برای دکمه را بفرستید:", reply_markup=None)
            return

        if query.data.startswith("del_cat_"):
            if str(uid) == str(ADMIN_ID):
                cat = query.data[8:]
                if cat in db["categories"]:
                    if len(db["categories"][cat]) == 0:
                        del db["categories"][cat]
                        save_db(db)
                        query.message.edit_text(f"✅ دسته‌بندی {cat} حذف شد.")
                    else:
                        query.message.edit_text("❌ این دسته‌بندی دارای پلن است. ابتدا پلن‌ها را حذف کنید.")
                else:
                    query.message.edit_text("❌ دسته‌بندی یافت نشد.")
            return

        if query.data.startswith("edit_cat_"):
            if str(uid) == str(ADMIN_ID):
                cat = query.data[9:]
                user_data[uid] = {'step': 'edit_category', 'old_cat': cat}
                query.message.edit_text(f"📝 نام جدید برای دسته‌بندی '{cat}' را بفرستید:", reply_markup=None)
            return

        if query.data.startswith("del_"):
            if str(uid) == str(ADMIN_ID):
                try:
                    plan_id = int(query.data.split("_")[1])
                    deleted = False
                    for cat, plans in db["categories"].items():
                        for i, p in enumerate(plans):
                            if p["id"] == plan_id:
                                del plans[i]
                                deleted = True
                                break
                        if deleted:
                            break
                    if deleted:
                        save_db(db)
                        query.message.edit_text("✅ پلن با موفقیت حذف شد.")
                    else:
                        query.message.edit_text("❌ پلن یافت نشد.")
                except Exception as e:
                    query.message.edit_text(f"❌ خطا: {e}")
            return

        if query.data.startswith("edit_plan_"):
            if str(uid) == str(ADMIN_ID):
                try:
                    plan_id = int(query.data.split("_")[2])
                    
                    for cat, plans in db["categories"].items():
                        for p in plans:
                            if p["id"] == plan_id:
                                logger.info(f"✏️ کاربر {uid} شروع ویرایش پلن {p['name']}")
                                user_data[uid] = {'step': 'edit_plan_select_field', 'plan': p, 'cat': cat}
                                
                                keyboard = [
                                    ['نام', 'حجم', 'کاربران'],
                                    ['مدت', 'قیمت'],
                                    ['🔙 برگشت']
                                ]
                                query.message.edit_text(
                                    f"✏️ ویرایش پلن {p['name']}\nچه چیزی را ویرایش کنیم؟",
                                    reply_markup=None
                                )
                                context.bot.send_message(
                                    uid,
                                    "گزینه مورد نظر را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                                )
                                return
                    
                    query.message.edit_text("❌ پلن یافت نشد.")
                except Exception as e:
                    query.message.edit_text(f"❌ خطا: {e}")
            return

        if query.data.startswith("test_"):
            if str(uid) == str(ADMIN_ID):
                try:
                    parts = query.data.split("_")
                    if len(parts) >= 3:
                        target = parts[1]
                        name = parts[2]
                        user_data[uid] = {
                            'step': 'send_config',
                            'target': target,
                            'name': f"تست {name}",
                            'vol': '۳ ساعت',
                            'days': '۳'
                        }
                        context.bot.send_message(uid, f"📨 لطفاً کانفیگ تست برای {name} را ارسال کنید:")
                        query.message.edit_reply_markup(reply_markup=None)
                except Exception as e:
                    context.bot.send_message(uid, f"❌ خطا: {e}")
            return

        if query.data.startswith("send_"):
            if str(uid) == str(ADMIN_ID):
                try:
                    target = query.data.split("_")[1]
                    caption = query.message.caption or ""
                    lines = caption.split('\n')
                    name = "کاربر"
                    vol = "نامحدود"
                    for line in lines:
                        if "اکانت" in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                name = parts[1].strip()
                        elif "📦" in line and "حجم" not in line:
                            vol = line.split('📦')[-1].strip()
                    user_data[uid] = {
                        'step': 'send_config',
                        'target': target,
                        'name': name,
                        'vol': vol,
                        'days': '۳۰'
                    }
                    context.bot.send_message(uid, f"📨 لطفاً کانفیگ {name} را ارسال کنید:")
                    query.message.edit_reply_markup(reply_markup=None)
                except Exception as e:
                    context.bot.send_message(uid, f"❌ خطا: {e}")
            return

    except Exception as e:
        logger.error(f"Error in handle_cb: {e}")
        logger.error(traceback.format_exc())
        try:
            query.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

def handle_photo(update, context):
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get('step') == 'wait_photo':
            if 'plan' not in user_data[uid] or 'account' not in user_data[uid]:
                update.message.reply_text("❌ اطلاعات خرید یافت نشد.")
                return
            
            p = user_data[uid]['plan']
            account_name = user_data[uid]['account']
            price_toman = p['price'] * 1000
            users_display = p['users'] if p['users'] != "نامحدود" else "نامحدود"
            days_display = p['days'] if p['days'] != "نامحدود" else "نامحدود"
            
            caption = (
                f"💰 فیش واریزی جدید\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 کاربر: {update.effective_user.first_name}\n"
                f"🆔 آیدی: {uid}\n"
                f"👤 یوزرنیم: @{update.effective_user.username or 'ندارد'}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 پلن: {p['name']}\n"
                f"📊 حجم: {p['volume']}\n"
                f"👥 کاربران: {users_display}\n"
                f"⏳ مدت: {days_display} روز\n"
                f"💰 مبلغ: {price_toman:,} تومان\n"
                f"👤 نام اکانت: {account_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"send_{uid}")
            ]])
            
            context.bot.send_photo(
                ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=btn
            )
            
            update.message.reply_text(
                "✅ فیش شما ارسال شد.\nبه زودی سرویس ارسال می‌شود.",
                reply_markup=get_main_menu(uid)
            )
            
            if uid in user_data:
                del user_data[uid]

    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        update.message.reply_text("❌ خطایی رخ داد.")

def handle_document(update, context):
    try:
        uid = str(update.effective_user.id)
        
        if uid != str(ADMIN_ID):
            update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
            return
        
        step_data = user_data.get(uid, {})
        if step_data.get('step') != 'restore_waiting':
            return
        
        document = update.message.document
        if not document.file_name.endswith('.json'):
            update.message.reply_text("❌ لطفاً فایل JSON معتبر بفرستید.")
            return
        
        expected_file = step_data.get('expected_file')
        if document.file_name != expected_file:
            update.message.reply_text(
                f"❌ لطفاً فایل {expected_file} رو بفرستید.\n"
                f"شما {document.file_name} رو ارسال کردید."
            )
            return
        
        file = context.bot.get_file(document.file_id)
        file.download(document.file_name)
        
        with open(document.file_name, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        if document.file_name == 'users_backup.json':
            if "users" in backup_data:
                db["users"] = backup_data["users"]
            user_data[uid]['restore_files']['users'] = True
            next_file = 'plans_backup.json'
            msg = "✅ اطلاعات کاربران بازیابی شد.\n📁 حالا فایل `plans_backup.json` رو بفرستید."
        
        elif document.file_name == 'plans_backup.json':
            if "categories" in backup_data:
                db["categories"] = backup_data["categories"]
            user_data[uid]['restore_files']['plans'] = True
            next_file = 'card_backup.json'
            msg = "✅ پلن‌ها بازیابی شدن.\n💳 حالا فایل `card_backup.json` رو بفرستید."
        
        elif document.file_name == 'card_backup.json':
            if "card" in backup_data:
                db["card"] = backup_data["card"]
            user_data[uid]['restore_files']['card'] = True
            next_file = 'texts_backup.json'
            msg = "✅ اطلاعات کارت بازیابی شد.\n📝 حالا فایل `texts_backup.json` رو بفرستید."
        
        elif document.file_name == 'texts_backup.json':
            if "texts" in backup_data:
                db["texts"] = backup_data["texts"]
            user_data[uid]['restore_files']['texts'] = True
            next_file = 'menu_backup.json'
            msg = "✅ متن‌ها بازیابی شدن.\n📋 حالا فایل `menu_backup.json` رو بفرستید."
        
        elif document.file_name == 'menu_backup.json':
            if "menu" in backup_data:
                db["menu_buttons"] = backup_data["menu"]
            user_data[uid]['restore_files']['menu'] = True
            next_file = 'settings_backup.json'
            msg = "✅ منوی اصلی بازیابی شد.\n⚙️ حالا فایل `settings_backup.json` رو بفرستید."
        
        elif document.file_name == 'settings_backup.json':
            if "brand" in backup_data:
                db["brand"] = backup_data["brand"]
            if "support" in backup_data:
                db["support"] = backup_data["support"]
            if "guide" in backup_data:
                db["guide"] = backup_data["guide"]
            if "testimonials_channel" in backup_data:
                db["testimonials_channel"] = backup_data["testimonials_channel"]
            if "force_join" in backup_data:
                db["force_join"] = backup_data["force_join"]
            if "bot_status" in backup_data:
                db["bot_status"] = backup_data["bot_status"]
            user_data[uid]['restore_files']['settings'] = True
            next_file = 'COMPLETE'
            msg = "✅ **بازیابی با موفقیت کامل شد!**\n\n🔴 **نکته مهم:** لطفاً ربات را از طریق Railway یک بار ری‌استارت کنید."
        
        os.remove(document.file_name)
        
        if next_file == 'COMPLETE':
            save_db(db)
            
            update.message.reply_text(msg, parse_mode='Markdown')
            
            user_data[uid] = {}
            logger.info("✅ Backup restored successfully. Manual restart required.")
            
            return
        else:
            user_data[uid]['expected_file'] = next_file
            update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Error in handle_document: {e}")
        update.message.reply_text(f"❌ خطا در بازیابی: {e}")

def main():
    try:
        logger.info("🚀 Starting bot...")
        
        web_thread = Thread(target=run_web, daemon=True)
        web_thread.start()
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(MessageHandler(Filters.document, handle_document))
        dp.add_handler(CallbackQueryHandler(handle_cb))
        
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()