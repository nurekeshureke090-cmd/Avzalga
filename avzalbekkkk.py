import telebot
import requests
import time
import os
import threading
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup as RK, KeyboardButton as KB, InlineKeyboardMarkup as IK, InlineKeyboardButton as IB, WebAppInfo
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import dns.resolver

# DNS sozlamalari (MongoDB klasteriga ulanish uchun)
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

TOKEN = os.environ.get('BOT_TOKEN', '9047473926:AAFqBYlwig1Q4CvPDUJogREPYUM89QUP9-Q')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 8467707826))
GRIZZLY_API_KEY = os.environ.get('GRIZZLY_API_KEY', '3335af0d250efb73bdc40ebf82fa42dd')
SMM_API_KEY = os.environ.get('SMM_API_KEY', '17d89a016b9005b0e52bce6f67ad8e35')
SMM_API_URL = 'https://top4smm.com/api.php'
MONGO_URL = os.environ.get('MONGO_URL', "mongodb+srv://nurekeshureke090_db_user:qKFmlTnxjnAe27Gi@cluster0.1dcdbiw.mongodb.net/?appName=Cluster0")

bot = telebot.TeleBot(TOKEN, num_threads=100)
usr_st = {}
tmp_dt = {}

# Oddiy Emojilar
E_PHON = "📱"
E_BOX = "📦"
E_STAR = "✨"
E_USER = "👥"
E_1USR = "👤"
E_OK = "✅"
E_CHRT = "📊"
E_PEN = "✏️"
E_ERR = "❌"
E_DOWN = "⬇️"
E_CARD = "💳"
E_CART = "🛒"
E_BAG = "🛍"
E_MONY = "💵"
E_LINK = "🔗"
E_TIME = "⏳"
E_NUM = "🔢"
E_DATE = "🗓"
E_BELL = "🔔"
E_CROWN = "👑"
E_PERCENT = "💯"
E_SETTINGS = "⚙️"
E_BONUS = "🎁"
E_PAYME = "💳"
E_CLICK = "💳"
E_PAYNET = "🏦"

# Custom (Premium) Emojilar
CUSTOM_EMOJI = {
    'star': '5407034569176138231',
    'money': '5197434882321567830',
    'card': '5445353829304387411',
    'shop': '5294167145079395967',
    'cart': '5312361253610475399',
    'wallet': '5287231198098117669',
    'chart': '5190806721286657692',
    'rocket': '5456112073840801701',
    'shield': '5197288647275071607',
    'gift': '5278702045883292456',
    'target': '5310278924616356636',
    'briefcase': '5445221832074483553',
    'crown': '5460712567930371726',
    'sparkle': '5454073076771734647',
    'check': '5454008995859675847',
    'fire': '5460976145778358813',
    'diamond': '5460723807859782728',
    'phone': '5460905742674442512',
    'bell': '5460905742674442512',
    'game': '5309890285910644610',
    'search': '5312294067437062586',
    'lightning': '5195033767969839232',
    'handshake': '5461011665157894946',
    'wave': '5453929508899931025',
    'users': '5460618847449005320',
    'user': '5460618847449005320',
    'percent': '5404526480073966211',
    'timer': '5382194935057372936',
    'num': '5429651785352501917',
    'link': '5271837459783638319',
    'date': '5274055917766202507',
    'time': '5404727802370999261',
    'cross': '5454237135932506706',
    'warning': '5454237135932506706',
    'pin': '5310278924616356636',
    'lock': '5197288647275071607',
    'video': '5312357757507096610',
    'folder': '5460739411475973201',
    'bag': '5460689598445273231',
    'red_circle': '5407109232887613382',
    'mobile': '5461046042076136604',
    'phone3': '5460722686873321402',
    'phone2': '5460799223190534123',
    'payme': '5445353829304387411',
    'paynet': '5332455502917949981',
    'click': '5445353829304387411',
    'robot': '5312019116515673002',
    'heart': '5461138474067312201',
    'bulb': '5262844652964303985',
    'money_bag': '5278467510604160626',
    'chart_down': '5429518319243775957',
    'chart_up': '5429651785352501917',
    'pen': '5460900833526825380',
    'youtube': '5456299961480132196',
    'telegram': '5456281420106315074',
    'instagram': '5319160079465857105',
    'tiktok': '5327982530702359565'
}

def ce(emoji_id, text):
    return f'<tg-emoji emoji-id="{emoji_id}">{text}</tg-emoji>'

def ce_f(key, text):
    emoji_id = CUSTOM_EMOJI.get(key)
    if emoji_id:
        return ce(emoji_id, text)
    return text

# Ma'lumotlar bazasi ulanishi
cluster = MongoClient(MONGO_URL, maxPoolSize=100)
db = cluster["PROSmmMarket"]
users_db = db["users"]
orders_db = db["orders"]
accounts_db = db["accounts"]
settings_db = db["settings"]
admins_db = db["admins"]
payments_db = db["payments"]
promos_db = db["promos"]

# Standart sozlamalar
defaults = {
    'card': '8600 0000 0000 0000',
    'admin': '@SizningUserneyim',
    'm_chan': '@prosmmmarket',
    'p_y1': '190000',
    'p_y2': '120000',
    'p_2func': '100000',
    'm_nomer': '20',
    'm_yt_sub': '20',
    'm_yt_watch': '20',
    'm_smm': '20',
    'bot_desc': 'Tezkor, Arzon va Sifatli SMM Xizmatlar',
    'webapp_url': os.environ.get('WEBAPP_URL', '')
}

for k, v in defaults.items():
    if not settings_db.find_one({"_id": k}):
        settings_db.insert_one({"_id": k, "value": str(v)})

# Valyuta kurslari caching
K_C = {"RUB": {"r": 140.0, "t": 0}, "USD": {"r": 12700.0, "t": 0}}

def g_k(c, d):
    if time.time() - K_C[c]["t"] > 3600:
        try:
            r = requests.get(f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/{c}/", timeout=3).json()
            K_C[c]["r"] = float(r[0]['Rate'])
            K_C[c]["t"] = time.time()
        except:
            K_C[c]["r"] = d
    return K_C[c]["r"]

# Yordamchi funksiyalar
def is_adm(uid):
    return uid == ADMIN_ID or (admins_db.find_one({"_id": uid}) is not None)

def g_adms():
    return list(set([ADMIN_ID] + [x["_id"] for x in admins_db.find()]))

def adm_msg(txt, rm=None):
    for a in g_adms():
        try:
            bot.send_message(a, txt, reply_markup=rm, parse_mode='HTML')
        except:
            pass

def g_bal(id):
    user = users_db.find_one({"_id": id})
    if user:
        return int(user.get('balance', 0))
    return 0

def g_c(t):
    return accounts_db.count_documents({"type": t})

def g_set(k):
    res = settings_db.find_one({"_id": k})
    if res:
        return str(res.get('value', " "))
    return " "

def u_set(k, v):
    settings_db.update_one({"_id": k}, {"$set": {"value": str(v)}}, upsert=True)

def u_bal(id, amt):
    users_db.update_one({"_id": id}, {"$inc": {"balance": int(amt)}}, upsert=True)

def get_m(k):
    try:
        return 1.0 + (int(g_set(k)) / 100.0)
    except:
        return 1.20

def get_country_m(cid):
    val = g_set(f'm_num_{cid}')
    if val != " ":
        try:
            return 1.0 + (int(val) / 100.0)
        except:
            pass
    return get_m('m_nomer')
        
# Grizzly API funksiyalari
def get_gz_pr(sc=None, cid=None):
    try:
        url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_API_KEY}&action=getPrices"
        if sc: url += f"&service={sc}"
        if cid: url += f"&country={cid}"
        r = requests.get(url, timeout=10).json()
        p = {}
        if sc and not cid:
            for c_id, s_data in r.items():
                if type(s_data) is dict and sc in s_data:
                    if int(s_data[sc].get('count', 1)) > 0:
                        v = s_data[sc].get('cost') or s_data[sc].get('price')
                        if v: p[str(c_id)] = float(v)
        elif cid and not sc:
            target = r[str(cid)] if str(cid) in r else r
            for s_id, s_data in target.items():
                if type(s_data) is dict:
                    if int(s_data.get('count', 1)) > 0:
                        v = s_data.get('cost') or s_data.get('price')
                        if v: p[str(s_id)] = float(v)
        return p
    except:
        return {}

def http_get_text(url, params=None, timeout=10):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        return r.status_code, r.text.strip(), None
    except requests.RequestException as e:
        return 0, "", str(e)

def req_gz(sc, cid):
    code, body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "getNumber", "service": sc, "country": cid}, timeout=15)
    if err:
        return {"s": False, "m": "API xatosi yuz berdi."}
    if "NO_BALANCE" in body:
        return {"s": False, "m": "Texnik uzilish. Keyinroq urinib ko'ring."}
    if "NO_NUMBERS" in body:
        return {"s": False, "m": "Bu tarmoq mavjud emas"}
    
    parts = body.split(":")
    if body.startswith("ACCESS_NUMBER:") and len(parts) >= 3:
        return {"s": True, "id": parts[1], "n": ":".join(parts[2:])}
    
    return {"s": False, "m": "Bu tarmoq mavjud emas"}

# SMM Xizmatlari ro'yxati
def g_smm():
    return [
        {'service': '281', 'name': 'Telegram Followers', 'category': 'telegram sub follower', 'rate': '6.9', 'min': 100, 'max': 35000},
        {'service': '532', 'name': 'Telegram ⭐Premium⭐ Followers', 'category': 'telegram sub follower', 'rate': '30.0', 'min': 10, 'max': 20000},
        {'service': '295', 'name': 'Telegram Views', 'category': 'telegram view', 'rate': '0.49', 'min': 100, 'max': 10000},
        {'service': '296', 'name': 'Telegram Views (Several Posts)', 'category': 'telegram view', 'rate': '0.69', 'min': 100, 'max': 1000000},
        {'service': '530', 'name': 'Telegram Story Views', 'category': 'telegram view', 'rate': '3.8', 'min': 10, 'max': 50000},
        {'service': '531', 'name': 'Telegram Shares', 'category': 'telegram view', 'rate': '1.79', 'min': 10, 'max': 5000},
        {'service': '650', 'name': 'Telegram Where', 'category': 'telegram like', 'rate': '1.79', 'min': 10, 'max': 300000},
        {'service': '633', 'name': 'Telegram Positive Reactions', 'category': 'telegram like', 'rate': '1.79', 'min': 50, 'max': 150000},
        {'service': '634', 'name': 'Telegram Negative Reactions', 'category': 'telegram like', 'rate': '1.79', 'min': 50, 'max': 150000},
        {'service': '162', 'name': 'YouTube Views', 'category': 'youtube view', 'rate': '2.9', 'min': 100, 'max': 2000000},
        {'service': '208', 'name': 'YouTube Views (Ranking)', 'category': 'youtube view', 'rate': '3.39', 'min': 100, 'max': 10000000},
        {'service': '123', 'name': 'YouTube Views (Slow)', 'category': 'youtube view', 'rate': '2.29', 'min': 100, 'max': 50000},
        {'service': '333', 'name': 'YouTube Live-Stream Views', 'category': 'youtube view', 'rate': '0.29', 'min': 30, 'max': 25000},
        {'service': '226', 'name': 'YouTube Pre-Premiere Views', 'category': 'youtube view', 'rate': '0.59', 'min': 1000, 'max': 10000},
        {'service': '501', 'name': 'YouTube Watch Hours (30+ min)', 'category': 'youtube watch time hour', 'rate': '6.0', 'min': 100, 'max': 4000},
        {'service': '203', 'name': 'YouTube 100 Watch Hours', 'category': 'youtube watch time hour', 'rate': '20.0', 'min': 1, 'max': 1},
        {'service': '499', 'name': 'YouTube 250 Watch Hours', 'category': 'youtube watch time hour', 'rate': '45.0', 'min': 1, 'max': 1},
        {'service': '202', 'name': 'YouTube 500 Watch Hours', 'category': 'youtube watch time hour', 'rate': '90.0', 'min': 1, 'max': 1},
        {'service': '198', 'name': 'YouTube 1000 Watch Hours', 'category': 'youtube watch time hour', 'rate': '180.0', 'min': 1, 'max': 1},
        {'service': '200', 'name': 'YouTube 2000 Watch Hours', 'category': 'youtube watch time hour', 'rate': '360.0', 'min': 1, 'max': 1},
        {'service': '161', 'name': 'YouTube Likes', 'category': 'youtube like', 'rate': '15.9', 'min': 10, 'max': 30000},
        {'service': '378', 'name': 'YouTube Community Post Likes', 'category': 'youtube like', 'rate': '15.9', 'min': 10, 'max': 50000},
        {'service': '122', 'name': 'YouTube Comment Likes', 'category': 'youtube like', 'rate': '15.9', 'min': 10, 'max': 4000},
        {'service': '116', 'name': 'YouTube Subscribers (Slow)', 'category': 'youtube sub follower', 'rate': '43.0', 'min': 100, 'max': 2000},
        {'service': '78', 'name': 'YouTube Custom Comments', 'category': 'youtube comment', 'rate': '65.0', 'min': 10, 'max': 4000},
        {'service': '207', 'name': 'YouTube Random Positive Comments', 'category': 'youtube comment', 'rate': '65.0', 'min': 10, 'max': 4000},
        {'service': '156', 'name': 'Instagram Followers', 'category': 'instagram sub follower', 'rate': '3.69', 'min': 10, 'max': 1000000},
        {'service': '191', 'name': 'Instagram Followers (Premium)', 'category': 'instagram sub follower', 'rate': '5.9', 'min': 10, 'max': 1000000},
        {'service': '187', 'name': 'Instagram Likes', 'category': 'instagram like', 'rate': '1.0', 'min': 10, 'max': 85000},
        {'service': '547', 'name': 'Instagram Comment Likes', 'category': 'instagram like', 'rate': '7.1', 'min': 20, 'max': 1000},
        {'service': '14', 'name': 'Instagram Views', 'category': 'instagram view', 'rate': '0.59', 'min': 100, 'max': 100000000},
        {'service': '159', 'name': 'Instagram Saves', 'category': 'instagram view', 'rate': '2.1', 'min': 100, 'max': 5000},
        {'service': '209', 'name': 'Instagram Profile Visits', 'category': 'instagram view', 'rate': '0.59', 'min': 100, 'max': 1000000},
        {'service': '626', 'name': 'Instagram Engagement', 'category': 'instagram view', 'rate': '2.1', 'min': 100, 'max': 1000000},
        {'service': '58', 'name': 'Instagram Random Positive Comments', 'category': 'instagram comment', 'rate': '45.9', 'min': 20, 'max': 5000},
        {'service': '49', 'name': 'Instagram Custom Comments', 'category': 'instagram comment', 'rate': '45.9', 'min': 5, 'max': 500},
        {'service': '661', 'name': 'TikTok Views (High Retention)', 'category': 'tiktok view', 'rate': '1.2', 'min': 100, 'max': 100000},
        {'service': '506', 'name': 'TikTok Live Viewers', 'category': 'tiktok view', 'rate': '7.0', 'min': 50, 'max': 3500},
        {'service': '212', 'name': 'TikTok Followers', 'category': 'tiktok sub follower', 'rate': '13.9', 'min': 25, 'max': 5000},
        {'service': '213', 'name': 'TikTok Likes', 'category': 'tiktok like', 'rate': '7.9', 'min': 10, 'max': 10000},
        {'service': '223', 'name': 'TikTok Custom Comments', 'category': 'tiktok comment', 'rate': '0.4', 'min': 10, 'max': 500},
        {'service': '225', 'name': 'TikTok Random Comments', 'category': 'tiktok comment', 'rate': '0.4', 'min': 10, 'max': 1000},
        {'service': '258', 'name': 'TikTok Auto Likes', 'category': 'tiktok like', 'rate': '0.5', 'min': 10, 'max': 500}
    ]

