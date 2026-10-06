import telebot
import requests
import time
import os
import threading
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup as RK, KeyboardButton as KB, InlineKeyboardMarkup as IK, InlineKeyboardButton as IB
from flask import Flask
from pymongo import MongoClient
import dns.resolver

# DNS sozlamalari (MongoDB klasteriga ulanish uchun)
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

TOKEN = '8904483870:AAH4Y-d4OfFtLWgmiDla2y8piRLgjsH0ydk'
ADMIN_ID = 8467707826
GRIZZLY_API_KEY = '3335af0d250efb73bdc40ebf82fa42dd'
SMM_API_KEY = '17d89a016b9005b0e52bce6f67ad8e35'
SMM_API_URL = 'https://top4smm.com/api.php'
MONGO_URL = "mongodb+srv://nurekeshureke090_db_user:qKFmlTnxjnAe27Gi@cluster0.1dcdbiw.mongodb.net/?appName=Cluster0"

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
    'bot_desc': 'Tezkor, Arzon va Sifatli SMM Xizmatlar'
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
    ch = g_set('m_chan')
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
def m_menu(uid):
    m = RK(resize_keyboard=True, row_width=2)
    m.add(
        KB("Xizmatlar", icon_custom_emoji_id="5294167145079395967"),
        KB("Nomer olish", icon_custom_emoji_id="5461046042076136604"),
        KB("Tayyor Kanallar", icon_custom_emoji_id="5456299961480132196"), # Tayyor kanallar tugmasi qo'shildi
        KB("Buyurtmalarim", icon_custom_emoji_id="5312361253610475399"),
        KB("Pul ishlash", icon_custom_emoji_id="5278467510604160626"),
        KB("Mening hisobim", icon_custom_emoji_id="5287231198098117669"),
        KB("Hisob to'ldirish", icon_custom_emoji_id="5445353829304387411"),
        KB("Murojaat", icon_custom_emoji_id="5460618847449005320"),
        KB("Qo'llab-quvvatlash", icon_custom_emoji_id="5454237135932506706")
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
{ce_f('telegram', '✈️️')} Telegram - Obunachi, View, Like
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

@bot.message_handler(func=lambda m: "Bosh sahifa" in m.text)
def bs(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, f"🏠 <b>Asosiy menyuga qaytdingiz.</b>", reply_markup=m_menu(m.from_user.id), parse_mode='HTML')
# Profil (Mening hisobim)
@bot.message_handler(func=lambda m: "Mening hisobim" in m.text)
def mc(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    user = users_db.find_one({"_id": m.from_user.id})
    balans = g_bal(m.from_user.id)
    total_dep = int(user.get('total_deposited', 0)) if user else 0
    ref_count = users_db.count_documents({"r": m.from_user.id})
    
    txt = f"""
{ce_f('briefcase', '💼')} <b>Kabinetingizga xush kelibsiz.</b>
<blockquote>
📋 <b>Ma'lumotlaringiz:</b>
├─ {ce_f('user', '👤')} ID raqamingiz: <code>{m.from_user.id}</code>
├─ {ce_f('money', '💵')} Hisobingiz: <b>{balans:,} so'm</b>
└─ {ce_f('wallet', '💰')} Kiritgan pullaringiz: <b>{total_dep:,} so'm</b>
</blockquote>
{ce_f('gift', '🎁')} <b>Referal tizimi (5% bonus):</b>
{ce_f('link', '🔗')} <code>https://t.me/{bot.get_me().username}?start={m.from_user.id}</code>
{ce_f('users', '👥')} Taklif qilinganlar: <b>{ref_count} ta</b>
"""
    mk = IK(row_width=2).add(
        IB(f"{E_CARD} Pul kiritish", callback_data="deposit_menu"),
        IB(f"{E_PERCENT} Chegirma olish", callback_data="discount_info"),
        IB(f"{E_SETTINGS} Sozlamalar", callback_data="user_settings"),
        IB(f"{E_BONUS} Promo-Bonus", callback_data="promo_bonus")
    )
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML', disable_web_page_preview=True)

# Profil Inline tugmalari
@bot.callback_query_handler(func=lambda c: c.data in ["deposit_menu", "back_profile", "discount_info", "promo_bonus", "none"])
def inline_menus(c):
    bot.answer_callback_query(c.id)
    if c.data == "none":
        return
    if c.data == "back_profile":
        return mc(c.message)
    if c.data == "deposit_menu":
        txt = f"""
{ce_f('card', '💳')} <b>Hisobni to'ldirish usullari:</b>

🇺🇿 <b>O'zbekiston kartalari:</b>
• Uzcard / Humo orqali
• Payme (Avtomatik)
• Click (Avtomatik)
• Paynet

🌍 <b>Xalqaro to'lovlar:</b>
• Visa / Mastercard
• PayPal
• Crypto (USDT, BTC)

━━━━━━━━━━━━━━━━━━━━
ℹ <i>Minimal to'lov: 1,000 so'm</i>
"""
        mk = IK(row_width=1).add(
            IB(f"{E_PAYME} Payme (Auto)", callback_data="payme_auto"),
            IB(f"{E_CLICK} Click (Auto)", callback_data="click_auto"),
            IB(f"{E_PAYNET} Paynet", callback_data="paynet"),
            IB(f"{E_CARD} Karta orqali", callback_data="card_manual"),
            IB("🔙 Orqaga", callback_data="back_profile")
        )
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    elif c.data == "discount_info":
        txt = f"""
{ce_f('percent', '💯')} <b>Chegirma olish yo'llari:</b>

{ce_f('gift', '🎁')} <b>Referal bonus 5%</b>
Do'stingizni taklif qiling va uning har bir to'lovidan <b>5%</b> bonus oling!

🔗 <b>Referal link:</b>
<code>https://t.me/{bot.get_me().username}?start={c.from_user.id}</code>
"""
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="back_profile")), parse_mode='HTML')
    elif c.data == "promo_bonus":
        usr_st[c.from_user.id] = "enter_promo"
        txt = f"""
{ce_f('target', '🎯')} <b>Promo-kod kiriting:</b>

Maxsus promo-kodlarni kanalimizdan oling!
Har bir promo-kod <b>bonus balans</b> beradi!

📢 <b>Kanal:</b> @{g_set('m_chan').replace('@','')}
"""
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=IK().add(IB("🔙 Orqaga", callback_data="back_profile")), parse_mode='HTML')

