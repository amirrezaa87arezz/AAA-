import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from datetime import datetime
import traceback

# --- تنظیمات لاگینگ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وب سرور (برای Health Check) ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "✅ VPN Bot is Running!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- توکن و آیدی ادمین اصلی ---
TOKEN = '8305364438:AAGAT39wGQey9tzxMVafEiRRXz1eGNvpfhY'
MAIN_ADMIN_ID = 1374345602  # ادمین اصلی (سوپر ادمین)

# --- مسیر دیتابیس ---
DB_FILE = 'data.json'

# --- سطوح دسترسی ادمین ---
PERMISSIONS = {
    "manage_admins": "👑 مدیریت ادمین‌ها",
    "manage_plans": "➕ مدیریت پلن‌ها",
    "manage_card": "💳 مدیریت کارت",
    "manage_texts": "📝 مدیریت متن‌ها",
    "manage_support": "👤 مدیریت پشتیبان",
    "manage_channel": "📢 مدیریت کانال",
    "manage_force_join": "🔒 مدیریت عضویت",
    "manage_brand": "🏷 مدیریت برند",
    "manage_status": "🔛 مدیریت وضعیت",
    "view_stats": "📊 مشاهده آمار",
    "send_broadcast": "📨 ارسال همگانی",
    "manage_categories": "➕ مدیریت دسته‌بندی",
    "delete_categories": "➖ حذف دسته‌بندی",
    "view_users": "👤 مشاهده کاربران"
}

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

# --- متن‌های پیش‌فرض برای همه بخش‌ها ---
DEFAULT_TEXTS = {
    # متن‌های اصلی
    "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته\n✅ نصب آسان",
    "support": "🆘 پشتیبانی: {support}",
    "guide": "📚 آموزش: {guide}",
    "test": "🎁 درخواست تست شما ثبت شد",
    "force": "🔒 برای استفاده از ربات باید در کانال زیر عضو شوید:\n{link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید.",
    "invite": "🤝 لینک دعوت شما:\n{link}\n\nبه ازای هر دعوت 1 روز هدیه",
    "payment_info": "💳 اطلاعات پرداخت\n━━━━━━━━━━━━━━\n👤 نام اکانت: {account}\n📦 پلن: {plan_name}\n📊 حجم: {volume}\n👥 {users_text}\n⏳ مدت: {days} روز\n💰 مبلغ: {price:,} تومان\n━━━━━━━━━━━━━━\n💳 شماره کارت:\n<code>{card_number}</code>\n👤 {card_name}\n━━━━━━━━━━━━━━\nپس از واریز، عکس فیش را بفرستید",
    "maintenance": "🔧 ربات در حال تعمیرات است. لطفاً بعداً مراجعه کنید.",
    
    # متن دکمه‌های منوی اصلی
    "btn_buy": "💰 خرید اشتراک",
    "btn_test": "🎁 تست رایگان",
    "btn_services": "📂 سرویس‌ها",
    "btn_renew": "⏳ تمدید",
    "btn_profile": "👤 مشخصات من",
    "btn_support": "👤 پشتیبانی",
    "btn_guide": "📚 آموزش",
    "btn_invite": "🤝 دعوت دوستان",
    "btn_admin": "⚙️ مدیریت",
    
    # متن دسته‌بندی‌ها
    "cat_powerful": "🚀 قوی",
    "cat_economy": "💎 ارزان",
    "cat_value": "🎯 به صرفه",
    "cat_multi": "👥 چند کاربره"
}

def load_db():
    """بارگذاری دیتابیس از فایل"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info("✅ Database loaded successfully")
                
                # اضافه کردن فیلدهای جدید اگر وجود نداشتند
                if "force_join" not in data:
                    data["force_join"] = {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""}
                if "bot_status" not in data:
                    data["bot_status"] = {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]}
                if "admins" not in data:
                    data["admins"] = {str(MAIN_ADMIN_ID): list(PERMISSIONS.keys())}  # ادمین اصلی همه دسترسی‌ها رو داره
                if "categories" not in data or not data["categories"]:
                    data["categories"] = DEFAULT_PLANS.copy()
                if "texts" not in data:
                    data["texts"] = DEFAULT_TEXTS.copy()
                else:
                    # اضافه کردن کلیدهای جدید به texts اگر نبودن
                    for key, value in DEFAULT_TEXTS.items():
                        if key not in data["texts"]:
                            data["texts"][key] = value
                
                return data
    except Exception as e:
        logger.error(f"❌ Error loading database: {e}")
    
    # دیتابیس پیش‌فرض
    logger.info("📁 Creating default database")
    return {
        "users": {},
        "brand": "تک نت وی‌پی‌ان",
        "card": {
            "number": "6277601368776066",
            "name": "محمد رضوانی"
        },
        "support": "@Support_Admin",
        "guide": "@Guide_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "force_join": {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""},
        "bot_status": {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]},
        "admins": {str(MAIN_ADMIN_ID): list(PERMISSIONS.keys())},
        "texts": DEFAULT_TEXTS.copy()
    }

def save_db(data):
    """ذخیره دیتابیس در فایل"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("💾 Database saved")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving database: {e}")
        return False

# بارگذاری دیتابیس
db = load_db()
user_data = {}

# --- بررسی دسترسی ادمین ---
def has_permission(admin_id, permission):
    """بررسی اینکه آیا ادمین دسترسی خاصی دارد یا نه"""
    if str(admin_id) == str(MAIN_ADMIN_ID):
        return True  # ادمین اصلی همه دسترسی‌ها را دارد
    admins = db.get("admins", {})
    perms = admins.get(str(admin_id), [])
    return permission in perms