# Obuna tekshirish
def c_sub(uid):
    ch = g_set('m_chan').strip()
    if not ch or is_adm(uid):
        return True
    try:
        return bot.get_chat_member(ch, uid).status in ['member', 'administrator', 'creator']
    except:
        return True

def req_sub(cid, uid):
    ch = g_set('m_chan').replace('@', '').strip()
    mk = IK(row_width=1).add(
        IB("➕ Obuna bo'lish", url=f"https://t.me/{ch}"),
        IB("🔄 Tekshirish", callback_data="ck_sub")
    )
    try:
        bot.send_message(cid, f"⚠ <b>Botdan foydalanish uchun kanalimizga a'zo bo'ling:</b>\n@{ch}", reply_markup=mk, parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data == "ck_sub")
def ck_s(c):
    if c_sub(c.from_user.id):
        bot.answer_callback_query(c.id, "Rahmat!")
        try:
            bot.delete_message(c.message.chat.id, c.message.message_id)
        except:
            pass
        try:
            bot.send_message(c.message.chat.id, f"{ce_f('check', '✅')} <b>Rahmat! Menyuga marhamat:</b>", reply_markup=m_menu(c.from_user.id), parse_mode='HTML')
        except:
            pass
    else:
        bot.answer_callback_query(c.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)

# Asosiy Menyu
def get_webapp_url():
    u = g_set('webapp_url').strip()
    if u and u.startswith('https://'):
        return u
    env_u = os.environ.get('RENDER_EXTERNAL_URL', '').strip()
    if env_u and env_u.startswith('https://'):
        return env_u + '/app'
    return ''

def m_menu(uid):
    m = RK(resize_keyboard=True, row_width=2)
    w_url = get_webapp_url()
    if w_url:
        m.add(KB("🚀 Mini App (Ilovani ochish)", web_app=WebAppInfo(url=w_url), icon_custom_emoji_id="5456112073840801701"))
    m.add(
        KB("Xizmatlar", icon_custom_emoji_id="5294167145079395967"),
        KB("Nomer olish", icon_custom_emoji_id="5461046042076136604"),
        KB("Tayyor Kanallar", icon_custom_emoji_id="5456299961480132196"),
        KB("Buyurtmalarim", icon_custom_emoji_id="5312361253610475399"),
        KB("Pul ishlash", icon_custom_emoji_id="5278467510604160626"),
        KB("Mening hisobim", icon_custom_emoji_id="5287231198098117669"),
        KB("Hisob to'ldirish", icon_custom_emoji_id="5445353829304387411"),
        KB("Murojaat", icon_custom_emoji_id="5460618847449005320"),
        KB("Qo'llab-quvvatlash", icon_custom_emoji_id="5454237135932506706"),
        KB("Qo'llanma", icon_custom_emoji_id="5312357757507096610")
    )
    m.add(KB("Hamkorlik", icon_custom_emoji_id="5461011665157894946"))
    if is_adm(uid):
        m.add(KB("Admin Panel", icon_custom_emoji_id="5460712567930371726"))
    return m

# Admin Menyu
def a_menu():
    y1_count = g_c('y1')
    y2_count = g_c('y2')
    return RK(resize_keyboard=True, row_width=2).add(
        KB(f"➕ 2006-2009 ({y1_count} ta)"),
        KB(f"➕ 2010-2019 ({y2_count} ta)"),
        KB(f"{E_CHRT} Statistika"),
        KB(f"{E_CARD} Karta o'zgartirish"),
        KB("⚙️ Narxlarni o'zgartirish"),
        KB("💯 Foizlarni o'zgartirish"),
        KB(f"{E_BELL} Kanal ulash"),
        KB("✉️ Xabarnoma"),
        KB(f"{E_CROWN} Admin qo'shish"),
        KB("💬 Murojaat o'zgartirish"),
        KB("🔗 Skidka Link"),
        KB("🏆 Top Xaridorlar"),
        KB(f"{E_BOX} Qo'llanma o'zgartirish"),
        KB("🏠 Bosh sahifa")
    )

# Start komandasi
@bot.message_handler(commands=['start'])
def st(m):
    uid = m.from_user.id
    ref = 0
    is_skidka = False
    args = m.text.split()
    
    if len(args) > 1:
        if args[1] == 'skidka':
            is_skidka = True
        elif args[1].isdigit():
            ref = int(args[1])
            
    ref = 0 if ref == uid else ref
    user = users_db.find_one({"_id": uid})
    
    if not user:
        users_db.insert_one({"_id": uid, "balance": 0, "r": ref, "skidka": is_skidka})
        if ref:
            try:
                bot.send_message(ref, f"{ce_f('bell', '🔔')} <b>Do'stingiz botga kirdi!</b>\n\nTo'lov qilsa <b>5%</b> bonus olasiz! {ce_f('gift', '')}", parse_mode='HTML')
            except:
                pass
    elif is_skidka and not user.get("skidka"):
        users_db.update_one({"_id": uid}, {"$set": {"skidka": True}})
    
    if not c_sub(uid):
        return req_sub(m.chat.id, uid)
        
    usr_st[uid] = None
    
    txt = f"""
{ce_f('wave', '👋')} <b>Assalomu alaykum, {m.from_user.first_name}!</b>

{ce_f('robot', '🤖')} <b>@{bot.get_me().username}</b> ga xush kelibsiz!

{ce_f('sparkle', '✨')} <i>{g_set('bot_desc')}</i>

━━━━━━━━━━━━━━━━━━━━
{ce_f('crown', '👑')} <b>Bizning xizmatlar:</b>
<blockquote>
{ce_f('mobile', '📱')} Virtual Nomerlar (20+ davlatlar)
{ce_f('red_circle', '🔴')} Tayyor YouTube Kanallar
{ce_f('telegram', '✈')} Telegram - Obunachi, View, Like
{ce_f('instagram', '📸')} Instagram - Obunachi, Like, View
{ce_f('youtube', '▶️')} YouTube - Obunachi, View, Watchtime
{ce_f('tiktok', '🎵')} TikTok - Obunachi, Like, View
</blockquote>
{ce_f('money', '💵')} <b>Qulay narxlar</b>
{ce_f('rocket', '🚀')} <b>Tezkor yetkazish</b>
{ce_f('shield', '🛡')} <b>Sifat kafolati</b>
━━━━━━━━━━━━━━━━━━━━
👇 <b>Menyudan kerakli bo'limni tanlang:</b>
"""
    if is_skidka or (user and user.get("skidka")):
        txt += f"\n\n{ce_f('gift', '🎁')} <b>Sizda ESKI YouTube kanallari (2006-2019) uchun 15 000 so'm CHEGIRMA mavjud!</b>"
        
    try:
        bot.send_message(m.chat.id, txt, reply_markup=m_menu(uid), parse_mode='HTML', disable_web_page_preview=True)
    except:
        pass

@bot.message_handler(func=lambda m: m.text and "Bosh sahifa" in m.text)
def bs(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, f"🏠 <b>Asosiy menyuga qaytdingiz.</b>", reply_markup=m_menu(m.from_user.id), parse_mode='HTML')

# Profil (Mening hisobim)
def send_profile_msg(chat_id, user_id, msg_id=None):
    user = users_db.find_one({"_id": user_id})
    balans = g_bal(user_id)
    total_dep = int(user.get('total_deposited', 0)) if user else 0
    ref_count = users_db.count_documents({"r": user_id})
    
    txt = f"""
{ce_f('briefcase', '💼')} <b>Kabinetingizga xush kelibsiz.</b>
<blockquote>
📋 <b>Ma'lumotlaringiz:</b>
├─ {ce_f('user', '👤')} ID raqamingiz: <code>{user_id}</code>
├─ {ce_f('money', '💵')} Hisobingiz: <b>{balans:,} so'm</b>
└─ {ce_f('wallet', '💰')} Kiritgan pullaringiz: <b>{total_dep:,} so'm</b>
</blockquote>
{ce_f('gift', '🎁')} <b>Referal tizimi (5% bonus):</b>
{ce_f('link', '🔗')} <code>https://t.me/{bot.get_me().username}?start={user_id}</code>
{ce_f('users', '👥')} Taklif qilinganlar: <b>{ref_count} ta</b>
"""
    mk = IK(row_width=2).add(
        IB(f"{E_CARD} Pul kiritish", callback_data="deposit_menu"),
        IB(f"{E_PERCENT} Chegirma olish", callback_data="discount_info"),
        IB(f"{E_SETTINGS} Sozlamalar", callback_data="user_settings"),
        IB(f"{E_BONUS} Promo-Bonus", callback_data="promo_bonus")
    )
    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=mk, parse_mode='HTML', disable_web_page_preview=True)
            return
        except:
            pass
    bot.send_message(chat_id, txt, reply_markup=mk, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text and "Mening hisobim" in m.text)