# Yordamchi Bo'limlar
@bot.message_handler(func=lambda m: any(x in m.text for x in ["Pul ishlash", "Murojaat", "Qo'llab-quvvatlash", "Hamkorlik", "Buyurtmalarim"]))
def info_menus(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    if "Pul ishlash" in m.text:
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
        bot.send_message(m.chat.id, txt, reply_markup=IK(row_width=1).add(IB("🔙 Orqaga", callback_data="none")), parse_mode='HTML')
        
    elif "Murojaat" in m.text and "o'zgartirish" not in m.text:
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
            IB("🔙 Orqaga", callback_data="none")
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
            IB("🔙 Orqaga", callback_data="none")
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
@bot.message_handler(func=lambda m: "Admin Panel" in m.text and is_adm(m.from_user.id))
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
• Mijoz tekshirish: <code>/info ID</code>
• Foydalanuvchilar: <code>/users</code>

📌 <b>Bo'limni tanlang:</b>
"""
    bot.send_message(m.chat.id, txt, reply_markup=a_menu(), parse_mode='HTML')

@bot.message_handler(commands=['info', 'users', 'addbalance'])
def ad_cmds(m):
    if not is_adm(m.from_user.id):
        return
        
    if m.text.startswith('/info') and len(m.text.split()) > 1:
        uid = int(m.text.split()[1])
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
            bot.send_message(m.chat.id, f"{ce_f('cross', '❌')} Bunday foydalanuvchi bazada yo'q.")
            
    elif m.text.startswith('/users'):
        count = users_db.count_documents({})
        bot.send_message(m.chat.id, f"👥 <b>Jami foydalanuvchilar:</b> {count:,} ta", parse_mode='HTML')
        
    elif m.text.startswith('/addbalance') and len(m.text.split()) > 2:
        parts = m.text.split()
        uid = int(parts[1])
        amount = int(parts[2])
        
        u_bal(uid, amount)
        users_db.update_one({"_id": uid}, {"$inc": {"total_deposited": amount}}, upsert=True)
        bot.send_message(uid, f"{ce_f('gift', '🎁')} Balansingizga <b>{amount:,} so'm</b> qo'shildi!", parse_mode='HTML')
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Bajarildi! {uid} raqamiga {amount:,} so'm qo'shildi.")

@bot.message_handler(func=lambda m: is_adm(m.from_user.id) and any(x in m.text for x in ["Statistika", "Top Xaridorlar", "Skidka"]))
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

@bot.message_handler(func=lambda m: is_adm(m.from_user.id) and any(x in m.text for x in ["Kanal ulash", "Xabarnoma", "Narxlarni o'zgartirish", "Foizlarni o'zgartirish", "Admin qo'shish", "Karta o'zgartirish", "Murojaat o'zgartirish", "Qo'llanma o'zgartirish", "➕ 2006", "➕ 2010"]))
def adm_bts(m):
    if "Kanal ulash" in m.text:
        usr_st[m.from_user.id] = "set_chan"
        bot.send_message(m.chat.id, f"Majburiy obuna kanalini <b>@bilan</b> yuboring", parse_mode='HTML')
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
            IB(f"📱 Nomerlar: {g_set('m_nomer')}%", callback_data="edp_m_nomer"),
            IB(f"📺 YT Obunachi: {g_set('m_yt_sub')}%", callback_data="edp_m_yt_sub"),
            IB(f"🛍 Boshqa: {g_set('m_smm')}%", callback_data="edp_m_smm")
        )
        bot.send_message(m.chat.id, "⚙️ <b>Qaysi xizmat ustama foizini o'zgartirasiz?</b>", reply_markup=mk, parse_mode='HTML')
    elif "Admin qo'shish" in m.text:
        usr_st[m.from_user.id] = "add_adm"
        bot.send_message(m.chat.id, f"<b>Yangi admin ID raqami:</b>", parse_mode='HTML')
    elif "Karta o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_c"
        bot.send_message(m.chat.id, f"<b>Yangi karta:</b>\n<i>Hozirgi: {g_set('card')}</i>", parse_mode='HTML')
    elif "Murojaat o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_a"
        bot.send_message(m.chat.id, f"<b>Yangi admin (@bilan):</b>\n<i>Hozirgi: {g_set('admin')}</i>", parse_mode='HTML')
    elif "Qo'llanma o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_guide"
        bot.send_message(m.chat.id, f"<b>Yangi video qo'llanmani yuboring.</b>\nPastiga matn yozishni unutmang.", parse_mode='HTML')
    elif "➕ 2006" in m.text or "➕ 2010" in m.text:
        usr_st[m.from_user.id] = f"wac_{'y1' if '2006' in m.text else 'y2'}"
        bot.send_message(m.chat.id, f"<b>Kanal ma'lumotlarini yuboring (Login:Parol):</b>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith("edp_"))
def ed_p(c):
    bot.answer_callback_query(c.id)
    usr_st[c.from_user.id] = f"setp_{c.data[4:]}"
    bot.send_message(c.message.chat.id, f"<b>Yangi qiymatni yuboring (faqat raqam):</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)) in ["set_chan", "brd_msg", "add_adm", "set_c", "set_a"] or str(usr_st.get(m.from_user.id)).startswith("setp_") or str(usr_st.get(m.from_user.id)).startswith("wac_"))
def adm_st(m):
    st = usr_st[m.from_user.id]
    
    if st == "set_chan":
        u_set('m_chan', " " if m.text == "0" else m.text)
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Saqlandi!")
        
    elif st == "brd_msg":
        if m.text == "/cancel":
            usr_st[m.from_user.id] = None
            return bot.send_message(m.chat.id, "Xabarnoma bekor qilindi.")
            
        bot.send_message(m.chat.id, f"{ce_f('time', '⏳')} Yuborilmoqda...")
        def send_broadcast():
            for x in users_db.find({}):
                try:
                    bot.copy_message(x["_id"], m.chat.id, m.message_id)
                    time.sleep(0.05)
                except:
                    pass
        threading.Thread(target=send_broadcast).start()
        
    elif st.startswith("setp_") and m.text.isdigit():
        u_set(st[5:], m.text)
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} Saqlandi!")
        
    elif st == "add_adm" and m.text.isdigit():
        admins_db.update_one({"_id": int(m.text)}, {"$set": {"_id": int(m.text)}}, upsert=True)
        bot.send_message(m.chat.id, "Admin qo'shildi!")
        
    elif st == "set_c":
        u_set('card', m.text)
        bot.send_message(m.chat.id, "Karta saqlandi!")
        
    elif st == "set_a":
        u_set('admin', m.text)
        bot.send_message(m.chat.id, "Admin username saqlandi!")
        
    elif st.startswith("wac_"):
        accounts_db.insert_one({"type": st.split('_')[1], "data": m.text})
        # Kanal qo'shilgach menyu o'zi yangilanishi uchun:
        bot.send_message(m.chat.id, "Kanal bazaga muvaffaqiyatli qo'shildi!", reply_markup=a_menu())
        
    usr_st[m.from_user.id] = None

# To'lov qabul qilish tizimi
@bot.message_handler(func=lambda m: "Hisob to'ldirish" in m.text)
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

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == "manual_amount")
def manual_amount(m):
    if not m.text or not m.text.isdigit():
        return bot.send_message(m.chat.id, "‼️ Faqat raqam kiriting.")
        
    amount = int(m.text)
    if amount < 1000:
        return bot.send_message(m.chat.id, "⚠️ Minimal to'lov: 1,000 so'm")
        
    try:
        r = payments_db.insert_one({"user_id": m.from_user.id, "amount": amount, "status": "awaiting_receipt", "created_at": int(time.time()), "method": "manual"})
        usr_st[m.from_user.id] = f"receipt_{str(r.inserted_id)}"
        
        txt = f"""
{ce_f('card', '💳')} <b>To'lov qilish</b>
━━━━━━━━━━━━━━━━━━━━
💵 Summa: <b>{amount:,} so'm</b>
💳 Karta: <code>{g_set('card')}</code>

📸 To'lov qilib bo'lgach, chek yoki skrinshotni shu yerga tashlang!
⏳ <i>Kutilmoqda...</i>
"""
        bot.send_message(m.chat.id, txt, parse_mode="HTML")
    except:
        usr_st[m.from_user.id] = None
        bot.send_message(m.chat.id, "Xatolik yuz berdi.")

@bot.message_handler(content_types=["photo", "document"])
def receive_receipt_fallback(m):
    st = str(usr_st.get(m.from_user.id, ""))
    pid = st[8:] if st.startswith("receipt_") else None
    
    if not pid:
        pay = payments_db.find_one({"user_id": m.from_user.id, "status": "awaiting_receipt"})
        if pay:
            pid = str(pay["_id"])
        else:
            return
            
    from bson import ObjectId
    try:
        oid = ObjectId(pid)
    except:
        return bot.send_message(m.chat.id, "Ariza topilmadi.")
        
    fid = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id
    receipt_kind = "photo" if m.content_type == "photo" else "document"
    
    payments_db.update_one({"_id": oid, "status": "awaiting_receipt"}, {"$set": {"status": "pending_admin", "receipt_file_id": fid, "receipt_kind": receipt_kind}})
    usr_st[m.from_user.id] = None
    
    bot.send_message(m.chat.id, f"{ce_f('check', '✅')} <b>Chek qabul qilindi!</b>\n⏳ Admin tekshiradi. 5-30 daqiqa ichida javob beramiz.", parse_mode="HTML")
    
    pay = payments_db.find_one({"_id": oid})
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
        
        ref = users_db.find_one({"_id": uid}).get("r", 0)
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
    bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=cap + f"\n\n{status_t}", parse_mode='HTML')

@bot.message_handler(content_types=['video', 'text'], func=lambda m: usr_st.get(m.from_user.id) == "set_guide")
def save_guide_video(m):
    if m.content_type == 'video':
        u_set('guide_vid', m.video.file_id)
        u_set('guide_txt', m.caption if m.caption else "🤖 Botingizdan foydalanish bo'yicha qisqacha qo'llanma.")
        usr_st[m.from_user.id] = None
        bot.send_message(m.chat.id, f"{ce_f('check', '✅')} <b>Qo'llanma saqlandi!</b>", parse_mode='HTML')
    else:
        bot.send_message(m.chat.id, "‼️ Faqat VIDEO yuboring.")

# Grizzly Nomer olish qismi
C_LIST = [
    ("0", "Rossiya 🇷🇺"), ("1", "Ukraina 🇺🇦"), ("2", "Qozog'iston 🇰🇿"), ("12", "AQSh 🇺🇸"),
    ("36", "Kanada 🇨🇦"), ("81", "Argentina (Gmail) 🇦🇷"), ("16", "Angliya 🇬🇧"), ("6", "Indoneziya 🇮🇩"),
    ("3", "Xitoy 🇨🇳"), ("4", "Filippin 🇵🇭"), ("5", "Myanma 🇲🇲"), ("7", "Malayziya 🇲🇾"),
    ("31", "JAR 🇿🇦"), ("34", "Estoniya 🇪🇪"), ("73", "Braziliya 🇧🇷"), ("21", "Ispaniya 🇪🇸")
]
S_LIST = [("vk", "VKontakte"), ("go", "Google"), ("yt", "YouTube"), ("fb", "Facebook"), ("ig", "Instagram"), ("dt", "TikTok"), ("wa", "WhatsApp")]

@bot.callback_query_handler(func=lambda c: c.data == "none")
def none_cb(c):
    bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: "Nomer olish" in m.text)
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
    gk = g_k("USD", 12700)
    mv = get_m('m_nomer')
    mk = IK(row_width=2)
    btns = []
    
    for cid, cname in C_LIST[page*8:page*8+8]:
        cost = pr.get(cid)
        if cost:
            price_uzs = int(cost * gk * mv)
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

@bot.callback_query_handler(func=lambda c: c.data.startswith("tg_p_"))
def tg_pg(c):
    bot.answer_callback_query(c.id)
    gen_page("tg", "tg", int(c.data.split('_')[2]), c.message.chat.id, c.message.message_id)

def gen_top(prefix, sc, c_id, msg_id):
    pr = get_gz_pr(sc=sc)
    gk = g_k("USD", 12700)
    mv = get_m('m_nomer')
    valid_c = []
    
    for cid, cname in C_LIST:
        if cid in pr:
            valid_c.append((cid, cname, pr[cid]))
            
    mk = IK(row_width=2)
    btns = []
    
    for cid, cname, p_usd in sorted(valid_c, key=lambda x: x[2])[:6]:
        price_uzs = int(p_usd * gk * mv)
        btns.append(IB(f"{cname} - {price_uzs:,} so'm", callback_data=f"buy_{sc}_{cid}_{price_uzs}"))
        
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
        
    mk.add(IB("🔙 Orqaga", callback_data=f"{prefix}_p_0"))
    
    try:
        bot.edit_message_text("⭐ <b>TOP 6 eng arzon davlatlar:</b>", c_id, msg_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

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
    gk = g_k("USD", 12700)
    mv = get_m('m_nomer')
    
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
            price_uzs = int(cost * gk * mv)
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

@bot.callback_query_handler(func=lambda c: c.data.startswith("ck_") or c.data.startswith("cl_"))
def ck_cl(c):
    bot.answer_callback_query(c.id)
    p = c.data.split('_')
    
    if p[0] == "ck":
        code, body, err = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "getStatus", "id": p[1]}, timeout=15)
        
        if body.startswith("STATUS_WAIT") or "WAIT" in body:
            mk = IK().add(
                IB("🔎 SMS olish", callback_data=f"ck_{p[1]}_{p[2]}"),
                IB("❌ Bekor qilish", callback_data=f"cl_{p[1]}_{p[2]}")
            )
            try:
                bot.edit_message_text(f"⏳ <b>SMS kutilmoqda...</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
            except:
                pass
                
        elif body.startswith("STATUS_OK") or body.startswith("OK:"):
            sms_code = body.split(':')[1] if ':' in body else body.replace('OK:', '')
            try:
                bot.edit_message_text(f"✅ <b>SMS KOD KELDI!</b>\n\n🔑 <b>KOD:</b> <code>{sms_code}</code>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            except:
                pass
                
        else:
            mk = IK().add(
                IB("🔎 SMS olish", callback_data=f"ck_{p[1]}_{p[2]}"),
                IB("❌ Bekor qilish", callback_data=f"cl_{p[1]}_{p[2]}")
            )
            try:
                bot.edit_message_text(f"⏳ <b>Holat: {body[:50]}</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
            except:
                pass
                
    elif p[0] == "cl":
        code, cancel_body, _ = http_get_text("https://api.grizzlysms.com/stubs/handler_api.php", {"api_key": GRIZZLY_API_KEY, "action": "setStatus", "status": 8, "id": p[1]}, timeout=15)
        
        if "ACCESS_CANCEL" in cancel_body:
            u_bal(c.from_user.id, int(p[2]))
            try:
                bot.edit_message_text(f"✅ <b>Bekor qilindi!</b>\n💵 <b>Pul qaytdi:</b> {int(p[2]):,} so'm", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            except:
                pass
        else:
            mk = IK().add(
                IB("❌ Bekor qilish", callback_data=f"cl_{p[1]}_{p[2]}"),
                IB("🔙 Orqaga", callback_data="ot_p_0")
            )
            try:
                bot.edit_message_text(f"⏳ <b>Nomer hali bekor qilinmadi. 1-2 daqiqadan so'ng urinib ko'ring.</b>", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
            except:
                pass

# Tayyor Kanallar
@bot.message_handler(func=lambda m: "Tayyor Kanallar" in m.text)
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
        p = int(g_set('p_' + k))
        if has_sk:
            mk.add(IB(f"{n} ({c} ta qoldi) - {p-15000:,} so'm (Skidka)", callback_data=f"by_{k}"))
        else:
            mk.add(IB(f"{n} ({c} ta qoldi) - {p:,} so'm", callback_data=f"by_{k}"))
            
    p_2func = int(g_set('p_2func'))
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
                return bot.answer_callback_query(c.id, "🔴 Pul kam!", show_alert=True)
                
            u_bal(c.from_user.id, -pr)
            usr_st[c.from_user.id] = f"wn_{t[2]}"
            bot.edit_message_text("🛠 <b>Ma'lumot yuboring (Yo'nalish/Link):</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            
        else:
            pr = int(g_set('p_' + t[1]))
            if has_sk:
                pr -= 15000
                
            if g_bal(c.from_user.id) < pr:
                return bot.answer_callback_query(c.id, "🔴 Pul kam!", show_alert=True)
                
            u_bal(c.from_user.id, -pr)
            acc = accounts_db.find_one({"type": t[1]})
            
            if acc:
                accounts_db.delete_one({"_id": acc["_id"]})
                bot.edit_message_text(f"✅ <b>KANAL:</b>\n<code>{acc['data']}</code>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
            else:
                orders_db.insert_one({"user_id": c.from_user.id, "oid": "YT", "link": t[1], "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Kutmoqda"})
                bot.edit_message_text(f"✅ <b>Kuting! Admin yuboradi.</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
                adm_msg(f"🔔 <b>YANGI KANAL BUYURTMASI:</b>\n👤 Mijoz ID: <code>{c.from_user.id}</code>\n📦 Turi: {t[1]}", rm=IK().add(IB("📤 Yuborish", callback_data=f"snd_{c.from_user.id}")))
                
    except Exception as e:
        print(f"Tayyor kanallar xatosi: {e}")

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)).startswith("wn_"))
def sv_nch(m):
    t = usr_st[m.from_user.id].split('_')[1]
    if m.text in [f"{E_BAG} Xizmatlar", "🏠 Bosh sahifa"]:
        u_bal(m.from_user.id, int(g_set('p_' + t)))
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Bekor qilindi. Pul qaytdi.")
        
    orders_db.insert_one({"user_id": m.from_user.id, "oid": t, "link": "Buyurtma", "quantity": 1, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Kutmoqda"})
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, f"✅ <b>Qabul qilindi!</b>", parse_mode='HTML')
    
    adm_msg(f"🔔 <b>YANGI XIZMAT BUYURTMASI:</b>\n👤 Mijoz ID: <code>{m.from_user.id}</code>\n📝 Ma'lumoti:\n<code>{m.text}</code>", rm=IK().add(IB("📤 Yuborish", callback_data=f"snd_{m.from_user.id}")))

@bot.callback_query_handler(func=lambda c: c.data.startswith("snd_"))
def rq_snd(c):
    bot.answer_callback_query(c.id)
    usr_st[c.from_user.id] = f"fw_{c.data.split('_')[1]}"
    bot.send_message(c.message.chat.id, f"<b>Ma'lumot kiriting:</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: str(usr_st.get(m.from_user.id)).startswith("fw_"))
def fw_m(m):
    uid = int(usr_st[m.from_user.id].split('_')[1])
    usr_st[m.from_user.id] = None
    try:
        bot.send_message(uid, f"🎁 <b>Tayyor:</b>\n<code>{m.text}</code>", parse_mode='HTML')
        bot.send_message(m.chat.id, "✅ Yuborildi!")
        orders_db.update_one({"user_id": uid, "status": "Kutmoqda"}, {"$set": {"status": "Bajarildi ✅"}})
    except:
        pass

# SMM Xizmatlar Qismi
@bot.message_handler(func=lambda m: "Xizmatlar" in m.text and "Tayyor" not in m.text)
def smm_services(m):
    if not c_sub(m.from_user.id):
        return req_sub(m.chat.id, m.from_user.id)
        
    txt = f"🛍 <b>@{bot.get_me().username} sizga Tezkor, Arzon va Sifatli xizmatlarni taqdim etadi!</b>"
    mk = IK(row_width=2).add(
        IB("Telegram", callback_data="mp_tg", icon_custom_emoji_id="5456281420106315074"),
        IB("Instagram", callback_data="mp_ig", icon_custom_emoji_id="5319160079465857105"),
        IB("TikTok", callback_data="mp_tt", icon_custom_emoji_id="5327982530702359565"),
        IB("YouTube", callback_data="mp_yt", icon_custom_emoji_id="5456299961480132196"),
        IB("🔍 Qidirish", callback_data="search_services"),
        IB("🛒 Barcha xizmatlar", callback_data="all_services")
    )
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')

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
        for s in services:
            mk.add(IB(f"🔹 {s['name']} - ${s['rate']}/1000", callback_data=f"sq_{s['service']}_all"))
        mk.add(IB("🔙 Orqaga", callback_data="none"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == "search_mode")
def search_handler(m):
    if m.text in [f"{E_BAG} Xizmatlar", "🏠 Bosh sahifa"]:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, "Bekor qilindi.", reply_markup=m_menu(m.from_user.id))
        
    usr_st[m.from_user.id] = None
    query = m.text.lower()
    results = [s for s in g_smm() if query in s['name'].lower() or query in s['category'].lower()]
    
    if not results:
        return bot.send_message(m.chat.id, f"❌ <b>Xizmat topilmadi.</b>", parse_mode='HTML')
        
    txt = f"🔍 <b>Qidiruv natijasi: '{m.text}'</b>\nTopildi: <b>{len(results)}</b> ta\n\n"
    mk = IK(row_width=1)
    for s in results[:15]:
        mk.add(IB(f"🔹 {s['name']} - ${s['rate']}/1000", callback_data=f"sq_{s['service']}_search"))
    mk.add(IB("🔙 Orqaga", callback_data="none"))
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
        
    mk.add(IB("🔙 Orqaga", callback_data="none"))
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
    sl = []
    if len(f) > 0: sl.append(("🥈 Arzon", f[0]))
    if len(f) > 1: sl.append(("🥇 Tezkor", f[1]))
    if len(f) > 2: sl.append(("💎 Premium", f[2]))
    
    mv = get_m('m_yt_sub') if cid == 'sub' else (get_m('m_yt_watch') if cid == 'watch' else get_m('m_smm'))
    gk = g_k("USD", 12700)
    mk = IK(row_width=1)
    txt = f"🛍 <b>Sifatni tanlang:</b>\n\n"
    
    for l, srv in sl:
        price_uzs = int(safe_float(srv.get('rate', '0')) * gk * mv)
        txt += f"🔹 <b>{l}</b>\n   💵 {price_uzs:,} so'm (1000 ta)\n   📉 Min: {srv.get('min')} | Max: {srv.get('max')}\n\n"
        mk.add(IB(f"{l} - {price_uzs:,} so'm", callback_data=f"sq_{srv['service']}_{cid}"))
        
    mk.add(IB("🔙 Orqaga", callback_data=f"mp_{p}"))
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode='HTML')
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("sq_"))
def sq_sel(c):
    bot.answer_callback_query(c.id)
    parts = c.data.split('_')
    sid = parts[1]
    cid = parts[2]
    
    srv = next((x for x in g_smm() if str(x.get('service')) == sid), None)
    if not srv:
        return bot.answer_callback_query(c.id, "Xizmat topilmadi")
        
    mv = get_m('m_yt_sub') if cid == 'sub' else (get_m('m_yt_watch') if cid == 'watch' else get_m('m_smm'))
    
    def safe_float(v):
        try:
            return float(str(v).replace(',','.'))
        except:
            return 0.0
            
    pr = int(safe_float(srv.get('rate', '0')) * g_k("USD", 12700) * mv)
    
    txt = f"🛍 <b>Tanlandi: {srv['name']}</b>\n💵 <b>Narx:</b> {pr:,} so'm (1000 ta)\n🔗 <b>Link yuboring:</b>"
    try:
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode='HTML')
    except:
        pass
        
    usr_st[c.from_user.id] = 'wl'
    tmp_dt[c.from_user.id] = {'s': sid, 'p': pr, 'm': int(srv.get('min',10)), 'x': int(srv.get('max',10000))}

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'wl')
def pl(m):
    tmp_dt[m.from_user.id]['l'] = m.text
    usr_st[m.from_user.id] = 'wq'
    bot.send_message(m.chat.id, f"🔢 <b>Qancha kerak? (Raqam yozing):</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'wq')
def pq(m):
    if not m.text.isdigit():
        return bot.send_message(m.chat.id, "Raqam yozing!")
        
    q = int(m.text)
    d = tmp_dt.get(m.from_user.id)
    
    if not d:
        return bot.send_message(m.chat.id, "Xato! Boshqatdan kiring.")
        
    t = int((d['p']/1000)*q)
    
    if q < d['m'] or q > d['x'] or g_bal(m.from_user.id) < t:
        usr_st[m.from_user.id] = None
        return bot.send_message(m.chat.id, f"⚠️ Pul kam yoki limit xato!\nKerak: {t:,} so'm\nBalans: {g_bal(m.from_user.id):,} so'm")
        
    u_bal(m.from_user.id, -t)
    bot.send_message(m.chat.id, f"⏳ Saytga yuborilmoqda...", parse_mode='HTML')
    
    try:
        r = requests.get(SMM_API_URL, params={'key': SMM_API_KEY, 'act': 'new_order', 'service_id': d['s'], 'link': d['l'], 'count': q}, timeout=20).json()
        
        if 'res' in r and isinstance(r['res'], dict) and r['res'].get('status') == 'ok':
            oid = str(r['res'].get('order_id', 'N/A'))
            bot.send_message(m.chat.id, f"✅ <b>Qabul qilindi!</b>\nBuyurtma ID: <code>{oid}</code>\n💵 To'langan: {t:,} so'm", parse_mode='HTML')
            orders_db.insert_one({"user_id": m.from_user.id, "oid": oid, "link": d['l'], "quantity": q, "date": datetime.now().strftime("%Y.%m.%d %H:%M:%S"), "status": "Yuborildi"})
        else:
            u_bal(m.from_user.id, t)
            bot.send_message(m.chat.id, f"❌ Xato: {r}", parse_mode='HTML')
            
    except Exception as e:
        u_bal(m.from_user.id, t)
        bot.send_message(m.chat.id, f"⚠️ Sistem xatosi yuz berdi.", parse_mode='HTML')
        
    usr_st[m.from_user.id] = None

# Custom emoji uchun yordamchi
@bot.message_handler(content_types=['text'])
def fallback_text_handler(m):
    if m.text and not m.text.startswith('/'):
        bot.send_message(m.chat.id, "🤖 Kechirasiz, faqat menyudagi tugmalardan foydalaning.", reply_markup=m_menu(m.from_user.id))

# Web Server qismi (Flask 24/7)
app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot 24/7 rejimida ishlamoqda!"

def run_server():
    port = int(os.environ.get("PORT", 8080) if os.environ.get("PORT") else 8080)
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server).start()

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
