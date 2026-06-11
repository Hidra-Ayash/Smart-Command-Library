import sqlite3
from dotenv import load_dotenv
from flask import Flask, request
import telebot
from telebot import types
import json
import os

# ==========================================
# 1. إعداد المسارات المطلقة وتحميل البيئة فوراً
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
LOGO_PATH = os.path.join(BASE_DIR, 'logo.png')
VIP_FILE_AR = os.path.join(BASE_DIR, 'vip_prompts_ar.json')
VIP_FILE_EN = os.path.join(BASE_DIR, 'vip_prompts_en.json')
DB_NAME = os.path.join(BASE_DIR, "bot_database.db")
# --- إضافة زر القائمة (Menu) ---
try:
    commands = [
        types.BotCommand("start", "إعادة تشغيل البوت / Restart"),
    ]
    bot.set_my_commands(commands)
except Exception as e:
    print(f"Error setting commands: {e}")
# ==========================================
# 2. نصوص واجهة المستخدم لكلتا اللغتين
# ==========================================
UI_STRINGS = {
    "ar": {
        "welcome": "أهلاً بك في مكتبة الأوامر الذكية! 🚀\nرقم معرفك الشخصي: `{}`\n\nاختر التصنيف الذي تريد تصفحه من القائمة بالأسفل:",
        "vip_btn": "⭐ الأوامر الاحترافية VIP",
        "back_main": "⬅️ عودة للقائمة الرئيسية",
        "back_cat": "⬅️ عودة للقسم",
        "browse_cat": "تصفح أوامر قسم: {}",
        "ready_copy": "📋 **الأمر جاهز للنسخ:**\n\n`{}`\n\n💡 _اضغط على النص الرمادي ليتم نسخه تلقائياً._",
        "no_vip_prompts": "⚠️ لم يتم العثور على أوامر في ملف الـ VIP حالياً.",
        "vip_welcome": "⭐ **أهلاً بك في عالم المحترفين VIP**\nإليك الأوامر الحصرية الخاصة بك:",
        "choose_lang": "الرجاء اختيار اللغة المفضلّة للبدء:\n\nPlease choose your preferred language to start:",
        "vip_locked": (
            "⭐ **قسم الأوامر الاحترافية VIP** ⭐\n\n"
            "هذا القسم يحتوي على استراتيجيات وأوامر متقدمة جداً وحصرية.\n\n"
            "👤 معرفك الشخصي المطلوب للتفعيل: `{}`\n\n"
            "💳 **للاشتراك وتفعيل القسم لمدة 30 يوم:**\n"
            "يرجى تحويل مبلغ **25,000 ل.س** عبر سيريتل كاش على الرقم:\n"
            "`30513694`\n\n"
            "أو عبر الشام كاش من خلال المعرف التالي:\n"
            "`208c4b3686cbc1987925a9c0e328703c`\n\n"
            "ثم أرسل لقطة شاشة للتحويل مع **رقم معرفك الشخصي** إلى الدعم: `@Your_Bot_Support_Command_lib` ليتم تفعيلك."
        ),
        # 🌟 أضيف حديثاً: نصوص المفضلة (عربي)
        "fav_btn": "⭐️ مفضلتي",
        "add_fav": "⭐️ إضافة للمفضلة",
        "rm_fav": "❌ إزالة من المفضلة",
        "fav_added": "✅ تم الحفظ في المفضلة!",
        "fav_removed": "🗑️ تمت الإزالة من المفضلة!",
        "fav_empty": "⚠️ لا يوجد أوامر في مفضلتك حالياً.",
        "browse_favs": "⭐️ **قائمة مفضلتي:**\nاختر أمراً لعرضه:",
    },
    "en": {
        "welcome": "Welcome to the Smart Prompts Library! 🚀\nYour Personal ID: `{}`\n\nChoose a category to browse from the menu below:",
        "vip_btn": "⭐ Pro Prompts VIP",
        "back_main": "⬅️ Back to Main Menu",
        "back_cat": "⬅️ Back to Category",
        "browse_cat": "Browsing category: {}",
        "ready_copy": "📋 **Prompt ready to copy:**\n\n`{}`\n\n💡 _Click the grey text to copy it automatically._",
        "no_vip_prompts": "⚠️ No prompts found in the VIP file currently.",
        "vip_welcome": "⭐ **Welcome to the VIP Pro World**\nHere are your exclusive prompts:",
        "choose_lang": "Please choose your preferred language to start:",
        "vip_locked": (
            "⭐ **VIP Pro Prompts Section** ⭐\n\n"
            "This section contains highly advanced and exclusive strategies and prompts.\n\n"
            "👤 Your Personal ID required for activation: `{}`\n\n"
            "💳 **To subscribe and activate for 30 days:**\n"
            "Please transfer **25,000 SYP** via Syriatel Cash to:\n"
            "`30513694`\n\n"
            "Or via Cham Cash using the following ID:\n"
            "`208c4b3686cbc1987925a9c0e328703c`\n\n"
            "Then send a screenshot of the transfer along with your **Personal ID** to support: `@Your_Bot_Support_Command_lib` to get activated."
        ),
        # 🌟 أضيف حديثاً: نصوص المفضلة (إنجليزي)
        "fav_btn": "⭐️ My Favorites",
        "add_fav": "⭐️ Add to Favorites",
        "rm_fav": "❌ Remove from Favorites",
        "fav_added": "✅ Saved to Favorites!",
        "fav_removed": "🗑️ Removed from Favorites!",
        "fav_empty": "⚠️ No prompts in your favorites currently.",
        "browse_favs": "⭐️ **Your Favorites List:**\nChoose a prompt to view:",
    }
}