def mc(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
    send_profile_msg(m.chat.id, m.from_user.id)

# Profil Inline tugmalari
@bot.callback_query_handler(func=lambda c: c.data in ["deposit_menu", "back_profile", "discount_info", "promo_bonus", "user_settings", "payme_auto", "click_auto", "paynet", "card_manual", "close_msg", "none"])
def inline_menus(c):
    if c.data == "none":
        return bot.answer_callback_query(c.id)
    if c.data == "close_msg":
        bot.answer_callback_query(c.id)
        try:
            bot.delete_message(c.message.chat.id, c.message.message_id)
        except:
            pass
        return
    if c.data == "back_profile":
        bot.answer_callback_query(c.id)
        usr_st[c.from_user.id] = None
        return send_profile_msg(c.message.chat.id, c.from_user.id, c.message.message_id)
    if c.data == "deposit_menu":
        bot.answer_callback_query(c.id)
        txt = f"""
{ce_f('card', '💳')} <b>Hisobni to'ldirish usullari:</b>

🇺🇿 <b>O'zbekiston kartalari:</b>
• Uzcard / Humo orqali

━━━━━━━━━━━━━━━━━━━━
ℹ <i>Minimal to'lov: 1,000 so'm</i>
"""
        mk = IK(row_width=1).add(
            IB(f"{E_CARD} Karta orqali to'ldirish", callback_data="card_manual"),
            IB("🔙 Orqaga", callback_data="back_profile")
        )
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    elif c.data in ["card_manual", "payme_auto", "click_auto", "paynet"]:
        bot.answer_callback_query(c.id)
        usr_st[c.from_user.id] = "manual_amount"
        txt = f"""
{ce_f('card', '💳')} <b>Hisobni to'ldirish</b>
━━━━━━━━━━━━━━━━━━━━
💵 <b>Necha so'm to'ldirmoqchisiz?</b>

<i>Raqamni yozing (masalan: 50000)</i>
"""
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="back_profile")), parse_mode='HTML')
    elif c.data == "user_settings":
        bot.answer_callback_query(c.id, "⚙️ Sozlamalar standart holatda faol!", show_alert=True)
    elif c.data == "discount_info":
        bot.answer_callback_query(c.id)
        txt = f"""
{ce_f('percent', '💯')} <b>Chegirma olish yo'llari:</b>

{ce_f('gift', '🎁')} <b>Referal bonus 5%</b>
Do'stingizni taklif qiling va uning har bir to'lovidan <b>5%</b> bonus oling!

🔗 <b>Referal link:</b>
<code>https://t.me/{bot.get_me().username}?start={c.from_user.id}</code>
"""
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="back_profile")), parse_mode='HTML')
    elif c.data == "promo_bonus":
        bot.answer_callback_query(c.id)
        usr_st[c.from_user.id] = "enter_promo"
        txt = f"""
{ce_f('target', '🎯')} <b>Promo-kod kiriting:</b>

Maxsus promo-kodlarni kanalimizdan oling!
Har bir promo-kod <b>bonus balans</b> beradi!

📢 <b>Kanal:</b> @{g_set('m_chan').replace('@','')}
✍️ <i>Promo-kodni xabar sifatida yozib yuboring:</i>
"""
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="back_profile")), parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == "enter_promo")
def handle_promo_code(m):
    if m.text in ["Xizmatlar", "Nomer olish", "Tayyor Kanallar", "Buyurtmalarim", "Pul ishlash", "Mening hisobim", "Hisob to'ldirish", "Murojaat", "Qo'llab-quvvatlash", "Qo'llanma", "Hamkorlik", "Admin Panel", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Promo-kod kiritish bekor qilindi.", reply_markup=m_menu(m.from_user.id))
    
    code_str = m.text.strip()
    promo = promos_db.find_one({"_id": code_str})
    usr_st[m.from_user.id] = None
    
    if not promo or int(promo.get("left", 0)) <= 0:
        return bot.send_message(m.chat.id, f"{ce_f('cross', '❌')} <b>Bunday promo-kod mavjud emas yoki muddati tugagan!</b>", parse_mode='HTML')
    if m.from_user.id in promo.get("used_by", []):
        return bot.send_message(m.chat.id, f"{ce_f('warning', '⚠️')} <b>Siz bu promo-koddan allaqachon foydalangansiz!</b>", parse_mode='HTML')
        
    amt = int(promo.get("amount", 0))
    promos_db.update_one({"_id": code_str}, {"$inc": {"left": -1}, "$push": {"used_by": m.from_user.id}})
    u_bal(m.from_user.id, amt)
    bot.send_message(m.chat.id, f"{ce_f('gift', '🎁')} <b>Tabriklaymiz! Promo-kod faollashtirildi!</b>\n💵 Hisobingizga <b>{amt:,} so'm</b> qo'shildi!", parse_mode='HTML')

# Yordamchi Bo'limlar
@bot.message_handler(func=lambda m: m.text and any(x in m.text for x in ["Pul ishlash", "Murojaat", "Qo'llab-quvvatlash", "Hamkorlik", "Buyurtmalarim", "Qo'llanma"]) and "o'zgartirish" not in m.text)
def info_menus(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    if "Qo'llanma" in m.text:
        vid = g_set('guide_vid').strip()
        g_txt = g_set('guide_txt').strip()
        if vid:
            try:
                bot.send_video(m.chat.id, vid, caption=g_txt if g_txt else "🤖 Botdan foydalanish bo'yicha video qo'llanma.", parse_mode='HTML')
            except:
                bot.send_message(m.chat.id, "📭 Hozircha video qo'llanma yuklanmagan.")
        else:
            bot.send_message(m.chat.id, "📭 Hozircha video qo'llanma yuklanmagan.")
            
    elif "Pul ishlash" in m.text:
        txt = f"""
{ce_f('wallet', '💰')} <b>Pul ishlash imkoniyatlari:</b>

{ce_f('gift', '🎁')} <b>1. Referal dasturi (5%):</b>
Do'stlaringizni taklif qiling va ularning har bir to'lovidan <b>5% komissiya</b> oling!

📢 <b>2. Kanal reklama:</b>
Kanal yoki guruhingizni bot orqali reklama qiling!

{ce_f('handshake', '🤝')} <b>3. Hamkorlik:</b>
SMM panel egalari bilan hamkorlik qiling!

━━━━━━━━━━━━━━━━━━━━
<b>Referal link:</b>
<code>https://t.me/{bot.get_me().username}?start={m.from_user.id}</code>
"""
        bot.send_message(m.chat.id, txt, reply_markup=IK(row_width=1).add(IB("❌ Yopish", callback_data="close_msg")), parse_mode='HTML')
        
    elif "Murojaat" in m.text:
        txt = f"""
{ce_f('phone', '📞')} <b>Admin bilan bog'lanish:</b>

👤 Admin: {g_set('admin')}
⏰ <b>Ish vaqti:</b> 09:00 - 23:00
📱 <b>Javob berish vaqti:</b> 5-30 daqiqa
"""
        bot.send_message(m.chat.id, txt, parse_mode='HTML')
        
    elif "Qo'llab-quvvatlash" in m.text:
        txt = f"""
{ce_f('phone2', '📞')} <b>Qo'llab-quvvatlash xizmati</b>

<b>Biz sizga yordam beramiz:</b>
❓ <b>Tez-tez so'raladigan savollar:</b>
1️⃣ <b>Buyurtma qancha vaqtda bajariladi?</b>
→ Odatda 5-60 daqiqa ichida

2️⃣ <b>To'lov qanday qilish kerak?</b>
→ "Hisob to'ldirish" bo'limidan

3️⃣ <b>Pul qaytariladimi?</b>
→ Ha, buyurtma bajarilmasa 100% qaytariladi

━━━━━━━━━━━━━━━━━━━━
📬 <b>Muammo bormi?</b>
Admin: {g_set('admin')}
"""
        mk = IK(row_width=1).add(
            IB(f"✍️ Adminga yozish", url=f"https://t.me/{g_set('admin').replace('@','')}"),
            IB("❌ Yopish", callback_data="close_msg")
        )
        bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML', disable_web_page_preview=True)
        
    elif "Hamkorlik" in m.text:
        txt = f"""
{ce_f('handshake', '🤝')} <b>Hamkorlik taklifi</b>

<b>SMM Panel egalari uchun:</b>
✅ <b>Nima beramiz:</b>
• Arzon narxlar (ulgurji)
• API ulanish
• Shaxsiy menejer

💰 <b>Shartlar:</b>
• Minimal balans: 500,000 so'm
• Oylik aylanma: 2,000,000+ so'm

━━━━━━━━━━━━━━━━━━━━
📩 <b>Bog'lanish:</b> {g_set('admin')}
"""
        mk = IK(row_width=1).add(
            IB(f"📩 Hamkorlik bo'yicha yozish", url=f"https://t.me/{g_set('admin').replace('@','')}"),
            IB("❌ Yopish", callback_data="close_msg")
        )
        bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML', disable_web_page_preview=True)
        
    elif "Buyurtmalarim" in m.text:
        r = list(orders_db.find({"user_id": m.from_user.id}).sort("_id", -1).limit(10))
        if not r:
            return bot.send_message(m.chat.id, "📭 Hali buyurtmalaringiz yo'q.")
            
        t = f"📋 <b>So'nggi buyurtmalaringiz:</b>\n\n"
        for i, x in enumerate(r, 1):
            st_em = ce_f('check', '✅') if "Bajarildi" in x.get('status', '') else ce_f('time', '⏳') if "Kutmoqda" in x.get('status', '') else "🔄"
            t += f"{ce_f('num', '🔢')} <b>#{i}</b>\n├─ ID: <code>{x.get('oid', 'N/A')}</code>\n├─ Holat: {st_em} {x.get('status', 'N/A')}\n├─ Miqdor: {x.get('quantity', 0)}\n├─ Link: {x.get('link', 'N/A')[:50]}\n└─ Sana: {x.get('date', 'N/A')}\n\n"
        bot.send_message(m.chat.id, t, parse_mode='HTML', disable_web_page_preview=True)

# Admin Panel qismi
@bot.message_handler(func=lambda m: m.text and "Admin Panel" in m.text and is_adm(m.from_user.id))
def ap(m):
    y1_count = g_c('y1')
    y2_count = g_c('y2')
    
    txt = f"""
{ce_f('crown', '👑')} <b>Admin Panel</b>

📦 <b>Bazada qolgan tayyor kanallar:</b>
🔴 2006-09 kanallar: <b>{y1_count} ta qoldi</b>
🟠 2010-19 kanallar: <b>{y2_count} ta qoldi</b>

<b>Tezkor buyruqlar:</b>
• Balans berish: <code>/addbalance ID SUMMA</code>
• Promo yaratish: <code>/addpromo KOD SUMMA SONI</code>
• Mini App ulash: <code>/setwebapp https://manzil/app</code>
• Mijoz tekshirish: <code>/info ID</code>
• Foydalanuvchilar: <code>/users</code>

📌 <b>Bo'limni tanlang:</b>
"""
    bot.send_message(m.chat.id, txt, reply_markup=a_menu(), parse_mode='HTML')

@bot.message_handler(commands=['info', 'users', 'addbalance', 'addpromo', 'setwebapp'])
def ad_cmds(m):
    if not is_adm(m.from_user.id):
        return
        
    if m.text.startswith('/info') and len(m.text.split()) > 1:
        try:
            uid = int(m.text.split()[1])
        except:
            return bot.send_message(m.chat.id, "❌ ID raqam bo'lishi kerak.")
        u = users_db.find_one({"_id": uid})
        if u:
            txt = f"""
👤 <b>Mijoz ma'lumotlari:</b>
ID: <code>{uid}</code>
💵 Balans: <b>{int(u.get('balance', 0)):,} so'm</b>
💰 Kiritgan puli: <b>{int(u.get('total_deposited', 0)):,} so'm</b>
"""
            bot.send_message(m.chat.id, txt, parse_mode='HTML')
        else:
            bot.send_message(m.chat.id, f"{ce_f('cross', '❌')} Bunday foydalanuvchi bazada yo'q.", parse_mode='HTML')
            
    elif m.text.startswith('/users'):
        count = users_db.count_documents({})
        bot.send_message(m.chat.id, f"👥 <b>Jami foydalanuvchilar:</b> {count:,} ta", parse_mode='HTML')
        
    elif m.text.startswith('/addbalance') and len(m.text.split()) > 2:
        try:
            parts = m.text.split()
            uid = int(parts[1])
            amount = int(parts[2])
        except:
            return bot.send_message(m.chat.id, "❌ Format: /addbalance ID SUMMA")
        
        u_bal(uid, amount)
        users_db.update_one({"_id": uid}, {"$inc": {"total_deposited": amount}}, upsert=True)
        try:
            bot.send_message(uid, f"{ce_f('gift', '🎁')} Balansingizga <b>{amount:,} so'm</b> qo'shildi!", parse_mode='HTML')
        except:
            pass
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Bajarildi! {uid} raqamiga {amount:,} so'm qo'shildi.", parse_mode='HTML')

    elif m.text.startswith('/addpromo') and len(m.text.split()) > 3:
        try:
            parts = m.text.split()
            code_str = parts[1]
            amount = int(parts[2])
            limit_cnt = int(parts[3])
            promos_db.update_one({"_id": code_str}, {"$set": {"amount": amount, "left": limit_cnt, "used_by": []}}, upsert=True)
            bot.send_message(m.chat.id, f"✅ Promo-kod yaratildi!\nKod: <code>{code_str}</code>\nSumma: {amount:,} so'm\nLimit: {limit_cnt} ta", parse_mode='HTML')
        except:
            bot.send_message(m.chat.id, "❌ Format: /addpromo KOD SUMMA SONI")

    elif m.text.startswith('/setwebapp') and len(m.text.split()) > 1:
        url_val = m.text.split()[1].strip()
        if url_val == "0":
            u_set('webapp_url', '')
            bot.send_message(m.chat.id, "✅ Mini App tugmasi o'chirildi!", reply_markup=m_menu(m.from_user.id))
        elif url_val.startswith("https://"):
            if not url_val.endswith("/app"):
                url_val = url_val.rstrip("/") + "/app"
            u_set('webapp_url', url_val)
            bot.send_message(m.chat.id, f"✅ Mini App manzili saqlandi!\n🔗 <code>{url_val}</code>", parse_mode='HTML', reply_markup=m_menu(m.from_user.id))
        else:
            bot.send_message(m.chat.id, "❌ URL faqat https:// bilan boshlanishi shart! (Masalan: /setwebapp https://sizning-saytingiz.onrender.com/app)")

@bot.message_handler(func=lambda m: m.text and is_adm(m.from_user.id) and any(x in m.text for x in ["Statistika", "Top Xaridorlar", "Skidka"]))
def adm_stats(m):
    if "Statistika" in m.text:
        total_bal_list = list(users_db.aggregate([{"$group": {"_id": None, "total": {"$sum": "$balance"}}}]))
        total_bal = int(total_bal_list[0]['total']) if total_bal_list else 0
        total_income = sum(int(p.get("amount", 0)) for p in list(payments_db.find({"status": "paid"})))
        
        dash_text = f"""
{ce_f('chart', '📊')} <b>ADMIN DASHBOARD</b>
━━━━━━━━━━━━━━━━━━━━
👥 Jami a'zolar: <b>{users_db.count_documents({}):,} ta</b>
💰 Userlar balansi: <b>{total_bal:,} so'm</b>
💵 Jami sof tushum: <b>{total_income:,} so'm</b>
"""
        bot.send_message(m.chat.id, dash_text, parse_mode='HTML')
        
    elif "Top Xaridorlar" in m.text:
        top_users = list(orders_db.aggregate([
            {"$group": {"_id": "$user_id", "total_orders": {"$sum": 1}}},
            {"$sort": {"total_orders": -1}},
            {"$limit": 5}
        ]))
        txt = "🏆 <b>TOP 5 ENG FAOL XARIDORLAR:</b>\n\n"
        for i, u in enumerate(top_users, 1):
            txt += f"{i}. 👤 ID: <code>{u['_id']}</code> - 📦 <b>{int(u['total_orders'])} marta</b>\n"
        bot.send_message(m.chat.id, txt, parse_mode="HTML")
        
    elif "Skidka" in m.text:
        bot.send_message(m.chat.id, f"{ce_f('gift', '🎁')} <b>Maxsus Skidka Ssilkasi:</b>\n<code>https://t.me/{bot.get_me().username}?start=skidka</code>", parse_mode='HTML')

# TO'G'RILANDI: "+ 2006" va "+ 2010" o'rniga "2006-2009" va "2010-2019" ishlatildi hamda state "wac_y1"/"wac_y2" ga to'g'rilandi
@bot.message_handler(func=lambda m: m.text and is_adm(m.from_user.id) and any(x in m.text for x in ["Kanal ulash", "Xabarnoma", "Narxlarni o'zgartirish", "Foizlarni o'zgartirish", "Admin qo'shish", "Karta o'zgartirish", "Murojaat o'zgartirish", "Qo'llanma o'zgartirish", "2006-2009", "2010-2019"]))
def adm_btns(m):
    if "Kanal ulash" in m.text:
        usr_st[m.from_user.id] = "set_chan"
        bot.send_message(m.chat.id, f"📌 <b>Majburiy obuna kanalini @bilan yuboring (o'chirish uchun 0):</b>", parse_mode='HTML')
        
    elif "Xabarnoma" in m.text:
        usr_st[m.from_user.id] = "brd_msg"
        bot.send_message(m.chat.id, f"<b>Xabarni yuboring</b> (/cancel - bekor qilish):", parse_mode='HTML')
        
    elif "Narxlarni o'zgartirish" in m.text:
        mk = IK(row_width=1).add(
            IB(f"06-09 Kanal: {g_set('p_y1')} so'm", callback_data="edp_p_y1"),
            IB(f"10-19 Kanal: {g_set('p_y2')} so'm", callback_data="edp_p_y2"),
            IB(f"2 funksiya: {g_set('p_2func')} so'm", callback_data="edp_p_2func")
        )
        bot.send_message(m.chat.id, "⚙️ <b>Qaysi xizmat narxini o'zgartirasiz?</b>", reply_markup=mk, parse_mode='HTML')
        
    elif "Foizlarni o'zgartirish" in m.text:
        mk = IK(row_width=1).add(
            IB("🌍 Davlatlarga alohida foiz", callback_data="margin_countries"),
            IB(f"📱 Umumiy Nomerlar: {g_set('m_nomer')}%", callback_data="edp_m_nomer"),
            IB(f"📺 YT Obunachi: {g_set('m_yt_sub')}%", callback_data="edp_m_yt_sub"),
            IB(f"⏱ YT Watchtime: {g_set('m_yt_watch')}%", callback_data="edp_m_yt_watch"),
            IB(f"🛍 Boshqa SMM: {g_set('m_smm')}%", callback_data="edp_m_smm")
        )
        bot.send_message(m.chat.id, "⚙️ <b>Qaysi xizmat ustama foizini o'zgartirasiz?</b>", reply_markup=mk, parse_mode='HTML')
        
    elif "Admin qo'shish" in m.text:
        usr_st[m.from_user.id] = "add_adm"
        bot.send_message(m.chat.id, f"<b>Yangi admin ID raqamini yuboring:</b>", parse_mode='HTML')
        
    elif "Karta o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_c"
        bot.send_message(m.chat.id, f"<b>Yangi karta:</b>\nHozirgi: <code>{g_set('card')}</code>", parse_mode='HTML')
        
    elif "Murojaat o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_a"
        bot.send_message(m.chat.id, f"<b>Yangi admin @bilan:</b>\nHozirgi: {g_set('admin')}", parse_mode='HTML')  
        
    elif "Qo'llanma o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_guide"
        bot.send_message(m.chat.id, f"<b>Yangi video qo'llanmani yuboring:</b>", parse_mode='HTML')
        
    elif "2006-2009" in m.text or "2010-2019" in m.text:
        ch_type = "y1" if "2006-2009" in m.text else "y2"
        usr_st[m.from_user.id] = f"wac_{ch_type}"
        bot.send_message(m.chat.id, f"<b>Kanal ma'lumotlarini yuboring (Login:Parol):</b>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("edp_"))
def ed_p(c):
    bot.answer_callback_query(c.id)
    usr_st[c.from_user.id] = f"setp_{c.data[4:]}"
    bot.send_message(c.message.chat.id, f"<b>Yangi qiymatni yuboring (faqat raqam):</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)) in ["set_chan", "brd_msg", "add_adm", "set_c", "set_a"] or str(usr_st.get(m.from_user.id)).startswith("setp_") or str(usr_st.get(m.from_user.id)).startswith("wac_"))
def adm_st(m):
    st = str(usr_st.get(m.from_user.id))
    
    if st == "set_chan":
        u_set('m_chan', " " if m.text == "0" else m.text)
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Saqlandi!", parse_mode='HTML')
        
    elif st == "brd_msg":
        if m.text == "/cancel":
            usr_st[m.from_user.id] = None
            return bot.send_message(m.chat.id, "Xabarnoma bekor qilindi.")
            
        bot.send_message(m.chat.id, f"{ce_f('time', '⏳')} Yuborilmoqda...", parse_mode='HTML')
        def send_broadcast():
            sent = 0
            for x in users_db.find({}):
                try:
                    bot.copy_message(x["_id"], m.chat.id, m.message_id)
                    sent += 1
                    time.sleep(0.05)
                except:
                    pass
            try:
                bot.send_message(m.chat.id, f"✅ Xabarnoma {sent} ta foydalanuvchiga yuborildi!")
            except:
                pass
        threading.Thread(target=send_broadcast).start()
        
    elif st.startswith("setp_"):
        if m.text and m.text.isdigit():
            u_set(st[5:], m.text)
            bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Saqlandi!", parse_mode='HTML')
        else:
            return bot.send_message(m.chat.id, "❗ Faqat raqam yuboring!")
        
    elif st == "add_adm":
        if m.text and m.text.isdigit():
            admins_db.update_one({"_id": int(m.text)}, {"$set": {"_id": int(m.text)}}, upsert=True)
            bot.send_message(m.chat.id, "✅ Admin qo'shildi!")
        else:
            return bot.send_message(m.chat.id, "❗ Faqat ID raqam yuboring!")
        
    elif st == "set_c":
        u_set('card', m.text)
        bot.send_message(m.chat.id, "✅ Karta saqlandi!")
        
    elif st == "set_a":
        u_set('admin', m.text)
        bot.send_message(m.chat.id, "✅ Admin username saqlandi!")
        
    elif st.startswith("wac_"):
        accounts_db.insert_one({"type": st.split('_')[1], "data": m.text})
        bot.send_message(m.chat.id, "✅ Kanal bazaga muvaffaqiyatli qo'shildi!", reply_markup=a_menu())
        
    usr_st[m.from_user.id] = None

# To'lov qabul qilish tizimi
@bot.message_handler(func=lambda m: m.text and "Hisob to'ldirish" in m.text)
def tu(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
    usr_st[m.from_user.id] = "manual_amount"
    txt = f"""
{ce_f('card', '💳')} <b>Hisobni to'ldirish</b>
━━━━━━━━━━━━━━━━━━━━
💵 <b>Necha so'm to'ldirmoqchisiz?</b>

<i>Raqamni yozing (masalan: 50000)</i>
"""
    bot.send_message(m.chat.id, txt, parse_mode="HTML")

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'manual_amount')
def manual_amount(m):
    if m.text in ["Xizmatlar", "Nomer olish", "Tayyor Kanallar", "Buyurtmalarim", "Pul ishlash", "Mening hisobim", "Hisob to'ldirish", "Murojaat", "Qo'llab-quvvatlash", "Qo'llanma", "Hamkorlik", "Admin Panel", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        bot.send_message(m.chat.id, "To'lov kiritish bekor qilindi. Iltimos, tugmani yana bir bor bosing.", reply_markup=m_menu(m.from_user.id))
        return

    if not m.text or not m.text.isdigit():
        return bot.send_message(m.chat.id, "‼️ <b>Faqat raqamlardan foydalaning.</b>\n➡️ Masalan: 10000", parse_mode='HTML')

    amount = int(m.text)
    if amount < 1000:
        return bot.send_message(m.chat.id, "ℹ️ Minimal to'lov: 1,000 so'm")

    try:
        r = payments_db.insert_one({"user_id": m.from_user.id, "amount": amount, "status": "awaiting_receipt", "created_at": datetime.now()})
        usr_st[m.from_user.id] = f"receipt_{str(r.inserted_id)}"
        
        txt = (f"💳 <b>To'lovni amalga oshiring!</b>\n\n"
               f"➡️ <b>To'lov karta:</b> <code>{g_set('card')}</code>\n\n"
               f"💵 <b>Miqdori:</b> {amount:,} so'm\n\n"
               f"📸 <b>DIQQAT: To'lov qilib bo'lgach, albatta to'lov chekini (screenshot) shu yerga yuborishingiz SHART!</b>\n\n"
               f"❕ {amount:,} so'mdan ortiq yoki kam to'lov qilmang!")
               
        mk = IK(row_width=1)
        mk.add(IB("❌ To'lovni bekor qilish", callback_data="cancel_pay"))
        
        try:
            img = requests.get("https://i.postimg.cc/CKMwmCTY/IMG-20261006-235926-697.jpg", timeout=5).content
            bot.send_photo(m.chat.id, img, caption=txt, parse_mode='HTML', reply_markup=mk)
        except:
            bot.send_message(m.chat.id, txt, parse_mode='HTML', reply_markup=mk)
            
    except Exception as e:
        usr_st[m.from_user.id] = None
        bot.send_message(m.chat.id, f"Xatolik yuz berdi: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_pay")
def cancel_payment_cb(c):
    bot.answer_callback_query(c.id, "To'lov bekor qilindi.")
    usr_st[c.from_user.id] = None
    payments_db.update_many({"user_id": c.from_user.id, "status": "awaiting_receipt"}, {"$set": {"status": "cancelled"}})
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass
    bot.send_message(c.message.chat.id, "❌ <b>To'lov bekor qilindi.</b>", reply_markup=m_menu(c.from_user.id), parse_mode='HTML')

@bot.message_handler(content_types=["photo", "document"])
def receive_receipt_fallback(m):
    from bson import ObjectId
    st = str(usr_st.get(m.from_user.id, ""))
    oid = None
    
    if st.startswith("receipt_"):
        try:
            oid = ObjectId(st[8:])
        except:
            oid = None
    else:
        # Agar server restart bo'lib RAM o'chgan bo'lsa ham bazadan oxirgi kutilayotgan to'lovni topadi
        last_pay = payments_db.find_one({"user_id": m.from_user.id, "status": "awaiting_receipt"}, sort=[("created_at", -1)])
        if last_pay:
            oid = last_pay["_id"]
            
    if not oid:
        return
        
    fid = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id
    receipt_kind = "photo" if m.content_type == "photo" else "document"
    
    pay = payments_db.find_one_and_update(
        {"_id": oid, "status": "awaiting_receipt"},
        {"$set": {"status": "pending_admin", "receipt_file_id": fid, "receipt_kind": receipt_kind}}
    )
    if not pay:
        return bot.send_message(m.chat.id, "Ariza topilmadi yoki allaqachon yuborilgan.")
        
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, f"{ce_f('check', '✅')} <b>Chek qabul qilindi!</b>\n⏳ Admin tekshiradi. 5-30 daqiqa ichida javob beramiz.", parse_mode="HTML")
    
    pid = str(oid)
    kb = IK(row_width=2).add(
        IB("✅ TASDIQLASH", callback_data=f"pay_ok_{pid}"),
        IB("❌ RAD ETISH", callback_data=f"pay_no_{pid}")
    )
    
    cap = f"""
💳 <b>YANGI TO'LOV CHEKI</b>
👤 User: <code>{m.from_user.id}</code>
💵 Summa: <b>{int(pay['amount']):,} so'm</b>
📅 Sana: {datetime.now().strftime('%Y.%m.%d %H:%M')}
"""
    for aid in g_adms():
        try:
            if receipt_kind == "photo":
                bot.send_photo(aid, fid, caption=cap, reply_markup=kb, parse_mode="HTML")
            else:
                bot.send_document(aid, fid, caption=cap, reply_markup=kb, parse_mode="HTML")
        except:
            pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_ok_") or c.data.startswith("pay_no_"))
def admin_pay_ok_no(c):
    if not is_adm(c.from_user.id):
        return bot.answer_callback_query(c.id, "Ruxsat yo'q.")
        
    from bson import ObjectId
    action = "paid" if c.data.startswith("pay_ok_") else "rejected"
    pid = c.data[7:]
    
    pay = payments_db.find_one_and_update({"_id": ObjectId(pid), "status": "pending_admin"}, {"$set": {"status": action, "time": int(time.time())}})
    if not pay:
        return bot.answer_callback_query(c.id, "Bu to'lov allaqachon yopilgan.")
        
    uid = int(pay["user_id"])
    amount = int(pay["amount"])
    
    if action == "paid":
        u_bal(uid, amount)
        users_db.update_one({"_id": uid}, {"$inc": {"total_deposited": amount}}, upsert=True)
        
        u_doc = users_db.find_one({"_id": uid})
        ref = u_doc.get("r", 0) if u_doc else 0
        if ref and int(amount * 0.05) > 0:
            u_bal(ref, int(amount * 0.05))
            try:
                bot.send_message(ref, f"🎁 <b>Referal bonus!</b>\nSizning taklifingiz orqali to'lov amalga oshirildi. Sizga <b>{int(amount * 0.05):,} so'm</b> berildi!", parse_mode='HTML')
            except:
                pass
        try:
            bot.send_message(uid, f"✅ <b>To'lov tasdiqlandi!</b>\n💵 Balansingizga <b>{amount:,} so'm</b> qo'shildi.", parse_mode='HTML')
        except:
            pass
            
        status_t = "✅ <b>STATUS: TASDIQLANDI</b>"
    else:
        try:
            bot.send_message(uid, f"❌ <b>To'lov rad etildi.</b>\n💵 Summa: {amount:,} so'm", parse_mode='HTML')
        except:
            pass
        status_t = "❌ <b>STATUS: RAD ETILDI</b>"
        
    cap = c.message.caption if c.message.caption else "To'lov"
    try:
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=cap + f"\n\n{status_t}", parse_mode='HTML')
    except:
        pass

@bot.message_handler(content_types=['video', 'text'], func=lambda m: usr_st.get(m.from_user.id) == "set_guide")
def save_guide_video(m):
    if m.content_type == 'video':
        u_set('guide_vid', m.video.file_id)
        u_set('guide_txt', m.caption if m.caption else "🤖 Botingizdan foydalanish bo'yicha qisqacha qo'llanma.")
        usr_st[m.from_user.id] = None
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} <b>Qo'llanma saqlandi!</b>", parse_mode='HTML')
    else:
        if m.text == "/cancel":
            usr_st[m.from_user.id] = None
            return bot.send_message(m.chat.id, "Bekor qilindi.")
        bot.send_message(m.chat.id, "‼️ Faqat VIDEO yuboring (/cancel - bekor qilish).")

# Grizzly Nomer olish qismi (TO'G'RILANDI: RUB kursi va davlat foizlari)
C_LIST = [
    ("0", "Rossiya 🇷🇺"), ("1", "Ukraina 🇺🇦"), ("2", "Qozog'iston 🇰🇿"), ("12", "AQSh 🇺🇸"),
    ("36", "Kanada 🇨🇦"), ("81", "Argentina (Gmail) 🇦🇷"), ("16", "Angliya 🇬🇧"), ("6", "Indoneziya 🇮🇩"),
    ("3", "Xitoy 🇨🇳"), ("4", "Filippin 🇵🇭"), ("5", "Myanma 🇲🇲"), ("7", "Malayziya 🇲🇾"),
    ("31", "JAR 🇿🇦"), ("34", "Estoniya 🇪🇪"), ("73", "Braziliya 🇧🇷"), ("21", "Ispaniya 🇪🇸")
]
S_LIST = [("vk", "VKontakte"), ("go", "Google"), ("yt", "YouTube"), ("fb", "Facebook"), ("ig", "Instagram"), ("dt", "TikTok"), ("wa", "WhatsApp")]

@bot.callback_query_handler(func=lambda c: c.data == "margin_countries")
def margin_countries_menu(c):
    bot.answer_callback_query(c.id)
    mk = IK(row_width=2)
    btns = []
    for cid, cname in C_LIST:
        val = g_set(f'm_num_{cid}')
        d_val = f"{val}%" if val != " " else "Standart"
        btns.append(IB(f"{cname} ({d_val})", callback_data=f"edp_m_num_{cid}"))
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
    bot.edit_message_text("🌍 <b>Qaysi davlat foizini o'zgartirasiz?</b>\n<i>Eslatma: 'Standart' turgan davlatlar Umumiy Nomerlar foizini ishlatadi.</i>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text and "Nomer olish" in m.text)
def nm(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
    txt = f"{ce_f('phone3', '📱')} <b>Virtual Nomer Xizmati</b>\n👇 <b>Bo'limni tanlang:</b>"
    mk = IK(row_width=2).add(
        IB("📞 Telegram", callback_data="tg_p_0"),
        IB("☎️ Boshqa Tarmoqlar", callback_data="ot_p_0"),
        IB("⭐ TOP davlatlar", callback_data="tg_top")
    )
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')

def gen_page(prefix, sc, page, c_id, msg_id):
    pr = get_gz_pr(sc=sc)
    gk = g_k("RUB", 140.0) # TO'G'RILANDI: Grizzly narxlari RUB da keladi
    mk = IK(row_width=2)
    btns = []
    
    for cid, cname in C_LIST[page*8:page*8+8]:
        cost = pr.get(cid)
        if cost:
            cmv = get_country_m(cid)
            price_uzs = int(cost * gk * cmv)
            btns.append(IB(f"{cname} - {price_uzs:,} so'm", callback_data=f"buy_{sc}_{cid}_{price_uzs}"))
        else:
            btns.append(IB(f"{cname} (Yo'q)", callback_data="none"))
            
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
        
    tp = (len(C_LIST) + 7) // 8
    mk.row(
        IB("⬅️", callback_data=f"{prefix}_p_{page-1}") if page > 0 else IB("➖", callback_data="none"),
        IB(f"{page+1}/{tp}", callback_data="none"),
        IB("➡️", callback_data=f"{prefix}_p_{page+1}") if page < tp - 1 else IB("➖", callback_data="none")
    )
    mk.add(IB("⭐ TOP DAVLATLAR", callback_data=f"{prefix}_top"))
    
    try:
        bot.edit_message_text(f"🌍 <b>Davlatni tanlang:</b>\n\n<i>Sahifa {page+1}/{tp}</i>", c_id, msg_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

def gen_top(prefix, sc, c_id, msg_id):
    pr = get_gz_pr(sc=sc)
    gk = g_k("RUB", 140.0) # TO'G'RILANDI: RUB kursi va get_country_m saqlandi
    valid_c = []
    
    for cid, cname in C_LIST:
        if cid in pr:
            valid_c.append((cid, cname, pr[cid]))
            
    mk = IK(row_width=2)
    btns = []
    
    for cid, cname, p_rub in sorted(valid_c, key=lambda x: x[2])[:6]:
        cmv = get_country_m(cid)
        price_uzs = int(p_rub * gk * cmv)
        btns.append(IB(f"{cname} - {price_uzs:,} so'm", callback_data=f"buy_{sc}_{cid}_{price_uzs}"))
        
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
        
    mk.add(IB("🔙 Orqaga", callback_data=f"{prefix}_p_0"))
    
    try:
        bot.edit_message_text("⭐ <b>TOP 6 eng arzon davlatlar:</b>", c_id, msg_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("tg_p_"))
def tg_pg(c):
    bot.answer_callback_query(c.id)
    gen_page("tg", "tg", int(c.data.split('_')[2]), c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "tg_top")
def tg_top(c):
    bot.answer_callback_query(c.id)
    gen_top("tg", "tg", c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ot_p_") or c.data == "ot_top")
def ot_pg_top(c):
    bot.answer_callback_query(c.id)
    mk = IK(row_width=2)
    
    if c.data == "ot_top":
        top_c = [("0", "Rossiya 🇷🇺"), ("2", "Qozog'iston 🇰🇿"), ("12", "AQSh 🇺🇸"), ("36", "Kanada 🇨🇦"), ("81", "Argentina 🇦🇷"), ("16", "Angliya 🇬🇧")]
        btns = []
        for cid, cname in top_c:
            btns.append(IB(f"{cname}", callback_data=f"ot_c_{cid}"))
        for i in range(0, len(btns), 2):
            mk.row(*btns[i:i+2])
        mk.add(IB("🔙 Orqaga", callback_data="ot_p_0"))
        bot.edit_message_text("⭐ <b>TOP davlatlar:</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    else:
        page = int(c.data.split('_')[2])
        btns = []
        for cid, cname in C_LIST[page*8:page*8+8]:
            btns.append(IB(f"{cname}", callback_data=f"ot_c_{cid}"))
        for i in range(0, len(btns), 2):
            mk.row(*btns[i:i+2])
            
        tp = (len(C_LIST) + 7) // 8
        mk.row(
            IB("⬅️", callback_data=f"ot_p_{page-1}") if page > 0 else IB("➖", callback_data="none"),
            IB(f"{page+1}/{tp}", callback_data="none"),
            IB("➡️", callback_data=f"ot_p_{page+1}") if page < tp - 1 else IB("➖", callback_data="none")
        )
        mk.add(IB("⭐ TOP DAVLATLAR Ro'yxati", callback_data="ot_top"))
        bot.edit_message_text(f"🌍 <b>Davlatni tanlang:</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("ot_c_"))
def ot_c_sel(c):
    bot.answer_callback_query(c.id)
    cid = c.data.split('_')[2]
    cname = dict(C_LIST).get(cid, "Noma'lum")
    
    try:
        bot.edit_message_text(f"{ce_f('time', '⏳')} Yuklanmoqda...", c.message.chat.id, c.message.message_id, parse_mode='HTML')
    except:
        pass
        
    pr = get_gz_pr(cid=cid)
    gk = g_k("RUB", 140.0) # TO'G'RILANDI: RUB kursi
    cmv = get_country_m(cid)
    
    if not pr:
        try:
            bot.edit_message_text(f"❌ <b>Nomerlar yo'q.</b>", c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="ot_p_0")), parse_mode='HTML')
        except:
            pass
        return
    
    txt = f"🛍 <b>Tarmoqni tanlang:</b>\n♻️ <b>Davlat: {cname}</b>\n\n"
    mk = IK(row_width=2)
    btns = []
    
    for sc, sname in S_LIST:
        cost = pr.get(sc)
        if cost:
            price_uzs = int(cost * gk * cmv)
            txt += f"🔹 <b>{sname}</b> - {price_uzs:,} so'm\n"
            btns.append(IB(f"{sname} - {price_uzs:,} so'm", callback_data=f"buy_{sc}_{cid}_{price_uzs}"))
        else:
            btns.append(IB(f"{sname} (Yo'q)", callback_data="none"))
            
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
        
    mk.add(IB("🔙 Orqaga", callback_data="ot_p_0"))
    
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def pb(c):
    p = c.data.split('_')
    sc = p[1]
    cid = p[2]
    pr = int(p[3])
    
    if g_bal(c.from_user.id) < pr:
        return bot.answer_callback_query(c.id, "🔴 Balansingiz yetarli emas!", show_alert=True)
        
    try:
        bot.edit_message_text(f"{ce_f('time', '⏳')} Olinmoqda...", c.message.chat.id, c.message.message_id, parse_mode='HTML')
    except:
        pass
        
    r = req_gz(sc, cid)
    if r["s"]:
        u_bal(c.from_user.id, -pr)
        orders_db.insert_one({
            "user_id": c.from_user.id,
            "oid": f"GZ_{r['id']}",
            "gz_id": str(r['id']),
            "price": pr,
            "link": r['n'],
            "quantity": 1,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            "status": "SMS kutilmoqda"
        })
        mk = IK().add(
            IB("🔎 SMS olish", callback_data=f"ck_{r['id']}_{pr}"),
            IB("❌ Bekor qilish", callback_data=f"cl_{r['id']}_{pr}")
        )
        try:
            bot.edit_message_text(f"✅ <b>Xarid qilindi!</b>\n\n📱 <b>Nomer:</b> <code>{r['n']}</code>\n💵 Yechildi: {pr:,} so'm", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
        except:
            pass
    else:
        try:
            bot.edit_message_text(f"❌ <b>{r['m']}</b>", c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="ot_p_0")), parse_mode='HTML')
        except:
            pass

# TO'G'RILANDI: Nomer bekor qilishda ikki marta pul qaytishi va EARLY_CANCEL_DENIED exploit yopildi
@bot.callback_query_handler(func=lambda c: c.data.startswith("ck_") or c.data.startswith("cl_"))
def ck_cl(c):
    p = c.data.split('_')
    gz_id = str(p[1])
    pr = int(p[2])
    
    if p[0] == "ck":
        bot.answer_callback_query(c.id, "Tekshirilmoqda...")
        code, body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "getStatus", "id": gz_id}, timeout=15)
        
        if body.startswith("STATUS_WAIT") or "WAIT" in body:
            mk = IK().add(
                IB("🔎 SMS olish", callback_data=f"ck_{gz_id}_{pr}"),
                IB("❌ Bekor qilish", callback_data=f"cl_{gz_id}_{pr}")
            )
            try:
                bot.edit_message_text(f"⏳ <b>SMS kutilmoqda...</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
            except:
                pass
                
        elif body.startswith("STATUS_OK") or body.startswith("OK:"):
            sms_code = body.split(':')[1] if ':' in body else body.replace('OK:', '')
            orders_db.update_one({"gz_id": gz_id}, {"$set": {"status": "Bajarildi ✅"}})
            try:
                bot.edit_message_text(f"✅ <b>SMS KOD KELDI!</b>\n\n🔑 <b>KOD:</b> <code>{sms_code}</code>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            except:
                pass
        elif "STATUS_CANCEL" in body:
            try:
                bot.edit_message_text("❌ <b>Ushbu nomer bekor qilingan.</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            except:
                pass
        else:
            mk = IK().add(
                IB("🔎 SMS olish", callback_data=f"ck_{gz_id}_{pr}"),
                IB("❌ Bekor qilish", callback_data=f"cl_{gz_id}_{pr}")
            )
            try:
                bot.edit_message_text(f"⏳ <b>Holat: {body[:50]}</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
            except:
                pass
                
    elif p[0] == "cl":
        ord_doc = orders_db.find_one({"gz_id": gz_id})
        if ord_doc and ord_doc.get("status") in ["Bekor qilindi ❌", "Bajarildi ✅"]:
            return bot.answer_callback_query(c.id, "Bu nomer allaqachon yakunlangan yoki bekor qilingan!", show_alert=True)
            
        code, cancel_body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "setStatus", "status": 8, "id": gz_id}, timeout=15)
        
        if "ACCESS_CANCEL" in cancel_body:
            bot.answer_callback_query(c.id, "Nomer bekor qilindi!")
            res_upd = orders_db.find_one_and_update(
                {"gz_id": gz_id, "status": "SMS kutilmoqda"},
                {"$set": {"status": "Bekor qilindi ❌"}}
            )
            if res_upd or not ord_doc:
                u_bal(c.from_user.id, pr)
            try:
                bot.edit_message_text(f"✅ <b>Nomer bekor qilindi!</b>\n💵 <b>Pul hisobingizga to'liq qaytarildi:</b> {pr:,} so'm", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            except:
                pass
        elif "EARLY_CANCEL_DENIED" in cancel_body:
            bot.answer_callback_query(c.id, "⏳ Xarid qilinganidan so'ng kamida 2 daqiqa o'tgach bekor qilish mumkin!", show_alert=True)
        else:
            bot.answer_callback_query(c.id, "⏳ Hozircha bekor qilib bo'lmadi, birozdan so'ng urinib ko'ring.", show_alert=True)

# Tayyor Kanallar
@bot.message_handler(func=lambda m: m.text and "Tayyor Kanallar" in m.text)
def yt_channels(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    user = users_db.find_one({"_id": m.from_user.id})
    has_sk = user.get("skidka") if user else False
    
    txt = f"{ce_f('youtube', '▶️')} <b>Tayyor YouTube Kanallar Do'koni</b>\n👇 <b>Kanal turini tanlang:</b>"
    mk = IK(row_width=1)
    
    count_y1 = g_c('y1')
    count_y2 = g_c('y2')
    
    for k, n, c in [("y1", "🔴 [ESKI] 2006-09", count_y1), ("y2", "🟠 [ESKI] 2010-19", count_y2)]:
        try:
            p = int(g_set('p_' + k))
        except:
            p = 190000 if k == 'y1' else 120000
            
        if has_sk:
            mk.add(IB(f"{n} - {p-15000:,} so'm (Skidka) [{c} ta]", callback_data=f"by_{k}"))
        else:
            mk.add(IB(f"{n} - {p:,} so'm [{c} ta]", callback_data=f"by_{k}"))
            
    try:
        p_2func = int(g_set('p_2func'))
    except:
        p_2func = 100000
        
    mk.add(IB(f"🛠 2 funksiya - {p_2func:,} so'm", callback_data="by_n_2func"))
    
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')
    
@bot.callback_query_handler(func=lambda c: c.data.startswith("by_"))
def b_yt(c):
    try:
        t = c.data.split('_')
        user = users_db.find_one({"_id": c.from_user.id})
        has_sk = user.get("skidka") if user else False
        
        if t[1] == "n":
            pr = int(g_set('p_' + t[2]))
            if g_bal(c.from_user.id) < pr:
                return bot.answer_callback_query(c.id, "🔴 Balansingiz yetarli emas!", show_alert=True)
                
            u_bal(c.from_user.id, -pr)
            usr_st[c.from_user.id] = f"wn_{t[2]}"
            bot.edit_message_text("🛠 <b>Ma'lumot yuboring (Yo'nalish/Link):</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            
        else:
            pr = int(g_set('p_' + t[1]))
            if has_sk:
                pr -= 15000
                
            if g_bal(c.from_user.id) < pr:
                return bot.answer_callback_query(c.id, "🔴 Balansingiz yetarli emas!", show_alert=True)
                
            u_bal(c.from_user.id, -pr)
            acc = accounts_db.find_one_and_delete({"type": t[1]})
            
            if acc:
                orders_db.insert_one({"user_id": c.from_user.id, "oid": "YT_AUTO", "link": t[1], "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Bajarildi ✅"})
                bot.edit_message_text(f"✅ <b>KANAL XARID QILINDI:</b>\n<code>{acc['data']}</code>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            else:
                orders_db.insert_one({"user_id": c.from_user.id, "oid": "YT", "link": t[1], "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Kutmoqda"})
                bot.edit_message_text(f"✅ <b>Buyurtma qabul qilindi! Tez orada admin kanal ma'lumotlarini yuboradi.</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
                adm_msg(f"🔔 <b>YANGI KANAL BUYURTMASI:</b>\n👤 Mijoz ID: <code>{c.from_user.id}</code>\n📦 Turi: {t[1]}", rm=IK().add(IB("📤 Yuborish", callback_data=f"snd_{c.from_user.id}")))
                
    except Exception as e:
        print(f"Tayyor kanallar xatosi: {e}")

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)).startswith("wn_"))
def sv_nch(m):
    t = usr_st[m.from_user.id].split('_')[1]
    if m.text in ["Xizmatlar", f"{E_BAG} Xizmatlar", "🏠 Bosh sahifa"]:
        u_bal(m.from_user.id, int(g_set('p_' + t)))
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Bekor qilindi. Pul qaytdi.", reply_markup=m_menu(m.from_user.id))
        
    orders_db.insert_one({"user_id": m.from_user.id, "oid": t, "link": m.text[:50], "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Kutmoqda"})
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, f"✅ <b>Qabul qilindi! Admin tez orada natijani yuboradi.</b>", parse_mode='HTML')
    
    adm_msg(f"🔔 <b>YANGI XIZMAT BUYURTMASI ({t}):</b>\n👤 Mijoz ID: <code>{m.from_user.id}</code>\n📝 Ma'lumoti:\n<code>{m.text}</code>", rm=IK().add(IB("📤 Yuborish", callback_data=f"snd_{m.from_user.id}")))

@bot.callback_query_handler(func=lambda c: c.data.startswith("snd_"))
def rq_snd(c):
    bot.answer_callback_query(c.id)
    usr_st[c.from_user.id] = f"fw_{c.data.split('_')[1]}"
    bot.send_message(c.message.chat.id, f"<b>Mijozga yuboriladigan ma'lumotni kiriting:</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)).startswith("fw_"))
def fw_m(m):
    uid = int(usr_st[m.from_user.id].split('_')[1])
    usr_st[m.from_user.id] = None
    try:
        bot.send_message(uid, f"🎁 <b>Buyurtmangiz tayyor:</b>\n<code>{m.text}</code>", parse_mode='HTML')
        bot.send_message(m.chat.id, "✅ Mijozga yuborildi!")
        orders_db.update_one({"user_id": uid, "status": "Kutmoqda"}, {"$set": {"status": "Bajarildi ✅"}})
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Xatolik: {e}")

# SMM Xizmatlar Qismi
def smm_main_kb():
    return IK(row_width=2).add(
        IB("Telegram", callback_data="mp_tg", icon_custom_emoji_id="5456281420106315074"),
        IB("Instagram", callback_data="mp_ig", icon_custom_emoji_id="5319160079465857105"),
        IB("TikTok", callback_data="mp_tt", icon_custom_emoji_id="5327982530702359565"),
        IB("YouTube", callback_data="mp_yt", icon_custom_emoji_id="5456299961480132196"),
        IB("🔍 Qidirish", callback_data="search_services"),
        IB("🛒 Barcha xizmatlar", callback_data="all_services")
    )

@bot.message_handler(func=lambda m: m.text and "Xizmatlar" in m.text and "Tayyor" not in m.text)
def smm_services(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    txt = f"🛍 <b>@{bot.get_me().username} sizga Tezkor, Arzon va Sifatli xizmatlarni taqdim etadi!</b>"
    bot.send_message(m.chat.id, txt, reply_markup=smm_main_kb(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "back_smm_main")
def back_smm_main_cb(c):
    bot.answer_callback_query(c.id)
    txt = f"🛍 <b>@{bot.get_me().username} sizga Tezkor, Arzon va Sifatli xizmatlarni taqdim etadi!</b>"
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=smm_main_kb(), parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data in ["search_services", "all_services"])
def s_all(c):
    bot.answer_callback_query(c.id)
    if c.data == "search_services":
        usr_st[c.from_user.id] = "search_mode"
        bot.send_message(c.message.chat.id, "🔍 <b>Xizmat nomini yozing:</b>", parse_mode='HTML')
    else:
        services = g_smm()
        txt = f"🛒 <b>Barcha xizmatlar ({len(services)} ta):</b>\n\n"
        mk = IK(row_width=1)
        gk = g_k("USD", 12700)
        for s in services:
            cat = s.get('category', '')
            mv = get_m('m_yt_sub') if 'youtube sub' in cat else (get_m('m_yt_watch') if 'youtube watch' in cat else get_m('m_smm'))
            try: pr_uzs = int(float(str(s.get('rate', '0')).replace(',','.')) * gk * mv)
            except: pr_uzs = 0
            mk.add(IB(f"🔹 {s['name']} - {pr_uzs:,} so'm", callback_data=f"sq_{s['service']}_all"))
        mk.add(IB("🔙 Orqaga", callback_data="back_smm_main"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == "search_mode")
def search_handler(m):
    if m.text in ["Xizmatlar", f"{E_BAG} Xizmatlar", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Bekor qilindi.", reply_markup=m_menu(m.from_user.id))
        
    usr_st[m.from_user.id] = None
    query = m.text.lower()
    results = [s for s in g_smm() if query in s['name'].lower() or query in s['category'].lower()]
    
    if not results:
        return bot.send_message(m.chat.id, f"❌ <b>Xizmat topilmadi.</b>", parse_mode='HTML')
        
    txt = f"🔍 <b>Qidiruv natijasi: '{m.text}'</b>\nTopildi: <b>{len(results)}</b> ta\n\n"
    mk = IK(row_width=1)
    gk = g_k("USD", 12700)
    for s in results[:15]:
        cat = s.get('category', '')
        mv = get_m('m_yt_sub') if 'youtube sub' in cat else (get_m('m_yt_watch') if 'youtube watch' in cat else get_m('m_smm'))
        try: pr_uzs = int(float(str(s.get('rate', '0')).replace(',','.')) * gk * mv)
        except: pr_uzs = 0
        mk.add(IB(f"🔹 {s['name']} - {pr_uzs:,} so'm", callback_data=f"sq_{s['service']}_search"))
    mk.add(IB("🔙 Orqaga", callback_data="back_smm_main"))
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("mp_"))
def smc(c):
    bot.answer_callback_query(c.id)
    p = c.data.split('_')[1]
    mk = IK(row_width=1)
    
    if p == 'yt':
        opts = [("sub", "👥 Obunachilar"), ("watch", "⏱ Watchtime"), ("view", "👁 Ko'rishlar"), ("like", "❤️ Layklar"), ("comment", "💬 Kommentariya")]
    elif p == 'tg':
        opts = [("sub", "👥 Obunachilar"), ("view", "👁 Ko'rishlar"), ("like", "❤️ Layklar / Reaksiyalar")]
    else:
        opts = [("sub", "👥 Obuna"), ("view", "👁 Ko'rish"), ("like", "❤️ Layk"), ("comment", "💬 Kommentariya")]
        
    for cid, cn in opts:
        mk.add(IB(cn, callback_data=f"mc_{p}_{cid}"))
        
    mk.add(IB("🔙 Orqaga", callback_data="back_smm_main"))
    try:
        bot.edit_message_text(f"📌 <b>Bo'limni tanlang:</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("mc_"))
def n_ss(c):
    bot.answer_callback_query(c.id)
    parts = c.data.split('_')
    p = parts[1]
    cid = parts[2]
    
    cat_map = {
        'yt_sub': 'youtube sub follower', 'yt_watch': 'youtube watch time hour', 'yt_view': 'youtube view', 'yt_like': 'youtube like', 'yt_comment': 'youtube comment',
        'tg_sub': 'telegram sub follower', 'tg_view': 'telegram view', 'tg_like': 'telegram like',
        'ig_sub': 'instagram sub follower', 'ig_view': 'instagram view', 'ig_like': 'instagram like', 'ig_comment': 'instagram comment',
        'tt_sub': 'tiktok sub follower', 'tt_view': 'tiktok view', 'tt_like': 'tiktok like', 'tt_comment': 'tiktok comment'
    }
    
    target_cat = cat_map.get(f"{p}_{cid}")
    f = [x for x in g_smm() if x.get('category') == target_cat]
    
    if not f:
        return bot.answer_callback_query(c.id, "Xizmat topilmadi", show_alert=True)
        
    def safe_float(v):
        try:
            return float(str(v).replace(',','.'))
        except:
            return 0.0
            
    f = sorted(f, key=lambda x: safe_float(x.get('rate', '0')))
    mv = get_m('m_yt_sub') if (p == 'yt' and cid == 'sub') else (get_m('m_yt_watch') if (p == 'yt' and cid == 'watch') else get_m('m_smm'))
    gk = g_k("USD", 12700)
    mk = IK(row_width=1)
    txt = f"🛍 <b>Xizmat va sifatni tanlang:</b>\n\n"
    
    labels = ["🥈 Arzon", "🥇 Tezkor", "💎 Premium", "🔥 VIP", "🚀 Super", "⭐ Maxsus"]
    for idx, srv in enumerate(f):
        lbl = f"{labels[idx]} ({srv['name']})" if idx < len(labels) else srv['name']
        price_uzs = int(safe_float(srv.get('rate', '0')) * gk * mv)
        is_pkg = (int(srv.get('min', 0)) == 1 and int(srv.get('max', 0)) == 1)
        unit_txt = "1 paket" if is_pkg else "1000 ta"
        txt += f"🔹 <b>{lbl}</b>\n   💵 {price_uzs:,} so'm ({unit_txt})\n   📉 Min: {srv.get('min')} | Max: {srv.get('max')}\n\n"
        mk.add(IB(f"{lbl} - {price_uzs:,} so'm", callback_data=f"sq_{srv['service']}_{cid}"))
        
    mk.add(IB("🔙 Orqaga", callback_data=f"mp_{p}"))
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

# TO'G'RILANDI: Dublikat sq_sel olib tashlandi va paketli (min=1, max=1) xizmatlar tahlili qo'shildi
@bot.callback_query_handler(func=lambda c: c.data.startswith("sq_"))
def sq_sel(c):
    bot.answer_callback_query(c.id)
    parts = c.data.split('_')
    sid = parts[1]
    
    srv = next((x for x in g_smm() if str(x.get('service')) == sid), None)
    if not srv:
        return bot.answer_callback_query(c.id, "Xizmat topilmadi")
        
    cat = srv.get('category', '')
    mv = get_m('m_yt_sub') if 'youtube sub' in cat else (get_m('m_yt_watch') if 'youtube watch' in cat else get_m('m_smm'))
    
    def safe_float(v):
        try:
            return float(str(v).replace(',','.'))
        except:
            return 0.0
            
    pr = int(safe_float(srv.get('rate', '0')) * g_k("USD", 12700) * mv)
    min_q = int(srv.get('min', 10))
    max_q = int(srv.get('max', 10000))
    is_pkg = (min_q == 1 and max_q == 1)
    unit_txt = "1 paket" if is_pkg else "1000 ta"
    
    txt = f"🛍 <b>Tanlandi: {srv['name']}</b>\n💵 <b>Narx:</b> {pr:,} so'm ({unit_txt})\n📉 <b>Min:</b> {min_q} | <b>Max:</b> {max_q}\n\n🔗 <b>Link yuboring:</b>"
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode='HTML')
    except:
        pass
        
    usr_st[c.from_user.id] = 'wl'
    tmp_dt[c.from_user.id] = {'s': sid, 'p': pr, 'm': min_q, 'x': max_q, 'pkg': is_pkg}

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'wl')
def pl(m):
    if m.text in ["Xizmatlar", "Nomer olish", "Tayyor Kanallar", "Buyurtmalarim", "Pul ishlash", "Mening hisobim", "Hisob to'ldirish", "Murojaat", "Qo'llab-quvvatlash", "Qo'llanma", "Hamkorlik", "Admin Panel", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Buyurtma bekor qilindi.", reply_markup=m_menu(m.from_user.id))
        
    tmp_dt[m.from_user.id]['l'] = m.text
    usr_st[m.from_user.id] = 'wq'
    d = tmp_dt[m.from_user.id]
    if d.get('pkg'):
        bot.send_message(m.chat.id, f"🔢 <b>Paket sonini kiriting (1 yozing):</b>", parse_mode='HTML')
    else:
        bot.send_message(m.chat.id, f"🔢 <b>Qancha kerak? (Min: {d['m']}, Max: {d['x']}):</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'wq')
def pq(m):
    if m.text in ["Xizmatlar", "Nomer olish", "Tayyor Kanallar", "Buyurtmalarim", "Pul ishlash", "Mening hisobim", "Hisob to'ldirish", "Murojaat", "Qo'llab-quvvatlash", "Qo'llanma", "Hamkorlik", "Admin Panel", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Buyurtma bekor qilindi.", reply_markup=m_menu(m.from_user.id))
        
    if not m.text or not m.text.isdigit():
        return bot.send_message(m.chat.id, "❗ Faqat raqam yozing!")
        
    q = int(m.text)
    d = tmp_dt.get(m.from_user.id)
    
    if not d:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Xato! Boshqatdan kiring.")
        
    # TO'G'RILANDI: Paket xizmatlarda (min=1, max=1) narx 1000 ga bo'linmaydi
    if d.get('pkg'):
        t = int(d['p'] * q)
    else:
        t = int((d['p'] / 1000.0) * q)
    
    if q < d['m'] or q > d['x']:
        return bot.send_message(m.chat.id, f"⚠️ Limit xato! Minimal: {d['m']}, Maksimal: {d['x']}")
        
    if g_bal(m.from_user.id) < t:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, f"⚠️ Balansingiz yetarli emas!\nKerak: {t:,} so'm\nBalans: {g_bal(m.from_user.id):,} so'm")
        
    u_bal(m.from_user.id, -t)
    bot.send_message(m.chat.id, f"⏳ Saytga yuborilmoqda...", parse_mode='HTML')
    
    try:
        r = requests.get(SMM_API_URL, params={'key': SMM_API_KEY, 'act': 'new_order', 'service_id': d['s'], 'link': d['l'], 'count': q}, timeout=20).json()
        
        if 'res' in r and isinstance(r['res'], dict) and r['res'].get('status') == 'ok':
            oid = str(r['res'].get('order_id', 'N/A'))
            bot.send_message(m.chat.id, f"✅ <b>Buyurtma qabul qilindi!</b>\n🆔 Buyurtma ID: <code>{oid}</code>\n💵 To'langan: {t:,} so'm", parse_mode='HTML')
            orders_db.insert_one({"user_id": m.from_user.id, "oid": oid, "link": d['l'], "quantity": q, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Yuborildi"})
        else:
            u_bal(m.from_user.id, t)
            bot.send_message(m.chat.id, f"❌ Xatolik yuz berdi (Pul balansingizga qaytarildi): {r}", parse_mode='HTML')
            
    except Exception as e:
        u_bal(m.from_user.id, t)
        bot.send_message(m.chat.id, f"⚠️ Tizim xatosi yuz berdi. Pul balansingizga qaytarildi.", parse_mode='HTML')
        
    usr_st[m.from_user.id] = None

# Fallback handler
@bot.message_handler(content_types=['text'])
def fallback_text_handler(m):
    if m.text and not m.text.startswith('/'):
        bot.send_message(m.chat.id, "🤖 Kechirasiz, faqat menyudagi tugmalardan foydalaning.", reply_markup=m_menu(m.from_user.id))

# Web Server va Telegram Mini App (WebApp) qismi (Flask 24/7)
app = Flask(__name__)

MINI_APP_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>PRO SMM Market — Mini App</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #07090e;
  --card: rgba(18, 24, 38, 0.9);
  --border: rgba(255, 255, 255, 0.08);
  --accent: #6366f1;
  --accent-glow: rgba(99, 102, 241, 0.35);
  --accent2: #8b5cf6;
  --green: #10b981;
  --red: #ef4444;
  --text: #f8fafc;
  --muted: #94a3b8;
}
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; -webkit-tap-highlight-color: transparent; }
body { background: var(--bg); color: var(--text); padding-bottom: 96px; overflow-x: hidden; min-height: 100vh; }

.header {
  background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.15));
  border-bottom: 1px solid var(--border);
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(16px);
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo {
  width: 42px; height: 42px; border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; box-shadow: 0 4px 20px var(--accent-glow);
}
.brand-title { font-size: 16px; font-weight: 800; letter-spacing: -0.3px; }
.brand-sub { font-size: 11px; color: var(--muted); font-weight: 500; }

.bal-pill {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 8px 14px;
  border-radius: 14px;
  text-align: right;
  cursor: pointer;
  transition: 0.2s;
}
.bal-pill:active { transform: scale(0.95); }
.bal-lbl { font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; color: #6ee7b7; display: block; font-weight: 700; }
.bal-val { font-size: 14px; font-weight: 800; color: #34d399; }

.container { padding: 16px; }
.tab-content { display: none; animation: fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1); }
.tab-content.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
  margin-bottom: 14px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  backdrop-filter: blur(12px);
}
.sec-title { font-size: 16px; font-weight: 800; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; letter-spacing: -0.2px; }

.pills { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 14px; scrollbar-width: none; }
.pills::-webkit-scrollbar { display: none; }
.pill {
  padding: 9px 16px; border-radius: 99px; font-size: 12px; font-weight: 700;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border);
  color: var(--muted); white-space: nowrap; cursor: pointer; transition: 0.2s;
}
.pill.active {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #fff; border-color: transparent; box-shadow: 0 4px 16px var(--accent-glow);
}

.input, select {
  width: 100%; padding: 14px 16px; border-radius: 14px;
  background: rgba(11, 15, 25, 0.9); border: 1px solid var(--border);
  color: var(--text); font-size: 14px; font-weight: 500; margin-bottom: 12px; outline: none;
  transition: 0.2s;
}
.input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }

.btn {
  width: 100%; padding: 14px; border-radius: 14px; border: none;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #fff; font-weight: 800; font-size: 14px; cursor: pointer;
  box-shadow: 0 6px 20px var(--accent-glow); transition: 0.2s; text-align: center;
}
.btn:active { transform: scale(0.98); }
.btn-green { background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 6px 20px rgba(16,185,129,0.3); }
.btn-red { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); box-shadow: none; }
.btn-sm { padding: 9px 14px; font-size: 12px; width: auto; border-radius: 10px; font-weight: 700; }

.srv-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; border-radius: 16px; background: rgba(255,255,255,0.025);
  border: 1px solid var(--border); margin-bottom: 10px; cursor: pointer;
  transition: 0.2s;
}
.srv-item:hover, .srv-item:active { border-color: var(--accent); background: rgba(99,102,241,0.06); }
.srv-name { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.srv-meta { font-size: 11px; color: var(--muted); font-weight: 500; }
.srv-price { font-size: 14px; font-weight: 800; color: #818cf8; text-align: right; white-space: nowrap; margin-left: 12px; }

.bottom-nav {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: rgba(11, 15, 25, 0.95);
  border-top: 1px solid var(--border);
  display: flex; justify-content: space-around;
  padding: 10px 8px 20px; z-index: 100; backdrop-filter: blur(20px);
}
.nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  color: var(--muted); font-size: 10px; font-weight: 700; cursor: pointer;
  padding: 8px 12px; border-radius: 14px; transition: 0.2s;
}
.nav-item.active { color: #fff; background: rgba(99,102,241,0.2); }
.nav-icon { font-size: 20px; }

.badge { padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 800; }
.badge-ok { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.badge-wait { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }

.toast {
  position: fixed; top: 20px; left: 16px; right: 16px;
  background: #1e293b; border: 1px solid var(--accent); color: #fff;
  padding: 14px 18px; border-radius: 16px; z-index: 1000; font-size: 13px; font-weight: 700;
  display: none; box-shadow: 0 12px 35px rgba(0,0,0,0.6); animation: toastIn 0.3s ease;
}
@keyframes toastIn { from { opacity: 0; transform: translateY(-15px); } to { opacity: 1; transform: translateY(0); } }

.loading-screen {
  position: fixed; inset: 0; background: var(--bg); z-index: 9999;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px;
  transition: opacity 0.3s ease;
}
.spinner {
  width: 44px; height: 44px; border: 4px solid rgba(99,102,241,0.2);
  border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>

<div id="loading" class="loading-screen">
  <div class="brand-logo" style="width:60px; height:60px; font-size:28px;">🚀</div>
  <div style="font-weight:800; font-size:16px;">PRO SMM Market</div>
  <div class="spinner"></div>
</div>

<div id="toast" class="toast"></div>

<div class="header">
  <div class="brand">
    <div class="brand-logo">🚀</div>
    <div>
      <div class="brand-title">PRO SMM Market</div>
      <div class="brand-sub" id="user-greeting">Xush kelibsiz!</div>
    </div>
  </div>
  <div class="bal-pill" onclick="switchTab('profile')">
    <span class="bal-lbl">Balans</span>
    <span class="bal-val" id="top-balance">0 so'm</span>
  </div>
</div>

<div class="container">
  <!-- TAB 1: SMM XIZMATLAR -->
  <div id="tab-smm" class="tab-content active">
    <div class="card">
      <div class="sec-title">🛍 SMM Xizmatlar</div>
      <div class="pills" id="smm-cats">
        <div class="pill active" onclick="filterSmm('all', this)">Barchasi</div>
        <div class="pill" onclick="filterSmm('telegram', this)">✈️ Telegram</div>
        <div class="pill" onclick="filterSmm('instagram', this)">📸 Instagram</div>
        <div class="pill" onclick="filterSmm('youtube', this)">▶️ YouTube</div>
        <div class="pill" onclick="filterSmm('tiktok', this)">🎵 TikTok</div>
      </div>
      <input type="text" id="smm-search" class="input" placeholder="🔍 Xizmat nomini qidiring..." oninput="renderSmmList()" style="margin-bottom:0;">
    </div>

    <div id="smm-order-box" class="card" style="display:none; border-color: var(--accent); box-shadow: 0 10px 35px var(--accent-glow);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <b id="sel-srv-name" style="font-size:15px; color:#a5b4fc;"></b>
        <span onclick="closeSmmOrder()" style="cursor:pointer; font-size:18px; padding:4px 8px;">✕</span>
      </div>
      <div id="sel-srv-info" style="font-size:12px; color:var(--muted); margin-bottom:12px; font-weight:500;"></div>
      <input type="text" id="smm-link" class="input" placeholder="🔗 Havola (Link) kiriting...">
      <input type="number" id="smm-qty" class="input" placeholder="🔢 Miqdorni kiriting..." oninput="calcSmmTotal()">
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:14px; margin-bottom:16px; font-weight:700;">
        <span>Jami to'lov:</span>
        <b id="smm-total" style="color:#34d399; font-size:16px;">0 so'm</b>
      </div>
      <button class="btn" onclick="submitSmmOrder()">🚀 Buyurtma berish</button>
    </div>

    <div id="smm-list"></div>
  </div>

  <!-- TAB 2: VIRTUAL NOMER -->
  <div id="tab-numbers" class="tab-content">
    <div class="card">
      <div class="sec-title">📱 Virtual Nomer olish</div>
      <label style="font-size:12px; color:var(--muted); display:block; margin-bottom:6px; font-weight:700;">Tarmoqni tanlang:</label>
      <select id="num-service" onchange="loadNumberPrices()" style="margin-bottom:0;">
        <option value="tg">✈️ Telegram</option>
        <option value="go">🔍 Google / Gmail</option>
        <option value="yt">▶️ YouTube</option>
        <option value="ig">📸 Instagram</option>
        <option value="wa">💬 WhatsApp</option>
        <option value="fb">📘 Facebook</option>
        <option value="dt">🎵 TikTok</option>
        <option value="vk">🌐 VKontakte</option>
      </select>
    </div>

    <div id="active-sms-box" class="card" style="display:none; border-color:#10b981;">
      <div class="sec-title" style="color:#34d399;">📩 Faol Xarid</div>
      <div style="font-size:14px; margin-bottom:8px;">Nomer: <code id="act-phone" style="color:#34d399; font-weight:800; font-size:16px; background:rgba(0,0,0,0.3); padding:4px 8px; border-radius:8px;"></code></div>
      <div style="font-size:13px; margin-bottom:14px;">Holati: <b id="act-status" style="color:#fbbf24;">SMS kutilmoqda...</b></div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-green" onclick="checkSmsStatus()">🔄 SMS tekshirish</button>
        <button class="btn btn-red" onclick="cancelSmsNumber()">❌ Bekor qilish</button>
      </div>
    </div>

    <div id="countries-list"></div>
  </div>

  <!-- TAB 3: TAYYOR KANALLAR -->
  <div id="tab-channels" class="tab-content">
    <div class="sec-title">▶️ Tayyor YouTube Kanallar</div>
    <div id="channels-list"></div>
  </div>

  <!-- TAB 4: BUYURTMALAR -->
  <div id="tab-orders" class="tab-content">
    <div class="sec-title">📦 So'nggi buyurtmalarim</div>
    <div id="orders-list"></div>
  </div>

  <!-- TAB 5: HISOBIM & TO'LOV -->
  <div id="tab-profile" class="tab-content">
    <div class="card">
      <div class="sec-title">💼 Mening Kabinetim</div>
      <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px;">
        <span style="color:var(--muted); font-weight:600;">ID raqamingiz:</span>
        <b id="prof-id">-</b>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px;">
        <span style="color:var(--muted); font-weight:600;">Asosiy balans:</span>
        <b id="prof-bal" style="color:#34d399;">0 so'm</b>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px;">
        <span style="color:var(--muted); font-weight:600;">Jami kiritilgan:</span>
        <b id="prof-dep">0 so'm</b>
      </div>
      <div style="display:flex; justify-content:space-between; font-size:13px;">
        <span style="color:var(--muted); font-weight:600;">Taklif qilingan do'stlar (5%):</span>
        <b id="prof-ref">0 ta</b>
      </div>
    </div>

    <div class="card">
      <div class="sec-title">💳 Karta orqali hisob to'ldirish</div>
      <div style="background:rgba(99,102,241,0.12); border:1px dashed var(--accent); padding:14px; border-radius:14px; margin-bottom:14px; text-align:center;">
        <div style="font-size:11px; color:var(--muted); margin-bottom:4px; font-weight:700;">To'lov uchun Uzcard / Humo karta:</div>
        <div id="pay-card-num" style="font-size:16px; font-weight:800; letter-spacing:1px; color:#a5b4fc;"></div>
      </div>
      <input type="number" id="dep-amount" class="input" placeholder="💵 Summani kiriting (min: 1000 so'm)">
      <button class="btn btn-green" onclick="createDeposit()">✅ To'lov arizasi yaratish</button>
      <p style="font-size:11px; color:var(--muted); margin-top:10px; text-align:center; font-weight:500;">Ariza yaratilgach, to'lov chekini botga yuborasiz.</p>
    </div>

    <div class="card">
      <div class="sec-title">🎁 Promo-kod faollashtirish</div>
      <div style="display:flex; gap:10px;">
        <input type="text" id="promo-input" class="input" placeholder="Kodni yozing..." style="margin-bottom:0;">
        <button class="btn btn-sm btn-green" onclick="applyPromo()">Faollashtirish</button>
      </div>
    </div>

    <div class="card">
      <div class="sec-title">🔗 Referal havolangiz</div>
      <input type="text" id="ref-link-box" class="input" readonly onclick="this.select()" style="margin-bottom:8px;">
      <div style="font-size:12px; color:var(--muted); font-weight:600;">👨‍💻 Admin bilan aloqa: <b id="admin-user" style="color:#fff;"></b></div>
    </div>
  </div>
</div>

<div class="bottom-nav">
  <div class="nav-item active" onclick="switchTab('smm', this)"><span class="nav-icon">🛍</span><span>Xizmatlar</span></div>
  <div class="nav-item" onclick="switchTab('numbers', this)"><span class="nav-icon">📱</span><span>Nomerlar</span></div>
  <div class="nav-item" onclick="switchTab('channels', this)"><span class="nav-icon">▶️</span><span>Kanallar</span></div>
  <div class="nav-item" onclick="switchTab('orders', this)"><span class="nav-icon">📦</span><span>Buyurtma</span></div>
  <div class="nav-item" onclick="switchTab('profile', this)"><span class="nav-icon">👤</span><span>Kabinet</span></div>
</div>

<script>
const tg = window.Telegram.WebApp;
try { tg.expand(); } catch(e) {}

const urlParams = new URLSearchParams(window.location.search);
let USER_ID = urlParams.get('uid') || (tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 8467707826);
let USER_NAME = (tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.first_name : "Foydalanuvchi");

let APP_DATA = { services: [], channels: [], orders: [], balance: 0 };
let SEL_CAT = 'all';
let SEL_SRV = null;
let ACT_GZ = null;

function showToast(msg) {
  const t = document.getElementById('toast');
  t.innerText = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3200);
}

function switchTab(tab, el) {
  document.querySelectorAll('.tab-content').forEach(x => x.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
  if (el) el.classList.add('active');
  if (tab === 'numbers') loadNumberPrices();
  if (tab === 'orders') loadInitData();
}

async function loadInitData() {
  const loader = document.getElementById('loading');
  if (loader) {
    loader.style.opacity = '0';
    setTimeout(() => { loader.style.display = 'none'; }, 250);
  }
  try {
    const res = await fetch('/api/init?uid=' + USER_ID);
    const d = await res.json();
    APP_DATA = d;

    document.getElementById('user-greeting').innerText = "Salom, " + USER_NAME + "!";
    document.getElementById('top-balance').innerText = (d.balance || 0).toLocaleString() + " so'm";
    document.getElementById('prof-id').innerText = USER_ID || "Noma'lum";
    document.getElementById('prof-bal').innerText = (d.balance || 0).toLocaleString() + " so'm";
    document.getElementById('prof-dep').innerText = (d.total_dep || 0).toLocaleString() + " so'm";
    document.getElementById('prof-ref').innerText = (d.ref_count || 0) + " ta";
    document.getElementById('pay-card-num').innerText = d.card || '-';
    document.getElementById('admin-user').innerText = d.admin || '-';
    document.getElementById('ref-link-box').value = "https://t.me/" + (d.bot_user || 'bot') + "?start=" + USER_ID;
    
    renderSmmList();
    renderChannels();
    renderOrders();
  } catch (e) {
    console.error(e);
    document.getElementById('loading').style.display = 'none';
    showToast("⚠️ Ma'lumotlarni yuklashda xatolik!");
  }
}

function filterSmm(cat, el) {
  SEL_CAT = cat;
  document.querySelectorAll('#smm-cats .pill').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
  renderSmmList();
}

function renderSmmList() {
  const q = (document.getElementById('smm-search').value || '').toLowerCase();
  const box = document.getElementById('smm-list');
  box.innerHTML = '';
  if (!APP_DATA.services || APP_DATA.services.length === 0) {
    box.innerHTML = '<div class="card" style="text-align:center; color:var(--muted);">Xizmatlar topilmadi</div>';
    return;
  }
  APP_DATA.services.forEach(s => {
    if (SEL_CAT !== 'all' && !s.category.includes(SEL_CAT)) return;
    if (q && !s.name.toLowerCase().includes(q)) return;
    const unit = s.pkg ? "1 paket" : "1000 ta";
    const div = document.createElement('div');
    div.className = 'srv-item';
    div.onclick = () => openSmmOrder(s);
    div.innerHTML = `
      <div>
        <div class="srv-name">${s.name}</div>
        <div class="srv-meta">Min: ${s.min} | Max: ${s.max}</div>
      </div>
      <div class="srv-price">${s.price_uzs.toLocaleString()} so'm<br><span style="font-size:10px; color:var(--muted); font-weight:500;">${unit}</span></div>
    `;
    box.appendChild(div);
  });
}

function openSmmOrder(s) {
  SEL_SRV = s;
  document.getElementById('smm-order-box').style.display = 'block';
  document.getElementById('sel-srv-name').innerText = s.name;
  document.getElementById('sel-srv-info').innerText = `Narxi: ${s.price_uzs.toLocaleString()} so'm (${s.pkg ? '1 paket' : '1000 ta'}) | Limit: ${s.min} - ${s.max}`;
  document.getElementById('smm-qty').value = s.min;
  calcSmmTotal();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function closeSmmOrder() {
  document.getElementById('smm-order-box').style.display = 'none';
  SEL_SRV = null;
}

function calcSmmTotal() {
  if (!SEL_SRV) return;
  const q = parseInt(document.getElementById('smm-qty').value || '0');
  const tot = SEL_SRV.pkg ? (SEL_SRV.price_uzs * q) : Math.floor((SEL_SRV.price_uzs / 1000) * q);
  document.getElementById('smm-total').innerText = (tot > 0 ? tot.toLocaleString() : 0) + " so'm";
}

async function submitSmmOrder() {
  if (!SEL_SRV) return;
  const link = document.getElementById('smm-link').value.trim();
  const qty = parseInt(document.getElementById('smm-qty').value || '0');
  if (!link) return showToast("❗ Havolani (Link) kiriting!");
  
  showToast("⏳ Buyurtma yuborilmoqda...");
  try {
    const res = await fetch('/api/order_smm', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, service: SEL_SRV.service, link: link, qty: qty })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) {
      closeSmmOrder();
      document.getElementById('smm-link').value = '';
      loadInitData();
    }
  } catch(e) {
    showToast("❌ Xatolik yuz berdi!");
  }
}

async function loadNumberPrices() {
  const sc = document.getElementById('num-service').value;
  const box = document.getElementById('countries-list');
  box.innerHTML = '<div class="card" style="text-align:center; color:var(--muted);">⏳ Nomerlar yuklanmoqda...</div>';
  try {
    const res = await fetch('/api/numbers?sc=' + sc);
    const d = await res.json();
    box.innerHTML = '';
    if (!d.countries || d.countries.length === 0) {
      box.innerHTML = `<div class="card" style="text-align:center; color:var(--muted);">Hozircha nomerlar yo'q</div>`;
      return;
    }
    d.countries.forEach(c => {
      const div = document.createElement('div');
      div.className = 'srv-item';
      if (c.available) {
        div.onclick = () => buyVirtualNumber(sc, c.cid, c.price_uzs);
        div.innerHTML = `<div class="srv-name">${c.name}</div><div class="srv-price">${c.price_uzs.toLocaleString()} so'm</div>`;
      } else {
        div.style.opacity = '0.45';
        div.innerHTML = `<div class="srv-name">${c.name}</div><div class="srv-meta">Qolmagan</div>`;
      }
      box.appendChild(div);
    });
  } catch(e) {
    box.innerHTML = `<div class="card" style="text-align:center; color:var(--red);">Nomerlarni yuklab bo'lmadi</div>`;
  }
}

async function buyVirtualNumber(sc, cid, price) {
  showToast("⏳ Nomer olinmoqda...");
  try {
    const res = await fetch('/api/buy_number', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, sc: sc, cid: cid, price: price })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) {
      ACT_GZ = { id: d.gz_id, price: price };
      document.getElementById('active-sms-box').style.display = 'block';
      document.getElementById('act-phone').innerText = d.phone;
      document.getElementById('act-status').innerText = "SMS kutilmoqda...";
      loadInitData();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  } catch(e) {
    showToast("❌ Xatolik yuz berdi!");
  }
}

async function checkSmsStatus() {
  if (!ACT_GZ) return;
  showToast("⏳ Tekshirilmoqda...");
  try {
    const res = await fetch('/api/check_sms', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, gz_id: ACT_GZ.id, action: 'check', price: ACT_GZ.price })
    });
    const d = await res.json();
    document.getElementById('act-status').innerText = d.status_text;
    showToast(d.msg);
  } catch(e) {
    showToast("❌ Xatolik!");
  }
}

async function cancelSmsNumber() {
  if (!ACT_GZ) return;
  showToast("⏳ Bekor qilinmoqda...");
  try {
    const res = await fetch('/api/check_sms', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, gz_id: ACT_GZ.id, action: 'cancel', price: ACT_GZ.price })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) {
      document.getElementById('active-sms-box').style.display = 'none';
      ACT_GZ = null;
      loadInitData();
    }
  } catch(e) {
    showToast("❌ Xatolik!");
  }
}

function renderChannels() {
  const box = document.getElementById('channels-list');
  box.innerHTML = '';
  if (!APP_DATA.channels || APP_DATA.channels.length === 0) {
    box.innerHTML = '<div class="card" style="text-align:center; color:var(--muted);">Kanallar topilmadi</div>';
    return;
  }
  APP_DATA.channels.forEach(ch => {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <div>
          <div style="font-weight:800; font-size:14px; margin-bottom:2px;">${ch.title}</div>
          <div style="font-size:12px; color:var(--muted); font-weight:600;">Bazada mavjud: ${ch.count} ta</div>
        </div>
        <div style="font-weight:800; color:#34d399; font-size:15px;">${ch.price.toLocaleString()} so'm</div>
      </div>
      <button class="btn" onclick="buyYtChannel('${ch.key}')">🛒 Xarid qilish</button>
    `;
    box.appendChild(div);
  });
}

async function buyYtChannel(key) {
  showToast("⏳ Xarid qilinmoqda...");
  try {
    const res = await fetch('/api/buy_channel', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, key: key })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) loadInitData();
  } catch(e) {
    showToast("❌ Xatolik!");
  }
}

function renderOrders() {
  const box = document.getElementById('orders-list');
  if (!APP_DATA.orders || APP_DATA.orders.length === 0) {
    box.innerHTML = `<div class="card" style="text-align:center; color:var(--muted);">📭 Hali buyurtmalaringiz yo'q</div>`;
    return;
  }
  box.innerHTML = '';
  APP_DATA.orders.forEach(o => {
    const isOk = o.status.includes('Bajarildi') || o.status.includes('Yuborildi');
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
        <b style="font-size:13px;">ID: #${o.oid}</b>
        <span class="badge ${isOk ? 'badge-ok' : 'badge-wait'}">${o.status}</span>
      </div>
      <div style="font-size:12px; color:var(--muted); margin-bottom:4px; font-weight:600;">Miqdor: ${o.quantity} | Sana: ${o.date}</div>
      <div style="font-size:12px; color:#93c5fd; word-break:break-all; font-weight:500;">${o.link}</div>
    `;
    box.appendChild(div);
  });
}

async function createDeposit() {
  const amt = parseInt(document.getElementById('dep-amount').value || '0');
  if (amt < 1000) return showToast("❗ Minimal to'lov: 1,000 so'm");
  
  showToast("⏳ Ariza yaratilmoqda...");
  try {
    const res = await fetch('/api/deposit', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, amount: amt })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) {
      document.getElementById('dep-amount').value = '';
      if (tg.close) {
        setTimeout(() => tg.close(), 1800);
      }
    }
  } catch(e) {
    showToast("❌ Xatolik!");
  }
}

async function applyPromo() {
  const code = document.getElementById('promo-input').value.trim();
  if (!code) return showToast("❗ Promo-kodni yozing!");
  
  showToast("⏳ Tekshirilmoqda...");
  try {
    const res = await fetch('/api/promo', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: USER_ID, code: code })
    });
    const d = await res.json();
    showToast(d.msg);
    if (d.ok) {
      document.getElementById('promo-input').value = '';
      loadInitData();
    }
  } catch(e) {
    showToast("❌ Xatolik!");
  }
}

loadInitData();
</script>
</body>
</html>
"""



@app.route('/')
def home():
    return "🤖 PRO SMM Market Bot & Mini App 24/7 ishlamoqda! Mini App manzili: /app"

@app.route('/app')
def web_app_page():
    return render_template_string(MINI_APP_HTML)

@app.route('/api/init')
def api_init():
    try:
        uid = int(request.args.get('uid', 0))
    except:
        uid = 0
    user = users_db.find_one({"_id": uid}) if uid else None
    bal = int(user.get('balance', 0)) if user else 0
    total_dep = int(user.get('total_deposited', 0)) if user else 0
    has_sk = bool(user.get('skidka')) if user else False
    ref_cnt = users_db.count_documents({"r": uid}) if uid else 0

    gk_usd = g_k("USD", 12700)
    srv_list = []
    for s in g_smm():
        cat = s.get('category', '')
        mv = get_m('m_yt_sub') if 'youtube sub' in cat else (get_m('m_yt_watch') if 'youtube watch' in cat else get_m('m_smm'))
        try:
            rate_f = float(str(s.get('rate', '0')).replace(',', '.'))
        except:
            rate_f = 0.0
        pr_uzs = int(rate_f * gk_usd * mv)
        min_q = int(s.get('min', 10))
        max_q = int(s.get('max', 10000))
        srv_list.append({
            "service": str(s['service']),
            "name": s['name'],
            "category": cat,
            "min": min_q,
            "max": max_q,
            "price_uzs": pr_uzs,
            "pkg": (min_q == 1 and max_q == 1)
        })

    try: p_y1 = int(g_set('p_y1'))
    except: p_y1 = 190000
    try: p_y2 = int(g_set('p_y2'))
    except: p_y2 = 120000
    try: p_2f = int(g_set('p_2func'))
    except: p_2f = 100000

    channels_data = [
        {"key": "y1", "title": "🔴 [ESKI] 2006-2009 YouTube Kanal", "price": p_y1 - (15000 if has_sk else 0), "count": g_c('y1')},
        {"key": "y2", "title": "🟠 [ESKI] 2010-2019 YouTube Kanal", "price": p_y2 - (15000 if has_sk else 0), "count": g_c('y2')},
        {"key": "2func", "title": "🛠 2 funksiya yoqish xizmati", "price": p_2f, "count": "Buyurtma"}
    ]

    ords = []
    if uid:
        for x in orders_db.find({"user_id": uid}).sort("_id", -1).limit(15):
            ords.append({
                "oid": str(x.get('oid', 'N/A')),
                "status": str(x.get('status', 'N/A')),
                "quantity": int(x.get('quantity', 1)),
                "link": str(x.get('link', ''))[:60],
                "date": str(x.get('date', ''))
            })

    try:
        b_usr = bot.get_me().username
    except:
        b_usr = "bot"

    return jsonify({
        "balance": bal,
        "total_dep": total_dep,
        "ref_count": ref_cnt,
        "card": g_set('card'),
        "admin": g_set('admin'),
        "bot_user": b_usr,
        "services": srv_list,
        "channels": channels_data,
        "orders": ords
    })

@app.route('/api/order_smm', methods=['POST'])
def api_order_smm():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    sid = str(data.get('service', ''))
    link = str(data.get('link', '')).strip()
    qty = int(data.get('qty', 0))

    if not uid or not link or qty <= 0:
        return jsonify({"ok": False, "msg": "❗ Ma'lumotlar to'liq emas!"})

    srv = next((x for x in g_smm() if str(x.get('service')) == sid), None)
    if not srv:
        return jsonify({"ok": False, "msg": "❌ Xizmat topilmadi!"})

    min_q = int(srv.get('min', 10))
    max_q = int(srv.get('max', 10000))
    if qty < min_q or qty > max_q:
        return jsonify({"ok": False, "msg": f"⚠️ Miqdor {min_q} va {max_q} orasida bo'lishi kerak!"})

    cat = srv.get('category', '')
    mv = get_m('m_yt_sub') if 'youtube sub' in cat else (get_m('m_yt_watch') if 'youtube watch' in cat else get_m('m_smm'))
    pr_1000 = int(float(str(srv.get('rate', '0')).replace(',', '.')) * g_k("USD", 12700) * mv)
    is_pkg = (min_q == 1 and max_q == 1)
    total_cost = int(pr_1000 * qty) if is_pkg else int((pr_1000 / 1000.0) * qty)

    if g_bal(uid) < total_cost:
        return jsonify({"ok": False, "msg": f"🔴 Balansingiz yetarli emas! Kerak: {total_cost:,} so'm"})

    u_bal(uid, -total_cost)
    try:
        r = requests.get(SMM_API_URL, params={'key': SMM_API_KEY, 'act': 'new_order', 'service_id': sid, 'link': link, 'count': qty}, timeout=20).json()
        if 'res' in r and isinstance(r['res'], dict) and r['res'].get('status') == 'ok':
            oid = str(r['res'].get('order_id', 'N/A'))
            orders_db.insert_one({"user_id": uid, "oid": oid, "link": link, "quantity": qty, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Yuborildi"})
            try:
                bot.send_message(uid, f"✅ <b>Mini App orqali buyurtma qabul qilindi!</b>\n🆔 ID: <code>{oid}</code>\n💵 Yechildi: {total_cost:,} so'm", parse_mode='HTML')
            except:
                pass
            return jsonify({"ok": True, "msg": f"✅ Buyurtma qabul qilindi! ID: #{oid}"})
        else:
            u_bal(uid, total_cost)
            return jsonify({"ok": False, "msg": "❌ Provayder xatosi, pul balansingizga qaytarildi."})
    except:
        u_bal(uid, total_cost)
        return jsonify({"ok": False, "msg": "⚠️ Tizim xatosi, pul balansingizga qaytarildi."})

@app.route('/api/numbers')
def api_numbers():
    sc = request.args.get('sc', 'tg')
    pr = get_gz_pr(sc=sc)
    gk = g_k("RUB", 140.0)
    res_list = []
    for cid, cname in C_LIST:
        cost = pr.get(cid)
        if cost:
            cmv = get_country_m(cid)
            price_uzs = int(cost * gk * cmv)
            res_list.append({"cid": cid, "name": cname, "available": True, "price_uzs": price_uzs})
        else:
            res_list.append({"cid": cid, "name": cname, "available": False, "price_uzs": 0})
    return jsonify({"countries": res_list})

@app.route('/api/buy_number', methods=['POST'])
def api_buy_number():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    sc = str(data.get('sc', 'tg'))
    cid = str(data.get('cid', '0'))
    price = int(data.get('price', 0))

    if not uid or price <= 0:
        return jsonify({"ok": False, "msg": "❗ Foydalanuvchi aniqlanmadi!"})
    if g_bal(uid) < price:
        return jsonify({"ok": False, "msg": "🔴 Balansingiz yetarli emas!"})

    r = req_gz(sc, cid)
    if r["s"]:
        u_bal(uid, -price)
        orders_db.insert_one({
            "user_id": uid,
            "oid": f"GZ_{r['id']}",
            "gz_id": str(r['id']),
            "price": price,
            "link": r['n'],
            "quantity": 1,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            "status": "SMS kutilmoqda"
        })
        mk = IK().add(
            IB("🔎 SMS olish", callback_data=f"ck_{r['id']}_{price}"),
            IB("❌ Bekor qilish", callback_data=f"cl_{r['id']}_{price}")
        )
        try:
            bot.send_message(uid, f"✅ <b>Mini App orqali nomer olindi!</b>\n📱 Nomer: <code>{r['n']}</code>\n💵 Yechildi: {price:,} so'm", reply_markup=mk, parse_mode='HTML')
        except:
            pass
        return jsonify({"ok": True, "msg": "✅ Nomer olindi!", "phone": r['n'], "gz_id": str(r['id'])})
    return jsonify({"ok": False, "msg": f"❌ {r['m']}"})

@app.route('/api/check_sms', methods=['POST'])
def api_check_sms():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    gz_id = str(data.get('gz_id', ''))
    action = str(data.get('action', 'check'))
    price = int(data.get('price', 0))

    if action == 'check':
        code, body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "getStatus", "id": gz_id}, timeout=15)
        if body.startswith("STATUS_OK") or body.startswith("OK:"):
            sms_code = body.split(':')[1] if ':' in body else body.replace('OK:', '')
            orders_db.update_one({"gz_id": gz_id}, {"$set": {"status": "Bajarildi ✅"}})
            return jsonify({"ok": True, "status_text": f"✅ KOD: {sms_code}", "msg": f"✅ SMS kod keldi: {sms_code}"})
        return jsonify({"ok": False, "status_text": "⏳ SMS kutilmoqda...", "msg": "⏳ Hali SMS kelmadi, biroz kuting."})
    else:
        ord_doc = orders_db.find_one({"gz_id": gz_id})
        if ord_doc and ord_doc.get("status") in ["Bekor qilindi ❌", "Bajarildi ✅"]:
            return jsonify({"ok": False, "msg": "Bu nomer allaqachon yakunlangan!"})
        code, cancel_body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "setStatus", "status": 8, "id": gz_id}, timeout=15)
        if "ACCESS_CANCEL" in cancel_body:
            res_upd = orders_db.find_one_and_update({"gz_id": gz_id, "status": "SMS kutilmoqda"}, {"$set": {"status": "Bekor qilindi ❌"}})
            if res_upd or not ord_doc:
                u_bal(uid, price)
            return jsonify({"ok": True, "msg": f"✅ Nomer bekor qilindi va {price:,} so'm qaytarildi!"})
        elif "EARLY_CANCEL_DENIED" in cancel_body:
            return jsonify({"ok": False, "msg": "⏳ Kamida 2 daqiqa o'tgach bekor qilish mumkin!"})
        return jsonify({"ok": False, "msg": "⏳ Hozircha bekor qilib bo'lmadi."})

@app.route('/api/buy_channel', methods=['POST'])
def api_buy_channel():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    key = str(data.get('key', ''))
    if not uid or key not in ['y1', 'y2', '2func']:
        return jsonify({"ok": False, "msg": "❗ Xato so'rov!"})

    user = users_db.find_one({"_id": uid})
    has_sk = bool(user.get("skidka")) if user else False
    pr = int(g_set('p_' + key))
    if key in ['y1', 'y2'] and has_sk:
        pr -= 15000

    if g_bal(uid) < pr:
        return jsonify({"ok": False, "msg": "🔴 Balansingiz yetarli emas!"})

    u_bal(uid, -pr)
    if key in ['y1', 'y2']:
        acc = accounts_db.find_one_and_delete({"type": key})
        if acc:
            orders_db.insert_one({"user_id": uid, "oid": "YT_AUTO", "link": key, "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Bajarildi ✅"})
            try:
                bot.send_message(uid, f"✅ <b>KANAL XARID QILINDI:</b>\n<code>{acc['data']}</code>", parse_mode='HTML')
            except:
                pass
            return jsonify({"ok": True, "msg": "✅ Kanal ma'lumotlari bot orqali yuborildi!"})
        else:
            orders_db.insert_one({"user_id": uid, "oid": "YT", "link": key, "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Kutmoqda"})
            adm_msg(f"🔔 <b>YANGI KANAL BUYURTMASI (Mini App):</b>\n👤 Mijoz ID: <code>{uid}</code>\n📦 Turi: {key}", rm=IK().add(IB("📤 Yuborish", callback_data=f"snd_{uid}")))
            return jsonify({"ok": True, "msg": "✅ Buyurtma qabul qilindi! Admin bot orqali yuboradi."})
    else:
        usr_st[uid] = "wn_2func"
        try:
            bot.send_message(uid, "🛠 <b>2 funksiya xizmati uchun kanal yo'nalishi yoki havolasini botga yozib yuboring:</b>", parse_mode='HTML')
        except:
            pass
        return jsonify({"ok": True, "msg": "✅ Botga kirib kanal ma'lumotini yuboring!"})

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    amount = int(data.get('amount', 0))
    if not uid or amount < 1000:
        return jsonify({"ok": False, "msg": "❗ Minimal summa: 1,000 so'm"})

    r = payments_db.insert_one({"user_id": uid, "amount": amount, "status": "awaiting_receipt", "created_at": datetime.now()})
    usr_st[uid] = f"receipt_{str(r.inserted_id)}"
    txt = (f"💳 <b>Mini App orqali to'lov arizasi yaratildi!</b>\n\n"
           f"➡️ <b>To'lov karta:</b> <code>{g_set('card')}</code>\n"
           f"💵 <b>Miqdori:</b> {amount:,} so'm\n\n"
           f"📸 <b>To'lov qilib bo'lgach, to'lov chekini (skrinshotni) shu yerga yuboring!</b>")
    mk = IK(row_width=1).add(IB("❌ To'lovni bekor qilish", callback_data="cancel_pay"))
    try:
        bot.send_message(uid, txt, parse_mode='HTML', reply_markup=mk)
    except:
        pass
    return jsonify({"ok": True, "msg": "✅ Ariza yaratildi! Chekni botga yuboring."})

@app.route('/api/promo', methods=['POST'])
def api_promo():
    data = request.json or {}
    uid = int(data.get('uid', 0))
    code_str = str(data.get('code', '')).strip()
    if not uid or not code_str:
        return jsonify({"ok": False, "msg": "❗ Promo-kodni kiriting!"})

    promo = promos_db.find_one({"_id": code_str})
    if not promo or int(promo.get("left", 0)) <= 0:
        return jsonify({"ok": False, "msg": "❌ Bunday promo-kod yo'q yoki tugagan!"})
    if uid in promo.get("used_by", []):
        return jsonify({"ok": False, "msg": "⚠️ Siz bu promo-koddan foydalangansiz!"})

    amt = int(promo.get("amount", 0))
    promos_db.update_one({"_id": code_str}, {"$inc": {"left": -1}, "$push": {"used_by": uid}})
    u_bal(uid, amt)
    return jsonify({"ok": True, "msg": f"🎁 Tabriklaymiz! +{amt:,} so'm qo'shildi!"})

def run_server():
    port = int(os.environ.get("PORT", 8080) if os.environ.get("PORT") else 8080)
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server, daemon=True).start()

print("✅ Barcha tizimlar ulandi. Bot ishga tushdi...")
try:
    bot.remove_webhook()
except:
    pass
time.sleep(1)

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"🔴 XATOLIK: {e}", flush=True)
        time.sleep(5)