# --- منوها ---
def get_main_menu(uid):
    """منوی اصلی کاربر"""
    texts = db["texts"]
    kb = [
        [texts["btn_buy"], texts["btn_test"]],
        [texts["btn_services"], texts["btn_renew"]],
        [texts["btn_profile"], texts["btn_support"]],
        [texts["btn_guide"], texts["btn_invite"]]
    ]
    if str(uid) == str(MAIN_ADMIN_ID) or str(uid) in db.get("admins", {}):
        kb.append([texts["btn_admin"]])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    """کیبورد برگشت"""
    return ReplyKeyboardMarkup([['🔙 برگشت']], resize_keyboard=True)

def get_admin_menu(uid):
    """منوی مدیریت بر اساس دسترسی‌ها"""
    kb = []
    
    if has_permission(uid, "manage_admins"):
        kb.append(['👥 مدیریت ادمین‌ها'])
    
    if has_permission(uid, "manage_plans"):
        kb.extend([['➕ پلن جدید', '➖ حذف پلن'], ['✏️ ویرایش پلن']])
    
    if has_permission(uid, "manage_card"):
        kb.append(['💳 ویرایش کارت'])
    
    if has_permission(uid, "manage_texts"):
        kb.append(['📝 ویرایش متن‌ها'])
    
    if has_permission(uid, "manage_support"):
        kb.append(['👤 ویرایش پشتیبان'])
    
    if has_permission(uid, "manage_channel"):
        kb.append(['📢 ویرایش کانال'])
    
    if has_permission(uid, "manage_force_join"):
        kb.append(['🔒 عضویت اجباری'])
    
    if has_permission(uid, "manage_brand"):
        kb.append(['🏷 ویرایش برند'])
    
    if has_permission(uid, "manage_status"):
        kb.append(['🔛 وضعیت ربات'])
    
    if has_permission(uid, "view_stats"):
        kb.append(['📊 آمار'])
    
    if has_permission(uid, "send_broadcast"):
        kb.append(['📨 ارسال همگانی'])
    
    if has_permission(uid, "manage_categories"):
        kb.append(['➕ دسته جدید'])
    
    if has_permission(uid, "delete_categories"):
        kb.append(['➖ حذف دسته'])
    
    if has_permission(uid, "view_users"):
        kb.append(['👤 کاربران'])
    
    kb.append(['🔙 برگشت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- بررسی عضویت اجباری ---
def check_join(user_id, context):
    """بررسی عضویت کاربر در کانال"""
    if not db["force_join"]["enabled"]:
        return True
    
    channel_id = db["force_join"].get("channel_id", "")
    channel_username = db["force_join"].get("channel_username", "")
    
    if not channel_id and not channel_username:
        return True
    
    # امتحان با آیدی عددی
    if channel_id:
        try:
            member = context.bot.get_chat_member(
                chat_id=int(channel_id),
                user_id=int(user_id)
            )
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    # امتحان با یوزرنیم
    if channel_username:
        try:
            member = context.bot.get_chat_member(
                chat_id=channel_username,
                user_id=int(user_id)
            )
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    return False

# --- شروع ربات ---
def start(update, context):
    """هندلر دستور /start"""
    try:
        uid = str(update.effective_user.id)
        
        # ثبت کاربر جدید
        if uid not in db["users"]:
            db["users"][uid] = {
                "purchases": [],
                "tests": [],
                "test_count": 0,
                "invited_by": None,
                "invited_users": [],
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            save_db(db)
        
        user_data[uid] = {}
        
        # بررسی وضعیت ربات
        if not db["bot_status"]["enabled"]:
            update.message.reply_text(db["bot_status"]["message"])
            return
        
        # بررسی عضویت اجباری
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
            if not check_join(uid, context):
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                msg = db["texts"]["force"].format(link=db["force_join"]["channel_link"])
                update.message.reply_text(msg, reply_markup=btn)
                return
        
        # خوش‌آمدگویی
        welcome = db["texts"]["welcome"].format(brand=db["brand"])
        update.message.reply_text(welcome, reply_markup=get_main_menu(uid))
        
    except Exception as e:
        logger.error(f"Error in start: {e}")
        update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت پیام‌ها ---
def handle_msg(update, context):
    try:
        text = update.message.text
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')

        # بررسی وضعیت ربات
        if not db["bot_status"]["enabled"] and str(uid) != str(MAIN_ADMIN_ID) and not has_permission(uid, "manage_status"):
            update.message.reply_text(db["bot_status"]["message"])
            return

        # بررسی عضویت اجباری برای همه پیام‌ها
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
            if not check_join(uid, context) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                update.message.reply_text(
                    db["texts"]["force"].format(link=db["force_join"]["channel_link"]),
                    reply_markup=btn
                )
                return

        # برگشت به منوی اصلی
        if text == '🔙 برگشت':
            user_data[uid] = {}
            start(update, context)
            return

        # --- دستورات اسلش ---
        if text == '/start':
            start(update, context)
            return
        elif text == '/buy' or text == '💰 خرید اشتراک':
            text = db["texts"]["btn_buy"]
        elif text == '/test' or text == '🎁 تست رایگان':
            text = db["texts"]["btn_test"]
        elif text == '/services' or text == '📂 سرویس‌ها':
            text = db["texts"]["btn_services"]
        elif text == '/renew' or text == '⏳ تمدید':
            text = db["texts"]["btn_renew"]
        elif text == '/profile' or text == '👤 مشخصات من':
            text = db["texts"]["btn_profile"]
        elif text == '/support' or text == '👤 پشتیبانی':
            text = db["texts"]["btn_support"]
        elif text == '/guide' or text == '📚 آموزش':
            text = db["texts"]["btn_guide"]
        elif text == '/invite' or text == '🤝 دعوت دوستان':
            text = db["texts"]["btn_invite"]
        elif text == '/admin' or text == '⚙️ مدیریت':
            if str(uid) == str(MAIN_ADMIN_ID) or str(uid) in db.get("admins", {}):
                text = db["texts"]["btn_admin"]

        # --- تست رایگان ---
        if text == db["texts"]["btn_test"]:
            if db["users"][uid]["test_count"] >= 1:
                update.message.reply_text("❌ شما قبلاً یک بار تست دریافت کرده‌اید و امکان دریافت تست مجدد وجود ندارد.")
                return
            
            db["users"][uid]["test_count"] += 1
            db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
            save_db(db)
            
            update.message.reply_text(db["texts"]["test"])
            
            # اطلاع به ادمین‌ها
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال تست", callback_data=f"test_{uid}_{name}")
            ]])
            
            admin_msg = f"🎁 درخواست تست جدید\n👤 {name}\n🆔 {uid}"
            
            # ارسال به همه ادمین‌ها
            for admin_id in db.get("admins", {}):
                try:
                    context.bot.send_message(int(admin_id), admin_msg, reply_markup=btn)
                except:
                    pass
            context.bot.send_message(MAIN_ADMIN_ID, admin_msg, reply_markup=btn)
            return

        # --- مشخصات کاربر ---
        if text == db["texts"]["btn_profile"]:
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
                f"👤 یوزرنیم: @{update.effective_user.username}\n"
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

        # --- سرویس‌ها ---
        if text == db["texts"]["btn_services"]:
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

        # --- تمدید سرویس ---
        if text == db["texts"]["btn_renew"]:
            purchases = db["users"][uid].get("purchases", [])
            if not purchases:
                update.message.reply_text("❌ شما سرویسی برای تمدید ندارید.")
                return
            
            keyboard = []
            for i, p in enumerate(purchases[-5:]):
                keyboard.append([InlineKeyboardButton(
                    f"🔄 {p[:30]}...",
                    callback_data=f"renew_{i}"
                )])
            update.message.reply_text(
                "🔁 سرویس مورد نظر برای تمدید را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- پشتیبانی ---
        if text == db["texts"]["btn_support"]:
            update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
            return

        # --- آموزش ---
        if text == db["texts"]["btn_guide"]:
            update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
            return

        # --- دعوت دوستان ---
        if text == db["texts"]["btn_invite"]:
            bot_username = context.bot.get_me().username
            link = f"https://t.me/{bot_username}?start={uid}"
            msg = db["texts"]["invite"].format(link=link)
            update.message.reply_text(msg)
            return

        # --- خرید اشتراک (نمایش دسته‌بندی‌ها به صورت شیشه‌ای) ---
        if text == db["texts"]["btn_buy"]:
            categories = list(db["categories"].keys())
            keyboard = []
            for cat in categories:
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
            
            update.message.reply_text(
                "📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- مدیریت (فقط برای ادمین‌ها) ---
        if (str(uid) == str(MAIN_ADMIN_ID) or str(uid) in db.get("admins", {})) and text == db["texts"]["btn_admin"]:
            update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu(uid))
            return

        # --- بخش‌های مدیریت ---
        if str(uid) == str(MAIN_ADMIN_ID) or str(uid) in db.get("admins", {}):
            
            # --- مدیریت ادمین‌ها ---
            if text == '👥 مدیریت ادمین‌ها' and has_permission(uid, "manage_admins"):
                keyboard = [
                    ['➕ افزودن ادمین', '➖ حذف ادمین'],
                    ['🔙 برگشت']
                ]
                
                # نمایش لیست ادمین‌ها
                admins_list = "📋 لیست ادمین‌ها:\n"
                for admin_id, perms in db.get("admins", {}).items():
                    if admin_id == str(MAIN_ADMIN_ID):
                        admins_list += f"👑 {admin_id} (ادمین اصلی)\n"
                    else:
                        admins_list += f"👤 {admin_id}\n"
                
                update.message.reply_text(
                    admins_list,
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '➕ افزودن ادمین' and has_permission(uid, "manage_admins"):
                user_data[uid] = {'step': 'add_admin_id'}
                update.message.reply_text(
                    "🆔 آیدی عددی ادمین جدید را بفرستید:",
                    reply_markup=back_btn()
                )
                return

            if step == 'add_admin_id' and has_permission(uid, "manage_admins"):
                if text.isdigit():
                    user_data[uid]['new_admin_id'] = text
                    user_data[uid]['step'] = 'add_admin_perms'
                    
                    # نمایش لیست دسترسی‌ها
                    keyboard = []
                    for perm_key, perm_name in PERMISSIONS.items():
                        keyboard.append([InlineKeyboardButton(perm_name, callback_data=f"perm_{perm_key}")])
                    keyboard.append([InlineKeyboardButton("✅ تایید و ذخیره", callback_data="save_admin")])
                    
                    update.message.reply_text(
                        "✅ دسترسی‌های مورد نظر را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ لطفاً یک آیدی عددی معتبر بفرستید!")
                return

            if text == '➖ حذف ادمین' and has_permission(uid, "manage_admins"):
                keyboard = []
                for admin_id in db.get("admins", {}):
                    if admin_id != str(MAIN_ADMIN_ID):  # نمی‌شود ادمین اصلی را حذف کرد
                        keyboard.append([InlineKeyboardButton(f"❌ {admin_id}", callback_data=f"del_admin_{admin_id}")])
                
                if keyboard:
                    update.message.reply_text(
                        "🗑 ادمین مورد نظر را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ هیچ ادمینی برای حذف وجود ندارد.")
                return

            # --- ویرایش کارت ---
            if text == '💳 ویرایش کارت' and has_permission(uid, "manage_card"):
                keyboard = [
                    ['شماره کارت', 'نام صاحب کارت'],
                    ['🔙 برگشت']
                ]
                current = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(
                    current,
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == 'شماره کارت' and has_permission(uid, "manage_card"):
                user_data[uid] = {'step': 'card_num'}
                update.message.reply_text("💳 شماره کارت 16 رقمی را بفرستید:", reply_markup=back_btn())
                return

            if text == 'نام صاحب کارت' and has_permission(uid, "manage_card"):
                user_data[uid] = {'step': 'card_name'}
                update.message.reply_text("👤 نام صاحب کارت را بفرستید:", reply_markup=back_btn())
                return

            # --- ویرایش پشتیبان ---
            if text == '👤 ویرایش پشتیبان' and has_permission(uid, "manage_support"):
                user_data[uid] = {'step': 'support'}
                update.message.reply_text("👤 آیدی پشتیبان را بفرستید (مثال: @Support_Admin):", reply_markup=back_btn())
                return

            # --- ویرایش کانال آموزش ---
            if text == '📢 ویرایش کانال' and has_permission(uid, "manage_channel"):
                user_data[uid] = {'step': 'guide'}
                update.message.reply_text("📢 آیدی کانال آموزش را بفرستید (مثال: @Guide_Channel):", reply_markup=back_btn())
                return

            # --- ویرایش برند ---
            if text == '🏷 ویرایش برند' and has_permission(uid, "manage_brand"):
                user_data[uid] = {'step': 'brand'}
                update.message.reply_text("🏷 نام جدید برند را بفرستید:", reply_markup=back_btn())
                return

            # --- ویرایش متن‌ها ---
            if text == '📝 ویرایش متن‌ها' and has_permission(uid, "manage_texts"):
                keyboard = [
                    ['خوش‌آمدگویی', 'پشتیبانی', 'آموزش'],
                    ['تست رایگان', 'عضویت اجباری', 'دعوت دوستان'],
                    ['اطلاعات پرداخت', 'تعمیرات', 'دکمه‌ها'],
                    ['دسته‌بندی‌ها'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "📝 کدام متن را ویرایش کنیم؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # --- متن دکمه‌ها ---
            if text == 'دکمه‌ها' and has_permission(uid, "manage_texts"):
                keyboard = [
                    ['خرید', 'تست', 'سرویس‌ها'],
                    ['تمدید', 'مشخصات', 'پشتیبانی'],
                    ['آموزش', 'دعوت', 'مدیریت'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "📝 کدام دکمه را ویرایش کنیم؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # --- متن دسته‌بندی‌ها ---
            if text == 'دسته‌بندی‌ها' and has_permission(uid, "manage_texts"):
                keyboard = [
                    ['قوی', 'ارزان', 'به صرفه'],
                    ['چند کاربره'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "📝 کدام دسته‌بندی را ویرایش کنیم؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # --- عضویت اجباری ---
            if text == '🔒 عضویت اجباری' and has_permission(uid, "manage_force_join"):
                keyboard = [
                    ['✅ فعال', '❌ غیرفعال'],
                    ['🔗 تنظیم لینک کانال'],
                    ['🔙 برگشت']
                ]
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                channel = db["force_join"]["channel_username"] or "تنظیم نشده"
                update.message.reply_text(
                    f"🔒 وضعیت عضویت اجباری:\nوضعیت: {status}\nکانال: {channel}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ فعال' and has_permission(uid, "manage_force_join"):
                if db["force_join"]["channel_link"]:
                    db["force_join"]["enabled"] = True
                    save_db(db)
                    update.message.reply_text("✅ عضویت اجباری فعال شد", reply_markup=get_admin_menu(uid))
                else:
                    update.message.reply_text("❌ ابتدا لینک کانال را تنظیم کنید")
                return

            if text == '❌ غیرفعال' and has_permission(uid, "manage_force_join"):
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ عضویت اجباری غیرفعال شد", reply_markup=get_admin_menu(uid))
                return

            if text == '🔗 تنظیم لینک کانال' and has_permission(uid, "manage_force_join"):
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text(
                    "🔗 لینک کانال را بفرستید:\nمثال: https://t.me/mychannel",
                    reply_markup=back_btn()
                )
                return

            # --- وضعیت ربات ---
            if text == '🔛 وضعیت ربات' and has_permission(uid, "manage_status"):
                keyboard = [
                    ['✅ روشن', '❌ خاموش'],
                    ['✏️ ویرایش متن تعمیرات'],
                    ['🔙 برگشت']
                ]
                status = "✅ روشن" if db["bot_status"]["enabled"] else "❌ خاموش"
                update.message.reply_text(
                    f"🔛 وضعیت ربات: {status}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ روشن' and has_permission(uid, "manage_status"):
                db["bot_status"]["enabled"] = True
                save_db(db)
                update.message.reply_text("✅ ربات روشن شد", reply_markup=get_admin_menu(uid))
                return

            if text == '❌ خاموش' and has_permission(uid, "manage_status"):
                db["bot_status"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ ربات خاموش شد", reply_markup=get_admin_menu(uid))
                return

            if text == '✏️ ویرایش متن تعمیرات' and has_permission(uid, "manage_status"):
                user_data[uid] = {'step': 'edit_maintenance'}
                update.message.reply_text(
                    f"📝 متن فعلی:\n{db['bot_status']['message']}\n\nمتن جدید را بفرستید:",
                    reply_markup=back_btn()
                )
                return

            # --- آمار ربات ---
            if text == '📊 آمار' and has_permission(uid, "view_stats"):
                total_users = len(db["users"])
                total_purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                total_tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                today = datetime.now().strftime("%Y-%m-%d")
                today_users = sum(1 for u in db["users"].values() if u.get("date", "").startswith(today))
                
                stats = (
                    f"📊 آمار ربات\n"
                    f"━━━━━━━━━━\n"
                    f"👥 کل کاربران: {total_users}\n"
                    f"🆕 کاربران جدید امروز: {today_users}\n"
                    f"💰 تعداد خریدها: {total_purchases}\n"
                    f"🎁 تعداد تست‌ها: {total_tests}"
                )
                update.message.reply_text(stats)
                return

            # --- ارسال همگانی ---
            if text == '📨 ارسال همگانی' and has_permission(uid, "send_broadcast"):
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text(
                    "📨 پیام همگانی را بفرستید:",
                    reply_markup=back_btn()
                )
                return

            # --- افزودن پلن جدید ---
            if text == '➕ پلن جدید' and has_permission(uid, "manage_plans"):
                categories = list(db["categories"].keys())
                kb = [[c] for c in categories] + [['🔙 برگشت']]
                user_data[uid] = {'step': 'new_cat'}
                update.message.reply_text(
                    "📂 دسته‌بندی مورد نظر را انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
                return

            # --- حذف پلن ---
            if text == '➖ حذف پلن' and has_permission(uid, "manage_plans"):
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        btn = InlineKeyboardButton(
                            f"❌ {cat} - {p['name']}",
                            callback_data=f"del_{p['id']}"
                        )
                        keyboard.append([btn])
                
                if keyboard:
                    update.message.reply_text(
                        "🗑 پلن مورد نظر برای حذف را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ هیچ پلنی برای حذف وجود ندارد.")
                return

            # --- ویرایش پلن ---
            if text == '✏️ ویرایش پلن' and has_permission(uid, "manage_plans"):
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        btn = InlineKeyboardButton(
                            f"✏️ {cat} - {p['name']}",
                            callback_data=f"edit_plan_{p['id']}"
                        )
                        keyboard.append([btn])
                
                if keyboard:
                    update.message.reply_text(
                        "✏️ پلن مورد نظر برای ویرایش را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ هیچ پلنی برای ویرایش وجود ندارد.")
                return

            # --- دسته جدید ---
            if text == '➕ دسته جدید' and has_permission(uid, "manage_categories"):
                user_data[uid] = {'step': 'new_category'}
                update.message.reply_text(
                    "📝 نام دسته‌بندی جدید را بفرستید:",
                    reply_markup=back_btn()
                )
                return

            # --- حذف دسته ---
            if text == '➖ حذف دسته' and has_permission(uid, "delete_categories"):
                keyboard = []
                for cat in db["categories"].keys():
                    keyboard.append([InlineKeyboardButton(f"❌ {cat}", callback_data=f"del_cat_{cat}")])
                
                if keyboard:
                    update.message.reply_text(
                        "🗑 دسته‌بندی مورد نظر را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ هیچ دسته‌بندی برای حذف وجود ندارد.")
                return

            # --- کاربران ---
            if text == '👤 کاربران' and has_permission(uid, "view_users"):
                users_list = "👤 لیست کاربران:\n━━━━━━━━━━\n"
                for user_id, user_data in list(db["users"].items())[:20]:  # فقط 20 تا کاربر آخر
                    users_list += f"🆔 {user_id}\n"
                update.message.reply_text(users_list + "\n... (20 کاربر آخر)")
                return

            # --- مراحل ویرایش ---
            if step == 'card_num' and has_permission(uid, "manage_card"):
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ شماره کارت ذخیره شد", reply_markup=get_admin_menu(uid))
                else:
                    update.message.reply_text("❌ شماره کارت باید 16 رقم باشد!")
                user_data[uid] = {}
                return

            if step == 'card_name' and has_permission(uid, "manage_card"):
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ نام صاحب کارت ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'support' and has_permission(uid, "manage_support"):
                db["support"] = text
                save_db(db)
                update.message.reply_text("✅ آیدی پشتیبان ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'guide' and has_permission(uid, "manage_channel"):
                db["guide"] = text
                save_db(db)
                update.message.reply_text("✅ کانال آموزش ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'brand' and has_permission(uid, "manage_brand"):
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ نام برند ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'edit_maintenance' and has_permission(uid, "manage_status"):
                db["bot_status"]["message"] = text
                save_db(db)
                update.message.reply_text("✅ متن تعمیرات ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'set_link' and has_permission(uid, "manage_force_join"):
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
                update.message.reply_text("✅ لینک کانال ذخیره شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            if step == 'broadcast' and has_permission(uid, "send_broadcast"):
                success = 0
                failed = 0
                for uid2 in db["users"]:
                    try:
                        context.bot.send_message(int(uid2), text)
                        success += 1
                    except:
                        failed += 1
                update.message.reply_text(f"✅ ارسال همگانی انجام شد.\n✓ موفق: {success}\n✗ ناموفق: {failed}")
                user_data[uid] = {}
                return

            if step == 'new_category' and has_permission(uid, "manage_categories"):
                db["categories"][text] = []
                save_db(db)
                update.message.reply_text(f"✅ دسته‌بندی {text} اضافه شد", reply_markup=get_admin_menu(uid))
                user_data[uid] = {}
                return

            # --- مراحل افزودن پلن جدید ---
            if step == 'new_cat' and text in db["categories"] and has_permission(uid, "manage_plans"):
                user_data[uid]['cat'] = text
                user_data[uid]['step'] = 'new_name'
                update.message.reply_text("📝 نام پلن را وارد کنید:", reply_markup=back_btn())
                return

            if step == 'new_name' and has_permission(uid, "manage_plans"):
                user_data[uid]['name'] = text
                user_data[uid]['step'] = 'new_vol'
                update.message.reply_text("📦 حجم پلن را وارد کنید (مثال: 50GB):")
                return

            if step == 'new_vol' and has_permission(uid, "manage_plans"):
                user_data[uid]['vol'] = text
                user_data[uid]['step'] = 'new_users'
                update.message.reply_text("👥 تعداد کاربران را وارد کنید (عدد):")
                return

            if step == 'new_users' and has_permission(uid, "manage_plans"):
                try:
                    user_data[uid]['users'] = int(text)
                    user_data[uid]['step'] = 'new_days'
                    update.message.reply_text("⏳ مدت اعتبار را به روز وارد کنید (عدد):")
                except ValueError:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'new_days' and has_permission(uid, "manage_plans"):
                try:
                    user_data[uid]['days'] = int(text)
                    user_data[uid]['step'] = 'new_price'
                    update.message.reply_text("💰 قیمت را به هزار تومان وارد کنید (عدد):")
                except ValueError:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'new_price' and has_permission(uid, "manage_plans"):
                try:
                    price = int(text)
                    
                    # پیدا کردن بزرگترین id
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
                    
                    update.message.reply_text(f"✅ پلن جدید با موفقیت به دسته {category} اضافه شد!", reply_markup=get_admin_menu(uid))
                    user_data[uid] = {}
                    
                except Exception as e:
                    update.message.reply_text(f"❌ خطا در افزودن پلن: {e}")
                return

            # --- دریافت کانفیگ برای ارسال ---
            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                vol = user_data[uid].get('vol', 'نامحدود')
                
                # ثبت در سرویس‌های من
                service_record = f"🚀 {name} | {vol} | {datetime.now().strftime('%Y-%m-%d')}"
                if str(target) not in db["users"]:
                    db["users"][str(target)] = {"purchases": []}
                
                if "purchases" not in db["users"][str(target)]:
                    db["users"][str(target)]["purchases"] = []
                
                db["users"][str(target)]["purchases"].append(service_record)
                save_db(db)
                
                # متن حرفه‌ای نهایی با لینک mono
                msg = (
                    f"🎉 سرویس شما آماده است!\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 نام کاربری سرویس : {name}\n"
                    f"⏳ مدت زمان: نامحدود\n"
                    f"🗜 حجم سرویس: {vol}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"لینک اتصال:\n"
                    f"<code>{update.message.text}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر و انتخاب سیستم عامل خود را دریافت کنید\n\n"
                    f"🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه لینک‌ها رو استخراج کنید.\n\n"
                    f"🔵 کافیه لینک ساب خودتون رو بهش بدید تا تمامی کانفیگ‌هاش رو براتون خروجی بگیره."
                )
                
                # دکمه آموزش اتصال به کانال راهنما
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📚 آموزش اتصال", url=f"https://t.me/{db['guide'].replace('@', '')}")
                ]])
                
                try:
                    context.bot.send_message(int(target), msg, parse_mode='HTML', reply_markup=btn)
                    update.message.reply_text("✅ کانفیگ با موفقیت ارسال شد.")
                except Exception as e:
                    update.message.reply_text(f"❌ خطا در ارسال کانفیگ: {e}")
                
                user_data[uid] = {}
                return

        # --- دریافت نام برای خرید جدید ---
        if step == 'wait_name':
            user_data[uid]['account'] = text
            p = user_data[uid]['plan']
            
            price_toman = p['price'] * 1000
            users_text = f"👥 {p['users']} کاربره" if p['users'] > 1 else "👤 تک کاربره"
            
            # استفاده از متن اطلاعات پرداخت با قابلیت ویرایش
            msg = db["texts"]["payment_info"].format(
                account=text,
                plan_name=p['name'],
                volume=p['volume'],
                users_text=users_text,
                days=p['days'],
                price=price_toman,
                card_number=db['card']['number'],
                card_name=db['card']['name']
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="receipt")
            ]])
            
            update.message.reply_text(msg, parse_mode='HTML', reply_markup=btn)

        # --- نگاشت متن‌های ویرایشی ---
        text_map = {
            'خوش‌آمدگویی': 'welcome',
            'پشتیبانی': 'support',
            'آموزش': 'guide',
            'تست رایگان': 'test',
            'عضویت اجباری': 'force',
            'دعوت دوستان': 'invite',
            'اطلاعات پرداخت': 'payment_info',
            'تعمیرات': 'maintenance'
        }
        
        if text in text_map and has_permission(uid, "manage_texts"):
            user_data[uid] = {'step': f'edit_{text_map[text]}'}
            current_text = db["texts"][text_map[text]]
            update.message.reply_text(
                f"📝 متن فعلی:\n{current_text}\n\nمتن جدید را بفرستید:",
                reply_markup=back_btn()
            )
            return

        # --- نگاشت دکمه‌ها ---
        btn_map = {
            'خرید': 'btn_buy',
            'تست': 'btn_test',
            'سرویس‌ها': 'btn_services',
            'تمدید': 'btn_renew',
            'مشخصات': 'btn_profile',
            'پشتیبانی': 'btn_support',
            'آموزش': 'btn_guide',
            'دعوت': 'btn_invite',
            'مدیریت': 'btn_admin'
        }
        
        if text in btn_map and has_permission(uid, "manage_texts"):
            user_data[uid] = {'step': f'edit_{btn_map[text]}'}
            current_text = db["texts"][btn_map[text]]
            update.message.reply_text(
                f"📝 متن فعلی دکمه:\n{current_text}\n\nمتن جدید را بفرستید:",
                reply_markup=back_btn()
            )
            return

        # --- نگاشت دسته‌بندی‌ها ---
        cat_map = {
            'قوی': 'cat_powerful',
            'ارزان': 'cat_economy',
            'به صرفه': 'cat_value',
            'چند کاربره': 'cat_multi'
        }
        
        if text in cat_map and has_permission(uid, "manage_texts"):
            user_data[uid] = {'step': f'edit_{cat_map[text]}'}
            current_text = db["texts"][cat_map[text]]
            update.message.reply_text(
                f"📝 متن فعلی دسته‌بندی:\n{current_text}\n\nمتن جدید را بفرستید:",
                reply_markup=back_btn()
            )
            return

        # --- ذخیره متن‌های ویرایش شده ---
        if step and step.startswith('edit_') and has_permission(uid, "manage_texts"):
            key = step.replace('edit_', '')
            db["texts"][key] = text
            save_db(db)
            update.message.reply_text("✅ متن ذخیره شد", reply_markup=get_admin_menu(uid))
            user_data[uid] = {}
            return

    except Exception as e:
        logger.error(f"Error in handle_msg: {e}")
        logger.error(traceback.format_exc())
        update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت کالبک‌ها ---
def handle_cb(update, context):
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        query.answer()

        # --- بررسی عضویت اجباری ---
        if query.data == "join_check":
            if check_join(uid, context):
                query.message.delete()
                welcome = db["texts"]["welcome"].format(brand=db["brand"])
                context.bot.send_message(uid, welcome, reply_markup=get_main_menu(uid))
            else:
                query.message.reply_text(
                    "❌ شما هنوز عضو کانال نشده‌اید!\n"
                    "لطفاً ابتدا عضو شوید سپس دکمه تایید را بزنید."
                )
            return

        # --- انتخاب دسته‌بندی ---
        if query.data.startswith("cat_"):
            cat = query.data[4:]
            plans = db["categories"].get(cat, [])
            
            if not plans:
                query.message.reply_text("❌ این دسته‌بندی پلنی ندارد.")
                return
            
            keyboard = []
            for p in plans:
                price_toman = p['price'] * 1000
                btn_text = f"{p['name']} - {price_toman:,} تومان"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{p['id']}")])
            
            query.message.reply_text(
                f"📦 {cat}\nلطفاً پلن مورد نظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- خرید پلن ---
        if query.data.startswith("buy_"):
            try:
                plan_id = int(query.data.split("_")[1])
                
                # پیدا کردن پلن در همه دسته‌ها
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
                    query.message.reply_text("📝 لطفاً نام دلخواه برای اکانت خود وارد کنید:", reply_markup=back_btn())
                else:
                    query.message.reply_text("❌ پلن مورد نظر یافت نشد.")
            except Exception as e:
                query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- ارسال فیش ---
        elif query.data == "receipt":
            if uid in user_data and 'plan' in user_data[uid] and 'account' in user_data[uid]:
                user_data[uid]['step'] = 'wait_photo'
                query.message.reply_text("📸 لطفاً عکس فیش واریزی را ارسال کنید:", reply_markup=back_btn())
            else:
                query.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")
                if uid in user_data:
                    del user_data[uid]
            return

        # --- تمدید سرویس ---
        elif query.data.startswith("renew_"):
            try:
                index = int(query.data.split("_")[1])
                purchases = db["users"][uid].get("purchases", [])
                
                if index < len(purchases):
                    service = purchases[index]
                    
                    # پیدا کردن پلن مشابه
                    similar_plan = None
                    for cat, plans in db["categories"].items():
                        for p in plans:
                            if p['volume'] in service or any(word in service for word in p['name'].split()):
                                similar_plan = p
                                break
                        if similar_plan:
                            break
                    
                    if similar_plan:
                        user_data[uid] = {'step': 'wait_name', 'plan': similar_plan}
                        query.message.reply_text(
                            f"🔄 تمدید سرویس {service[:30]}...\n📝 لطفاً نام اکانت را وارد کنید:",
                            reply_markup=back_btn()
                        )
                    else:
                        query.message.reply_text("❌ پلن مشابه برای تمدید یافت نشد. لطفاً از خرید جدید استفاده کنید.")
                else:
                    query.message.reply_text("❌ سرویس مورد نظر یافت نشد.")
            except Exception as e:
                query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- حذف پلن توسط ادمین ---
        elif query.data.startswith("del_"):
            if has_permission(uid, "manage_plans"):
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
                        query.message.reply_text("✅ پلن با موفقیت حذف شد.")
                    else:
                        query.message.reply_text("❌ پلن مورد نظر یافت نشد.")
                except Exception as e:
                    query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- ویرایش پلن ---
        elif query.data.startswith("edit_plan_"):
            if has_permission(uid, "manage_plans"):
                try:
                    plan_id = int(query.data.split("_")[2])
                    
                    # پیدا کردن پلن
                    for cat, plans in db["categories"].items():
                        for p in plans:
                            if p["id"] == plan_id:
                                user_data[uid] = {'step': 'edit_plan', 'plan': p, 'cat': cat}
                                
                                keyboard = [
                                    ['نام', 'حجم', 'کاربران'],
                                    ['مدت', 'قیمت'],
                                    ['🔙 برگشت']
                                ]
                                query.message.reply_text(
                                    f"✏️ ویرایش پلن {p['name']}\nچه چیزی را ویرایش کنیم؟",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                                )
                                return
                    
                    query.message.reply_text("❌ پلن مورد نظر یافت نشد.")
                except Exception as e:
                    query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- حذف دسته‌بندی ---
        elif query.data.startswith("del_cat_"):
            if has_permission(uid, "delete_categories"):
                try:
                    cat = query.data[8:]
                    if cat in db["categories"]:
                        if len(db["categories"][cat]) > 0:
                            query.message.reply_text("❌ این دسته‌بندی دارای پلن است. ابتدا پلن‌ها را حذف کنید.")
                        else:
                            del db["categories"][cat]
                            save_db(db)
                            query.message.reply_text(f"✅ دسته‌بندی {cat} حذف شد.")
                    else:
                        query.message.reply_text("❌ دسته‌بندی یافت نشد.")
                except Exception as e:
                    query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- حذف ادمین ---
        elif query.data.startswith("del_admin_"):
            if has_permission(uid, "manage_admins"):
                try:
                    admin_id = query.data.split("_")[2]
                    if admin_id in db.get("admins", {}):
                        del db["admins"][admin_id]
                        save_db(db)
                        query.message.reply_text(f"✅ ادمین {admin_id} حذف شد.")
                    else:
                        query.message.reply_text("❌ ادمین یافت نشد.")
                except Exception as e:
                    query.message.reply_text(f"❌ خطا: {e}")
            return

        # --- انتخاب دسترسی برای ادمین جدید ---
        elif query.data.startswith("perm_"):
            if has_permission(uid, "manage_admins") and 'new_admin_id' in user_data.get(uid, {}):
                perm = query.data[5:]
                if 'perms' not in user_data[uid]:
                    user_data[uid]['perms'] = []
                
                if perm in user_data[uid]['perms']:
                    user_data[uid]['perms'].remove(perm)
                else:
                    user_data[uid]['perms'].append(perm)
                
                # نمایش وضعیت
                status_text = "✅ دسترسی‌های انتخاب شده:\n"
                for p in user_data[uid]['perms']:
                    status_text += f"• {PERMISSIONS[p]}\n"
                
                query.message.edit_text(
                    status_text + "\nبرای تغییر روی هر گزینه کلیک کنید:",
                    reply_markup=query.message.reply_markup
                )
            return

        # --- ذخیره ادمین جدید ---
        elif query.data == "save_admin":
            if has_permission(uid, "manage_admins") and 'new_admin_id' in user_data.get(uid, {}):
                new_admin_id = user_data[uid]['new_admin_id']
                perms = user_data[uid].get('perms', [])
                
                if 'admins' not in db:
                    db['admins'] = {}
                
                db['admins'][new_admin_id] = perms
                save_db(db)
                
                query.message.edit_text(f"✅ ادمین {new_admin_id} با موفقیت اضافه شد.")
                user_data[uid] = {}
            return

        # --- ارسال تست توسط ادمین ---
        elif query.data.startswith("test_"):
            if str(uid) == str(MAIN_ADMIN_ID) or uid in db.get("admins", {}):
                try:
                    parts = query.data.split("_")
                    if len(parts) >= 3:
                        target = parts[1]
                        name = parts[2]
                        user_data[uid] = {
                            'step': 'send_config',
                            'target': target,
                            'name': f"تست {name}",
                            'vol': '۳ ساعت'
                        }
                        context.bot.send_message(uid, f"📨 لطفاً کانفیگ تست برای {name} را ارسال کنید:")
                        try:
                            query.message.edit_reply_markup(reply_markup=None)
                        except:
                            pass
                except Exception as e:
                    context.bot.send_message(uid, f"❌ خطا: {e}")
            return

        # --- ارسال کانفیگ توسط ادمین (برای خرید) ---
        elif query.data.startswith("send_"):
            if str(uid) == str(MAIN_ADMIN_ID) or uid in db.get("admins", {}):
                try:
                    target = query.data.split("_")[1]
                    
                    # استخراج اطلاعات از کپشن عکس
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
                        'vol': vol
                    }
                    
                    context.bot.send_message(uid, f"📨 لطفاً کانفیگ {name} را ارسال کنید:")
                    try:
                        query.message.edit_reply_markup(reply_markup=None)
                    except:
                        pass
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

# --- مدیریت دریافت عکس (فیش واریزی) ---
def handle_photo(update, context):
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get('step') == 'wait_photo':
            if 'plan' not in user_data[uid] or 'account' not in user_data[uid]:
                update.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")
                return
            
            p = user_data[uid]['plan']
            account_name = user_data[uid]['account']
            
            price_toman = p['price'] * 1000
            
            # ارسال به ادمین‌ها
            caption = (
                f"💰 فیش واریزی جدید\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 کاربر: {update.effective_user.first_name}\n"
                f"🆔 آیدی: {uid}\n"
                f"👤 یوزرنیم: @{update.effective_user.username}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 پلن: {p['name']}\n"
                f"📊 حجم: {p['volume']}\n"
                f"💰 مبلغ: {price_toman:,} تومان\n"
                f"👤 نام اکانت: {account_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"send_{uid}")
            ]])
            
            # ارسال به همه ادمین‌ها
            for admin_id in db.get("admins", {}):
                try:
                    context.bot.send_photo(
                        int(admin_id),
                        update.message.photo[-1].file_id,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=btn
                    )
                except:
                    pass
            
            # ارسال به ادمین اصلی
            context.bot.send_photo(
                MAIN_ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=btn
            )
            
            update.message.reply_text(
                "✅ فیش شما با موفقیت ارسال شد.\n"
                "به زودی پس از تایید، سرویس برای شما ارسال می‌شود.",
                reply_markup=get_main_menu(uid)
            )
            
            # پاک کردن اطلاعات موقت
            if uid in user_data:
                del user_data[uid]

    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- اجرای اصلی ---
def main():
    try:
        logger.info("🚀 Starting bot...")
        
        # اجرای وب سرور در ترد جداگانه
        web_thread = Thread(target=run_web, daemon=True)
        web_thread.start()
        logger.info("✅ Web server started")
        
        # ساخت ربات
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # اضافه کردن هندلرها
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_cb))
        
        # شروع ربات
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()