# ==========================================
# 3. قاعدة بيانات الأوامر ثنائية اللغة (المجانية)
# ==========================================
PROMPTS_DATA = {
    "ar": {
        "prog": {
            "name": "💻 برمجة وأكواد",
            "prompts": [
                {"title": "🔍 مكتشف الأخطاء البرمجية", "text": "تصرف كمبرمج خبير. سأعطيك كوداً برمجياً، وأريدك أن تجد الأخطاء فيه وتشرح سببها وتصححها: [ضع الكود هنا]"},
                {"title": "💡 شرح كود معقد", "text": "اشرح لي الكود التالي خطوة بخطوة للمبتدئين، مع ذكر الوظيفة الأساسية له: [ضع الكود هنا]"},
                {"title": "🚀 تحسين وتنظيف الكود", "text": "قم بمراجعة الكود التالي وإعادة كتابته ليكون أكثر نظافة (Clean Code) وأفضل من حيث الأداء، مع إضافة تعليقات توضيحية: [ضع الكود هنا]"},
                {"title": "⚙️ سكريبت أتمتة مهام", "text": "اكتب لي سكريبت بلغة [بايثون] لأتمتة مهمة [وصف المهمة]، مع مراعاة معالجة الأخطاء."}
            ]
        },
        "lecture":{
            "name": "(💡NEW)🎓 المساعد الأكاديمي",
       "prompts":[
        {
            "title": "📝 تلخيص محاضرة (عربي)",
            "text": "بصفتك مساعداً أكاديمياً خبيراً، قم بتحليل نص المحاضرة التالي وتقديمه بهيكلية: (1) الخلاصة التنفيذية (4 أسطر)، (2) المفاهيم والمصطلحات الرئيسية (قائمة نقطية)، (3) ملخص شامل بجدول محتويات وعناوين فرعية، (4) اختبار فهم (3 أسئلة اختيار من متعدد مع الإجابة، وسؤالين تفكير نقدي). التزم بالدقة العلمية واللغة الفصحى المهنية. نص المحاضرة: [ضع النص هنا]"
         }]
            },
        "design": {
            "name": "🎨 تصميم و UI/UX",
            "prompts": [
                {"title": "✏️ توليد فكرة لوغو", "text": "أريد فكرة شعار (Logo) لشركة ناشئة تعمل في مجال [المجال]. اعطني اقتراحات للألوان، الأيقونات، والنمط العام."},
                {"title": "📱 تحسين تجربة مستخدم", "text": "اقترح لي 5 تحسينات لتجربة المستخدم (UX) لصفحة [اسم الصفحة] في تطبيق [نوع التطبيق]."}
            ]
        },
        "content": {
            "name": "📝 صناعة المحتوى التقني",
            "prompts": [
                {"title": "🎬 أفكار ريلز وفيديوهات", "text": "أعطني 5 أفكار لفيديوهات قصيرة جذابة تتحدث عن [الموضوع]، مع كتابة Hook قوي يشد المشاهد في أول 3 ثوانٍ."},
                {"title": "✍️ سكربت فيديو تعليمي", "text": "اكتب لي سكربت لفيديو مدته 60 ثانية يشرح [مفهوم معين] بطريقة مبسطة."}
            ]
        },
        "images": {
            "name": "🖼️ صور بالذكاء الاصطناعي",
            "prompts": [
                {"title": "📸 برومبت صورة إعلانية", "text": "اكتب لي برومبت إنجليزي لـ Midjourney لتوليد صورة إعلانية احترافية لمنتج [اسم المنتج]. إضاءة استوديو ناعمة وخلفية سادة."},
                {"title": "🏢 خلفية سوشيال ميديا", "text": "اكتب لي برومبت إنجليزي لتوليد صورة خلفية مناسبة لتصميم بوست انستغرام لمشروع في مجال [المجال]."}
            ]
        },
        "marketing": {
            "name": "🚀 تسويق وكتابة إعلانية",
            "prompts": [
                {"title": "📝 نص إعلان جذاب (AIDA)", "text": "اكتب لي نصاً إعلانياً لمنتج/خدمة [اسم المنتج] باستخدام نموذج AIDA. اجعل النص قصيراً ومناسباً لمنصة انستغرام."},
                {"title": "💬 رسالة مبيعات واتساب", "text": "اكتب لي رسالة واتساب قصيرة وودية لإرسالها لعميل استفسر عن [اسم المنتج]."}
            ]
        },
        "productivity": {
            "name": "💼 العمل الحر والإنتاجية",
            "prompts": [
                {"title": "📧 إيميل احترافي لعميل", "text": "اكتب لي رسالة بريد إلكتروني احترافية لعميل محتمل أعرض فيها خدماتي في مجال [مجال عملك]."},
                {"title": "⏳ خطة تنظيم مهام يومية", "text": "ضع لي جدولاً زمنياً (Time-blocking) ليوم عمل يتضمن أوقات التركيز العميق لإنجاز هذه المهام: [المهام]."}
            ]
        }
    },
    "en": {
        "prog": {
            "name": "💻 Coding & Dev",
            "prompts": [
                {"title": "🔍 Code Bug Finder", "text": "Act as an expert developer. Review this code, find bugs, explain why they happen, and provide the corrected version: [Insert Code]"},
                {"title": "💡 Complex Code Explainer", "text": "Explain the following code step-by-step for a beginner, highlighting its primary function: [Insert Code]"},
                {"title": "🚀 Code Optimization", "text": "Refactor the following code for better performance and clean code standards, adding helpful comments: [Insert Code]"},
                {"title": "⚙️ Task Automation Script", "text": "Write a Python script to automate the task of [Describe Task] with proper error handling."}
            ]
        },
        "lecture": {
            "name": "(💡NEW)🎓 Academic Assistant",
            "prompts": [
                {
                    "title": "📝 Lecture Summary (Arabic)",
                    "text": "As an expert academic assistant, analyze the following lecture text and format it as follows: (1) Executive Overview (max 4 lines), (2) Key Concepts & Glossary (bulleted list), (3) Comprehensive Summary with subheadings, and (4) Knowledge Check (3 MCQs with answers, and 2 critical thinking questions). Maintain scientific accuracy and professional formal language. Lecture text: [Insert text here]"
                }
            ]
        },
        "design": {
            "name": "🎨 Design & UI/UX",
            "prompts": [
                {"title": "✏️ Logo Concept Generator", "text": "Provide a creative logo design concept for a startup in the [Industry] field. Include suggestions for color palette, icons, and style."},
                {"title": "📱 UX Improvement Hints", "text": "Suggest 5 UX improvements for the [Page Name] of a [App Type] application."}
            ]
        },
        "content": {
            "name": "📝 Tech Content Creation",
            "prompts": [
                {"title": "🎬 Reels & Shorts Ideas", "text": "Give me 5 engaging short-form video ideas about [Topic], with a powerful hook for the first 3 seconds."},
                {"title": "✍️ Educational Video Script", "text": "Write a 60-second video script explaining [Concept] in simple terms, including a clear Call to Action (CTA)."}
            ]
        },
        "images": {
            "name": "🖼️ AI Image Prompts",
            "prompts": [
                {"title": "📸 Commercial Product Prompt", "text": "Create a high-quality Midjourney prompt for a commercial product shot of [Product Name]. Use soft studio lighting and a clean minimalist background."},
                {"title": "🏢 Social Media Background", "text": "Write an English prompt to generate a clean background image for an Instagram post related to [Project Niche], leaving negative space for text."}
            ]
        },
        "marketing": {
            "name": "🚀 Marketing & Copywriting",
            "prompts": [
                {"title": "📝 Ad Copywriting (AIDA)", "text": "Write a high-converting ad copy for [Product/Service] using the AIDA framework, optimized for Instagram/Facebook ads."},
                {"title": "💬 WhatsApp Sales Template", "text": "Draft a friendly and professional WhatsApp sales message to reply to a client inquiring about [Product Name]."}
            ]
        },
        "productivity": {
            "name": "💼 Freelancing & Productivity",
            "prompts": [
                {"title": "📧 Cold Outreach Email", "text": "Write a professional cold email offering my services in [Your Field] to a potential client, asking for a brief meeting."},
                {"title": "⏳ Time-Blocking Schedule", "text": "Create a daily time-blocking schedule for a [Your Role] focusing on completing these top 3 tasks: [Insert Tasks]."}
            ]
        }
    }
}

# ==========================================
# 4. دالات إدارة قاعدة البيانات واللغات والمفضلة
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            is_vip INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'ar'
        )
    ''')
    # 🌟 أضيف حديثاً: جدول المفضلة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            title TEXT,
            prompt_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def activate_user_in_db(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, is_vip, lang)
        VALUES (?, 1, 'ar')
        ON CONFLICT(user_id) DO UPDATE SET is_vip=1
    ''', (str(user_id),))
    conn.commit()
    conn.close()

def register_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, lang) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET lang=?
    ''', (str(user_id), lang, lang))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT lang FROM users WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "ar"

def is_user_vip(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT is_vip FROM users WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    return (row[0] == 1) if row else False

def load_vip_prompts(lang):
    file = VIP_FILE_AR if lang == "ar" else VIP_FILE_EN
    if not os.path.exists(file):
        return []
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

# 🌟 أضيف حديثاً: دوال التحكم بنظام المفضلة
def check_favorite(user_id, prompt_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND prompt_text = ?', (str(user_id), prompt_text))
    row = cursor.fetchone()
    conn.close()
    return bool(row)

def add_favorite(user_id, title, prompt_text):
    if check_favorite(user_id, prompt_text): return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO favorites (user_id, title, prompt_text) VALUES (?, ?, ?)', (str(user_id), title, prompt_text))
    conn.commit()
    conn.close()

def remove_favorite_by_text(user_id, prompt_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE user_id = ? AND prompt_text = ?', (str(user_id), prompt_text))
    conn.commit()
    conn.close()

def remove_favorite_by_id(user_id, fav_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE user_id = ? AND id = ?', (str(user_id), int(fav_id)))
    conn.commit()
    conn.close()

def get_user_favorites(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM favorites WHERE user_id = ?', (str(user_id),))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1]} for r in rows]

def get_favorite_by_id(fav_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT title, prompt_text FROM favorites WHERE id = ?', (int(fav_id),))
    row = cursor.fetchone()
    conn.close()
    return {"title": row[0], "prompt_text": row[1]} if row else None

init_db()

# ==========================================
# 5. القائمة الرئيسية وإعدادات اللغة عند الترحيب
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_ar = types.InlineKeyboardButton(text="العربية 🇸🇦", callback_data="set_lang_ar")
    btn_en = types.InlineKeyboardButton(text="English 🇬🇧", callback_data="set_lang_en")
    markup.add(btn_ar, btn_en)

    bot.send_message(message.chat.id, UI_STRINGS["ar"]["choose_lang"], reply_markup=markup)

def display_main_menu(chat_id, lang, message_id=None):
    markup = types.InlineKeyboardMarkup()
    for category_id, info in PROMPTS_DATA[lang].items():
        button = types.InlineKeyboardButton(text=info["name"], callback_data=f"cat_{category_id}")
        markup.add(button)

    vip_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["vip_btn"], callback_data="vip_section")
    # 🌟 أضيف حديثاً: زر المفضلة في القائمة الرئيسية
    fav_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["fav_btn"], callback_data="my_favorites")

    markup.add(vip_button)
    markup.add(fav_button)

    lang_text = "🌐 Change Language / تغيير اللغة"
    lang_button = types.InlineKeyboardButton(text=lang_text, callback_data="change_lang_menu")
    markup.add(lang_button)

    welcome_text = UI_STRINGS[lang]["welcome"].format(chat_id)

    if (os.path.exists(LOGO_PATH) and os.path.isfile(LOGO_PATH)) or LOGO_PATH.startswith(('http://', 'https://')):
        try:
            if message_id:
                try: bot.delete_message(chat_id, message_id)
                except Exception: pass

            if os.path.exists(LOGO_PATH) and os.path.isfile(LOGO_PATH):
                with open(LOGO_PATH, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=welcome_text, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_photo(chat_id, LOGO_PATH, caption=welcome_text, parse_mode="Markdown", reply_markup=markup)
            return
        except Exception:
            pass

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=welcome_text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# ==========================================
# 6. معالجة التفاعل والضغط على الأزرار
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id

    if call.data.startswith("set_lang_"):
        lang = call.data.replace("set_lang_", "")
        register_user_lang(user_id, lang)
        display_main_menu(user_id, lang, call.message.message_id)
        return

    elif call.data == "change_lang_menu":
        markup = types.InlineKeyboardMarkup()
        btn_ar = types.InlineKeyboardButton(text="العربية 🇸🇦", callback_data="set_lang_ar")
        btn_en = types.InlineKeyboardButton(text="English 🇬🇧", callback_data="set_lang_en")
        markup.add(btn_ar, btn_en)
        try: bot.delete_message(user_id, call.message.message_id)
        except Exception: pass
        bot.send_message(user_id, UI_STRINGS["ar"]["choose_lang"], reply_markup=markup)
        return

    lang = get_user_lang(user_id)

    if call.data.startswith("cat_"):
        category_id = call.data.replace("cat_", "")
        category = PROMPTS_DATA[lang][category_id]

        markup = types.InlineKeyboardMarkup()
        for index, prompt in enumerate(category["prompts"]):
            button = types.InlineKeyboardButton(text=prompt["title"], callback_data=f"show_{category_id}_{index}")
            markup.add(button)

        back_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_main"], callback_data="back_main")
        markup.add(back_button)

        text_to_send = UI_STRINGS[lang]["browse_cat"].format(category['name'])

        if call.message.content_type == 'photo':
            try: bot.delete_message(user_id, call.message.message_id)
            except Exception: pass
            bot.send_message(chat_id=user_id, text=text_to_send, reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text_to_send, reply_markup=markup)

    elif call.data.startswith("show_"):
        _, category_id, index = call.data.split("_")
        index = int(index)
        prompt = PROMPTS_DATA[lang][category_id]["prompts"][index]

        response_text = UI_STRINGS[lang]["ready_copy"].format(prompt['text'])
        markup = types.InlineKeyboardMarkup()

        # 🌟 أضيف حديثاً: التحقق من وجود الأمر في المفضلة وعرض الزر المناسب
        is_fav = check_favorite(user_id, prompt['text'])
        if is_fav:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["rm_fav"], callback_data=f"rmfav_f_{category_id}_{index}")
        else:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["add_fav"], callback_data=f"addfav_f_{category_id}_{index}")
        markup.add(fav_btn)

        back_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_cat"], callback_data=f"cat_{category_id}")
        markup.add(back_button)

        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=response_text, parse_mode="Markdown", reply_markup=markup)

    # 🌟 أضيف حديثاً: معالجة إضافة/إزالة الأوامر المجانية من المفضلة (تبديل تفاعلي للزر)
    elif call.data.startswith("addfav_f_") or call.data.startswith("rmfav_f_"):
        parts = call.data.split("_")
        action = parts[0]
        category_id = parts[2]
        index = int(parts[3])

        prompt = PROMPTS_DATA[lang][category_id]["prompts"][index]

        if action == "addfav":
            add_favorite(user_id, prompt['title'], prompt['text'])
            bot.answer_callback_query(call.id, text=UI_STRINGS[lang]["fav_added"])
        else:
            remove_favorite_by_text(user_id, prompt['text'])
            bot.answer_callback_query(call.id, text=UI_STRINGS[lang]["fav_removed"])

        is_fav = check_favorite(user_id, prompt['text'])
        markup = types.InlineKeyboardMarkup()
        if is_fav:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["rm_fav"], callback_data=f"rmfav_f_{category_id}_{index}")
        else:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["add_fav"], callback_data=f"addfav_f_{category_id}_{index}")

        markup.add(fav_btn)
        markup.add(types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_cat"], callback_data=f"cat_{category_id}"))
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "back_main":
        display_main_menu(user_id, lang, call.message.message_id)

    elif call.data == "vip_section":
        markup = types.InlineKeyboardMarkup()
        back_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_main"], callback_data="back_main")

        if is_user_vip(user_id):
            vip_prompts = load_vip_prompts(lang)
            if not vip_prompts:
                if call.message.content_type == 'photo':
                    try: bot.delete_message(user_id, call.message.message_id)
                    except Exception: pass
                    bot.send_message(chat_id=user_id, text=UI_STRINGS[lang]["no_vip_prompts"])
                else:
                    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=UI_STRINGS[lang]["no_vip_prompts"])
                return

            for index, prompt in enumerate(vip_prompts):
                button = types.InlineKeyboardButton(text=prompt["title"], callback_data=f"showvip_{index}")
                markup.add(button)
            markup.add(back_button)
            text_to_send = UI_STRINGS[lang]["vip_welcome"]
            parse_mode_set = None
        else:
            markup.add(back_button)
            text_to_send = UI_STRINGS[lang]["vip_locked"].format(user_id)
            parse_mode_set = "Markdown"

        if call.message.content_type == 'photo':
            try: bot.delete_message(user_id, call.message.message_id)
            except Exception: pass
            bot.send_message(chat_id=user_id, text=text_to_send, parse_mode=parse_mode_set, reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text_to_send, parse_mode=parse_mode_set, reply_markup=markup)

    elif call.data.startswith("showvip_"):
        index = int(call.data.split("_")[1])
        vip_prompts = load_vip_prompts(lang)
        prompt = vip_prompts[index]

        response_text = f"⭐ **VIP Prompt:**\n\n`{prompt['text']}`\n\n💡 _Click to copy instantly._" if lang=="en" else f"⭐ **أمر VIP حصري:**\n\n`{prompt['text']}`\n\n💡 _اضغط للنسخ الفوري._"
        markup = types.InlineKeyboardMarkup()

        # 🌟 أضيف حديثاً: التحقق من وجود الأمر الـ VIP في المفضلة
        is_fav = check_favorite(user_id, prompt['text'])
        if is_fav:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["rm_fav"], callback_data=f"rmfav_v_{index}")
        else:
            fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["add_fav"], callback_data=f"addfav_v_{index}")
        markup.add(fav_btn)

        back_button = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_main"], callback_data="vip_section")
        markup.add(back_button)

        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=response_text, parse_mode="Markdown", reply_markup=markup)

    # 🌟 أضيف حديثاً: معالجة إضافة/إزالة أوامر VIP من المفضلة
    elif call.data.startswith("addfav_v_") or call.data.startswith("rmfav_v_"):
        parts = call.data.split("_")
        action = parts[0]
        index = int(parts[2])

        vip_prompts = load_vip_prompts(lang)
        if index < len(vip_prompts):
            prompt = vip_prompts[index]
            if action == "addfav":
                add_favorite(user_id, prompt['title'], prompt['text'])
                bot.answer_callback_query(call.id, text=UI_STRINGS[lang]["fav_added"])
            else:
                remove_favorite_by_text(user_id, prompt['text'])
                bot.answer_callback_query(call.id, text=UI_STRINGS[lang]["fav_removed"])

            is_fav = check_favorite(user_id, prompt['text'])
            markup = types.InlineKeyboardMarkup()
            if is_fav:
                fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["rm_fav"], callback_data=f"rmfav_v_{index}")
            else:
                fav_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["add_fav"], callback_data=f"addfav_v_{index}")

            markup.add(fav_btn)
            markup.add(types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_main"], callback_data="vip_section"))
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)

    # 🌟 أضيف حديثاً: عرض قائمة مفضلتي
    elif call.data == "my_favorites":
        favs = get_user_favorites(user_id)
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_main"], callback_data="back_main")

        if not favs:
            markup.add(back_btn)
            text_to_send = UI_STRINGS[lang]["fav_empty"]
        else:
            for fav in favs:
                btn = types.InlineKeyboardButton(text=fav['title'], callback_data=f"showfav_{fav['id']}")
                markup.add(btn)
            markup.add(back_btn)
            text_to_send = UI_STRINGS[lang]["browse_favs"]

        if call.message.content_type == 'photo':
            try: bot.delete_message(user_id, call.message.message_id)
            except Exception: pass
            bot.send_message(chat_id=user_id, text=text_to_send, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text_to_send, parse_mode="Markdown", reply_markup=markup)

    # 🌟 أضيف حديثاً: عرض أمر محدد من المفضلة
    elif call.data.startswith("showfav_"):
        fav_id = int(call.data.split("_")[1])
        fav = get_favorite_by_id(fav_id)
        if fav:
            response_text = UI_STRINGS[lang]["ready_copy"].format(fav['prompt_text'])
            markup = types.InlineKeyboardMarkup()
            rm_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["rm_fav"], callback_data=f"rmfavid_{fav_id}")
            back_btn = types.InlineKeyboardButton(text=UI_STRINGS[lang]["back_cat"], callback_data="my_favorites")
            markup.add(rm_btn)
            markup.add(back_btn)
            bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=response_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "⚠️ هذا الأمر لم يعد موجوداً.")

    # 🌟 أضيف حديثاً: إزالة الأمر من داخل عرض المفضلة ثم العودة للقائمة
    elif call.data.startswith("rmfavid_"):
        fav_id = int(call.data.split("_")[1])
        remove_favorite_by_id(user_id, fav_id)
        bot.answer_callback_query(call.id, text=UI_STRINGS[lang]["fav_removed"])
        call.data = "my_favorites"
        handle_query(call)

# ==========================================
# 7. أوامر الإدارة والتحكم (للآدمن فقط)
# ==========================================
@bot.message_handler(commands=['myid'])
def check_bot_response(message):
    print(f"🔍 [فحص اتصال] وصل أمر /myid من شات ID: {message.chat.id}", flush=True)
    bot.reply_to(message, f"🤖 البوت مستجيب شغال! معرف الشات الحالي الخاص بك هو:\n`{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['activate'])
def activate_user(message):
    current_chat_id = str(message.chat.id).strip()
    expected_admin_id = str(ADMIN_ID).strip()

    if current_chat_id != expected_admin_id:
        bot.reply_to(message, "❌ عذراً، هذا الأمر مخصص للآدمن فقط.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ الرجاء كتابة المعرف. مثال: `/activate 123456`", parse_mode="Markdown")
            return

        target_id = str(parts[1]).strip()
        activate_user_in_db(target_id)

        status_text = f"✅ تم تفعيل المستخدم `{target_id}` في قاعدة البيانات كـ VIP بنجاح!"
        bot.reply_to(message, status_text, parse_mode="Markdown")

        try:
            bot.send_message(int(target_id), "🎉 مبروك! تم تفعيل حسابك في القسم المشترك VIP بنجاح.\n\nPress /start")
        except Exception:
            pass

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ داخلي: {e}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if str(message.chat.id).strip() != str(ADMIN_ID).strip(): return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_vip = 1')
    vip_count = cursor.fetchone()[0]
    conn.close()

    bot.send_message(message.chat.id, f"📊 **قائمة الإحصائيات الحية:**\n\n👥 إجمالي المستخدمين: `{total}`\n⭐ المشتركين المحترفين VIP: `{vip_count}`", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_to_all(message):
    if str(message.chat.id).strip() != str(ADMIN_ID).strip(): return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ الاستخدام الصحيح: `/broadcast نص الرسالة هنا`", parse_mode="Markdown")
        return

    broadcast_msg = parts[1]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = cursor.fetchall()
    conn.close()

    status_msg = bot.reply_to(message, "⏳ جاري إرسال البث الجماعي الآن...")
    success, failed = 0, 0

    for row in rows:
        u_id = row[0]
        try:
            bot.send_message(int(u_id), broadcast_msg, parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"📢 **تم الانتهاء من الإذاعة الجماعية!**\n\n✅ تم بنجاح: `{success}`\n❌ فشل (حظر أو توقف): `{failed}`", parse_mode="Markdown")


# ==========================================
# 8. إعدادات الـ Webhook للتشغيل 24/7 بالخلفية
# ==========================================
app = Flask(__name__)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def webhook_setup():
    bot.remove_webhook()
    YOUR_USERNAME = "haedra2004"
    bot.set_webhook(url=f"https://{YOUR_USERNAME}.pythonanywhere.com/{BOT_TOKEN}")
    return "🚀 Webhook has been set successfully!", 200

if __name__ == "__main__":
    app.run(port=5000)