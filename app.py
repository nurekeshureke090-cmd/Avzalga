import telebot
import requests
import time
import os
import threading
from datetime import datetime
from telebot.types import (
    ReplyKeyboardMarkup as RK, KeyboardButton as KB,
    InlineKeyboardMarkup as IK, InlineKeyboardButton as IB,
    WebAppInfo
)
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient
import dns.resolver
from bson import ObjectId

# ==================== SOZLAMALAR ====================
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

TOKEN = os.environ.get('BOT_TOKEN', '9135967685:AAFt935w1f7sKsKdX9i1tpBOyEmqQnZILlU')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 8467707826))
GRIZZLY_API_KEY = os.environ.get('GRIZZLY_API_KEY', '3335af0d250efb73bdc40ebf82fa42dd')
MONGO_URL = os.environ.get('MONGO_URL', "mongodb+srv://nurekeshureke090_db_user:qKFmlTnxjnAe27Gi@cluster0.1dcdbiw.mongodb.net/?appName=Cluster0")

# Mini App manzili (Ngrok yoki VPS domenini kiritish mumkin, masalan: https://mydomain.com)
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'http://127.0.0.1:8080')

bot = telebot.TeleBot(TOKEN, num_threads=50)
usr_st = {}

# MongoDB ulanishi
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
    'p_gemini': '50000',
    'm_nomer': '20',
    'bot_desc': 'Virtual Nomerlar, Tayyor Kanallar & Gemini Obunasi'
}

for k, v in defaults.items():
    if not settings_db.find_one({"_id": k}):
        settings_db.insert_one({"_id": k, "value": str(v)})

# Valyuta kursi kesh
K_C = {"USD": {"r": 12850.0, "t": 0}}
def g_k(c="USD", d=12850.0):
    if time.time() - K_C[c]["t"] > 3600:
        try:
            r = requests.get(f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/{c}/", timeout=4).json()
            K_C[c]["r"] = float(r[0]['Rate'])
            K_C[c]["t"] = time.time()
        except:
            K_C[c]["r"] = d
    return K_C[c]["r"]

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
    user = users_db.find_one({"_id": int(id)})
    return int(user.get('balance', 0)) if user else 0

def u_bal(id, amt):
    users_db.update_one({"_id": int(id)}, {"$inc": {"balance": int(amt)}}, upsert=True)

def g_set(k):
    res = settings_db.find_one({"_id": k})
    return str(res.get('value', " ")) if res else " "

def u_set(k, v):
    settings_db.update_one({"_id": k}, {"$set": {"value": str(v)}}, upsert=True)

def get_m(k='m_nomer'):
    try:
        return 1.0 + (int(g_set(k)) / 100.0)
    except:
        return 1.20

def get_country_m(cid):
    val = g_set(f'm_num_{cid}')
    if val != " ":
        try: return 1.0 + (int(val) / 100.0)
        except: pass
    return get_m('m_nomer')

C_LIST = [
    ("0", "Rossiya 🇷🇺"), ("1", "Ukraina 🇺🇦"), ("2", "Qozog'iston 🇰🇿"), ("12", "AQSh 🇺🇸"),
    ("36", "Kanada 🇨🇦"), ("81", "Argentina 🇦🇷"), ("16", "Angliya 🇬🇧"), ("6", "Indoneziya 🇮🇩"),
    ("3", "Xitoy 🇨🇳"), ("4", "Filippin 🇵🇭"), ("5", "Myanma 🇲🇲"), ("7", "Malayziya 🇲🇾"),
    ("31", "JAR 🇿🇦"), ("34", "Estoniya 🇪🇪"), ("73", "Braziliya 🇧🇷"), ("21", "Ispaniya 🇪🇸")
]

# Grizzly API narxlari
def get_gz_prices(sc="tg"):
    try:
        url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={GRIZZLY_API_KEY}&action=getPrices&service={sc}"
        r = requests.get(url, timeout=10).json()
        prices = {}
        for c_id, s_data in r.items():
            if isinstance(s_data, dict) and sc in s_data:
                cnt = int(s_data[sc].get('count', 1))
                if cnt > 0:
                    v = s_data[sc].get('cost') or s_data[sc].get('price')
                    if v: prices[str(c_id)] = float(v)
        return prices
    except:
        return {}

def req_gz_number(sc, cid):
    try:
        url = "https://api.grizzlysms.com/stubs/handler_api.php"
        r = requests.get(url, params={"api_key": GRIZZLY_API_KEY, "action": "getNumber", "service": sc, "country": cid}, timeout=15)
        body = r.text.strip()
        if "ACCESS_NUMBER:" in body:
            parts = body.split(":")
            return {"s": True, "id": parts[1], "n": ":".join(parts[2:])}
        elif "NO_NUMBERS" in body:
            return {"s": False, "m": "Hozirda bu davlatda bo'sh nomer qolmagan"}
        elif "NO_BALANCE" in body:
            return {"s": False, "m": "Texnik xatolik, iltimos keyinroq urinib ko'ring"}
        return {"s": False, "m": body}
    except Exception as e:
        return {"s": False, "m": str(e)}

# Obuna tekshirish
def c_sub(uid):
    ch = g_set('m_chan').strip()
    if not ch or ch == " " or is_adm(uid):
        return True
    try:
        return bot.get_chat_member(ch, uid).status in ['member', 'administrator', 'creator']
    except:
        return True

# ==================== BOT MENYULARI ====================
def m_menu(uid):
    m = RK(resize_keyboard=True, row_width=2)
    web_app_btn = KB("🚀 Do'konni ochish (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))
    m.add(web_app_btn)
    m.add(KB("💳 Hisob to'ldirish"), KB("👤 Mening hisobim"))
    m.add(KB("📦 Buyurtmalarim"), KB("💬 Qo'llab-quvvatlash"))
    if is_adm(uid):
        m.add(KB("👑 Admin Panel"))
    return m

def a_menu():
    y1_cnt = accounts_db.count_documents({"type": "y1"})
    y2_cnt = accounts_db.count_documents({"type": "y2"})
    return RK(resize_keyboard=True, row_width=2).add(
        KB(f"➕ 2006-2009 ({y1_cnt} ta)"),
        KB(f"➕ 2010-2019 ({y2_cnt} ta)"),
        KB("📊 Statistika"),
        KB("💳 Karta o'zgartirish"),
        KB("⚙️ Narxlarni o'zgartirish"),
        KB("💯 Foizlarni o'zgartirish"),
        KB("🔔 Kanal ulash"),
        KB("✉️ Xabarnoma"),
        KB("👑 Admin qo'shish"),
        KB("💬 Murojaat o'zgartirish"),
        KB("🏠 Bosh sahifa")
    )

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def handle_start(m):
    uid = m.from_user.id
    ref = 0
    is_skidka = False
    args = m.text.split()
    if len(args) > 1:
        if args[1] == 'skidka': is_skidka = True
        elif args[1].isdigit(): ref = int(args[1])

    ref = 0 if ref == uid else ref
    user = users_db.find_one({"_id": uid})
    if not user:
        users_db.insert_one({"_id": uid, "balance": 0, "r": ref, "skidka": is_skidka})
        if ref:
            try:
                bot.send_message(ref, f"🔔 <b>Do'stingiz taklif havolangiz orqali botga qo'shildi!</b>\nU hisobini to'ldirganda sizga 5% bonus taqdim etiladi.", parse_mode='HTML')
            except: pass
    elif is_skidka and not user.get("skidka"):
        users_db.update_one({"_id": uid}, {"$set": {"skidka": True}})

    if not c_sub(uid):
        ch = g_set('m_chan').replace('@', '').strip()
        mk = IK(row_width=1).add(
            IB("➕ Kanalga a'zo bo'lish", url=f"https://t.me/{ch}"),
            IB("🔄 Tekshirish", callback_data="ck_sub")
        )
        return bot.send_message(m.chat.id, f"⚠ <b>Botdan to'liq foydalanish uchun kanalimizga a'zo bo'ling:</b>\n@{ch}", reply_markup=mk, parse_mode='HTML')

    txt = f"""
👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>

🏪 <b>Xush kelibsiz!</b>
Bu yerda siz:
• 📱 <b>Virtual Nomerlar</b> (20+ davlatlar)
• 🔴 <b>Tayyor YouTube Kanallar</b> (2006-2019)
• ✨ <b>Gemini Advanced Obunasi</b>
• 🛠 <b>YouTube 2-funksiya ulanishi</b>

👇 Barcha xizmatlarni qulay va zamonaviy <b>Mini App</b> orqali xarid qilishingiz mumkin:
"""
    bot.send_message(m.chat.id, txt, reply_markup=m_menu(uid), parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "ck_sub")
def callback_check_sub(c):
    if c_sub(c.from_user.id):
        bot.answer_callback_query(c.id, "Rahmat!")
        try: bot.delete_message(c.message.chat.id, c.message.message_id)
        except: pass
        bot.send_message(c.message.chat.id, "✅ <b>Rahmat! Menyuga marhamat:</b>", reply_markup=m_menu(c.from_user.id), parse_mode='HTML')
    else:
        bot.answer_callback_query(c.id, "❌ Hali kanalga a'zo bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh sahifa")
def handle_home(m):
    usr_st[m.from_user.id] = None
    bot.send_message(m.chat.id, "🏠 <b>Asosiy menyuga qaytdingiz:</b>", reply_markup=m_menu(m.from_user.id), parse_mode='HTML')

@bot.message_handler(func=lambda m: "Mening hisobim" in m.text)
def handle_profile(m):
    bal = g_bal(m.from_user.id)
    bot_info = bot.get_me()
    txt = f"""
👤 <b>Shaxsiy Kabinetingiz</b>
━━━━━━━━━━━━━━━━━━━━
🆔 Sizning ID: <code>{m.from_user.id}</code>
💵 Balansingiz: <b>{bal:,} so'm</b>

🎁 <b>Referal dasturi:</b>
Do'stlaringizga havola yuboring va ularning to'lovidan <b>5%</b> bonus oling!
🔗 <code>https://t.me/{bot_info.username}?start={m.from_user.id}</code>
"""
    mk = IK(row_width=1).add(
        IB("🚀 Mini App orqali ochish", web_app=WebAppInfo(url=WEBAPP_URL)),
        IB("💳 Hisob to'ldirish", callback_data="btn_dep_now")
    )
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "btn_dep_now")
def cb_dep_now(c):
    bot.answer_callback_query(c.id)
    usr_st[c.from_user.id] = "manual_amount"
    bot.send_message(c.message.chat.id, "💵 <b>Necha so'm to'ldirmoqchisiz?</b>\nRaqamni yozing (masalan: 50000):", parse_mode='HTML')

@bot.message_handler(func=lambda m: "Hisob to'ldirish" in m.text)
def handle_deposit(m):
    usr_st[m.from_user.id] = "manual_amount"
    bot.send_message(m.chat.id, "💵 <b>Necha so'm to'ldirmoqchisiz?</b>\nRaqamni yozing (masalan: 50000):", parse_mode='HTML')

@bot.message_handler(func=lambda m: usr_st.get(m.from_user.id) == 'manual_amount')
def handle_amount_input(m):
    if m.text in ["🚀 Do'konni ochish (Mini App)", "💳 Hisob to'ldirish", "👤 Mening hisobim", "📦 Buyurtmalarim", "💬 Qo'llab-quvvatlash", "👑 Admin Panel"]:
        usr_st[m.from_user.id] = None
        return

    if not m.text or not m.text.isdigit():
        return bot.send_message(m.chat.id, "‼️ <b>Faqat raqamlardan foydalaning (masalan: 50000).</b>", parse_mode='HTML')

    amount = int(m.text)
    if amount < 1000:
        return bot.send_message(m.chat.id, "ℹ️ Minimal to'lov: 1,000 so'm")

    r = payments_db.insert_one({"user_id": m.from_user.id, "amount": amount, "status": "awaiting_receipt", "created_at": datetime.now()})
    usr_st[m.from_user.id] = f"receipt_{str(r.inserted_id)}"

    txt = f"""
💳 <b>To'lovni amalga oshiring:</b>

➡️ Karta raqami: <code>{g_set('card')}</code>
💵 Summa: <b>{amount:,} so'm</b>

📸 <b>DIQQAT:</b> To'lov qilgach, chek rasmini (screenshot) shu yerga yuboring!
"""
    mk = IK().add(IB("❌ Bekor qilish", callback_data="cancel_pay"))
    bot.send_message(m.chat.id, txt, reply_markup=mk, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "cancel_pay")
def cb_cancel_pay(c):
    usr_st[c.from_user.id] = None
    bot.answer_callback_query(c.id, "Bekor qilindi")
    bot.send_message(c.message.chat.id, "❌ To'lov bekor qilindi.", reply_markup=m_menu(c.from_user.id))

@bot.message_handler(content_types=['photo', 'document'], func=lambda m: str(usr_st.get(m.from_user.id, "")).startswith("receipt_"))
def handle_receipt_photo(m):
    st = usr_st.get(m.from_user.id, "")
    pid = st[8:]
    try:
        oid = ObjectId(pid)
    except:
        return bot.send_message(m.chat.id, "Ariza topilmadi.")

    fid = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id
    kind = "photo" if m.content_type == "photo" else "document"

    payments_db.update_one({"_id": oid, "status": "awaiting_receipt"}, {"$set": {"status": "pending_admin", "receipt_file_id": fid, "receipt_kind": kind}})
    usr_st[m.from_user.id] = None

    bot.send_message(m.chat.id, "✅ <b>Chek qabul qilindi!</b>\n⏳ Admin tekshirib 5-15 daqiqa ichida hisobingizga pul o'tkazadi.", parse_mode='HTML')

    pay = payments_db.find_one({"_id": oid})
    kb = IK(row_width=2).add(
        IB("✅ TASDIQLASH", callback_data=f"pay_ok_{pid}"),
        IB("❌ RAD ETISH", callback_data=f"pay_no_{pid}")
    )
    cap = f"💳 <b>YANGI TO'LOV CHEKI:</b>\n👤 User: <code>{m.from_user.id}</code>\n💵 Summa: <b>{int(pay['amount']):,} so'm</b>"
    for aid in g_adms():
        try:
            if kind == "photo": bot.send_photo(aid, fid, caption=cap, reply_markup=kb, parse_mode="HTML")
            else: bot.send_document(aid, fid, caption=cap, reply_markup=kb, parse_mode="HTML")
        except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_ok_") or c.data.startswith("pay_no_"))
def cb_admin_pay_approval(c):
    if not is_adm(c.from_user.id):
        return bot.answer_callback_query(c.id, "Ruxsat berilmagan.")

    action = "paid" if c.data.startswith("pay_ok_") else "rejected"
    pid = c.data[7:]
    pay = payments_db.find_one_and_update({"_id": ObjectId(pid), "status": "pending_admin"}, {"$set": {"status": action, "time": int(time.time())}})
    if not pay:
        return bot.answer_callback_query(c.id, "Bu to'lov allaqachon ko'rib chiqilgan.")

    uid = int(pay["user_id"])
    amount = int(pay["amount"])

    if action == "paid":
        u_bal(uid, amount)
        users_db.update_one({"_id": uid}, {"$inc": {"total_deposited": amount}}, upsert=True)
        ref = users_db.find_one({"_id": uid}).get("r", 0)
        if ref and int(amount * 0.05) > 0:
            u_bal(ref, int(amount * 0.05))
            try: bot.send_message(ref, f"🎁 <b>Referal bonus!</b> Sizga <b>{int(amount * 0.05):,} so'm</b> qo'shildi!", parse_mode='HTML')
            except: pass
        try: bot.send_message(uid, f"✅ <b>To'lovingiz tasdiqlandi!</b>\n💵 Hisobingizga <b>{amount:,} so'm</b> qo'shildi.", parse_mode='HTML')
        except: pass
    else:
        try: bot.send_message(uid, f"❌ <b>To'lovingiz rad etildi.</b>\nSumma: {amount:,} so'm", parse_mode='HTML')
        except: pass

    bot.answer_callback_query(c.id, "Saqlandi!")
    status_label = "✅ TASDIQLANDI" if action == "paid" else "❌ RAD ETILDI"
    try: bot.edit_message_caption(f"{c.message.caption}\n\n<b>Status: {status_label}</b>", c.message.chat.id, c.message.message_id, parse_mode='HTML')
    except: pass

@bot.message_handler(func=lambda m: "Buyurtmalarim" in m.text)
def handle_orders(m):
    r = list(orders_db.find({"user_id": m.from_user.id}).sort("_id", -1).limit(5))
    if not r:
        return bot.send_message(m.chat.id, "📭 Hozircha sizda buyurtmalar yo'q.")
    txt = "📋 <b>So'nggi buyurtmalaringiz:</b>\n\n"
    for i, x in enumerate(r, 1):
        txt += f"<b>#{i}. {x.get('oid', 'Xizmat')}</b>\nHolat: {x.get('status', 'Kutmoqda')}\nSana: {x.get('date', 'N/A')}\n\n"
    bot.send_message(m.chat.id, txt, parse_mode='HTML')

@bot.message_handler(func=lambda m: "Qo'llab-quvvatlash" in m.text)
def handle_support(m):
    admin = g_set('admin')
    bot.send_message(m.chat.id, f"💬 <b>Qo'llab-quvvatlash xizmati:</b>\n\nSavol yoki muammolar bo'lsa adminga murojaat qiling:\n👤 {admin}", parse_mode='HTML')

# ==================== ADMIN PANEL ====================
@bot.message_handler(func=lambda m: "Admin Panel" in m.text and is_adm(m.from_user.id))
def handle_admin_panel(m):
    y1_cnt = accounts_db.count_documents({"type": "y1"})
    y2_cnt = accounts_db.count_documents({"type": "y2"})
    txt = f"""
👑 <b>Admin Panel</b>

📦 <b>Bazadagi kanallar:</b>
🔴 2006-09: <b>{y1_cnt} ta</b>
🟠 2010-19: <b>{y2_cnt} ta</b>

<b>Tezkor buyruqlar:</b>
• <code>/addbalance ID SUMMA</code> — Balans berish
• <code>/info ID</code> — Foydalanuvchi ma'lumoti
"""
    bot.send_message(m.chat.id, txt, reply_markup=a_menu(), parse_mode='HTML')

@bot.message_handler(commands=['addbalance'])
def handle_addbalance_cmd(m):
    if not is_adm(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 3:
        return bot.send_message(m.chat.id, "⚠️ To'g'ri format: <code>/addbalance ID SUMMA</code>", parse_mode='HTML')
    try:
        uid = int(parts[1])
        amount = int(parts[2])
    except:
        return bot.send_message(m.chat.id, "❌ Faqat raqam yozing!")

    u_bal(uid, amount)
    users_db.update_one({"_id": uid}, {"$inc": {"total_deposited": amount}}, upsert=True)
    try: bot.send_message(uid, f"🎁 Balansingizga <b>{amount:,} so'm</b> qo'shildi!", parse_mode='HTML')
    except: pass
    bot.send_message(m.chat.id, f"✅ {uid} ga {amount:,} so'm qo'shildi! Yangi balans: {g_bal(uid):,} so'm", parse_mode='HTML')

@bot.message_handler(commands=['info'])
def handle_info_cmd(m):
    if not is_adm(m.from_user.id): return
    parts = m.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])
        u = users_db.find_one({"_id": uid})
        if u:
            bot.send_message(m.chat.id, f"👤 ID: <code>{uid}</code>\n💵 Balans: {int(u.get('balance',0)):,} so'm\n💰 Jami kiritgan: {int(u.get('total_deposited',0)):,} so'm", parse_mode='HTML')
        else:
            bot.send_message(m.chat.id, "Foydalanuvchi topilmadi.")

@bot.message_handler(func=lambda m: is_adm(m.from_user.id) and any(x in m.text for x in ["➕ 2006", "➕ 2010", "Karta o'zgartirish", "Narxlarni o'zgartirish", "Statistika", "Xabarnoma", "Admin qo'shish", "Murojaat o'zgartirish", "Kanal ulash"]))
def handle_admin_actions(m):
    if "Statistika" in m.text:
        u_cnt = users_db.count_documents({})
        total_bal = sum([x.get("balance", 0) for x in users_db.find()])
        bot.send_message(m.chat.id, f"📊 <b>Statistika:</b>\n👥 A'zolar: {u_cnt} ta\n💰 Foydalanuvchilar balansi: {total_bal:,} so'm", parse_mode='HTML')
    elif "➕ 2006" in m.text or "➕ 2010" in m.text:
        acc_type = 'y1' if '2006' in m.text else 'y2'
        usr_st[m.from_user.id] = f"add_acc_{acc_type}"
        bot.send_message(m.chat.id, "Kanal ma'lumotlarini (Login:Parol) yuboring:")
    elif "Karta o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_card"
        bot.send_message(m.chat.id, f"Yangi karta raqamini kiriting:\nHozirgi: <code>{g_set('card')}</code>", parse_mode='HTML')
    elif "Narxlarni o'zgartirish" in m.text:
        mk = IK(row_width=1).add(
            IB(f"2006-09: {g_set('p_y1')} so'm", callback_data="edp_p_y1"),
            IB(f"2010-19: {g_set('p_y2')} so'm", callback_data="edp_p_y2"),
            IB(f"Gemini: {g_set('p_gemini')} so'm", callback_data="edp_p_gemini"),
            IB(f"2-funksiya: {g_set('p_2func')} so'm", callback_data="edp_p_2func")
        )
        bot.send_message(m.chat.id, "⚙️ Qaysi xizmat narxini o'zgartirasiz?", reply_markup=mk)
    elif "Admin qo'shish" in m.text:
        usr_st[m.from_user.id] = "add_admin_id"
        bot.send_message(m.chat.id, "Yangi admin ID raqamini yuboring:")
    elif "Murojaat o'zgartirish" in m.text:
        usr_st[m.from_user.id] = "set_admin_user"
        bot.send_message(m.chat.id, f"Admin username (@userneyim):\nHozirgi: {g_set('admin')}")
    elif "Kanal ulash" in m.text:
        usr_st[m.from_user.id] = "set_m_chan"
        bot.send_message(m.chat.id, "Majburiy obuna kanalini (@kanal) yuboring (O'chirish uchun 0):")
    elif "Xabarnoma" in m.text:
        usr_st[m.from_user.id] = "broadcast"
        bot.send_message(m.chat.id, "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (/cancel - bekor qilish):")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edp_"))
def cb_edit_price(c):
    bot.answer_callback_query(c.id)
    key = c.data[4:]
    usr_st[c.from_user.id] = f"setval_{key}"
    bot.send_message(c.message.chat.id, "Yangi narxni (faqat raqam) yuboring:")

@bot.message_handler(func=lambda m: is_adm(m.from_user.id) and usr_st.get(m.from_user.id))
def handle_admin_text_inputs(m):
    st = usr_st[m.from_user.id]
    if st.startswith("add_acc_"):
        t = st.split("_")[2]
        accounts_db.insert_one({"type": t, "data": m.text})
        bot.send_message(m.chat.id, "✅ Kanal bazaga qo'shildi!", reply_markup=a_menu())
    elif st == "set_card":
        u_set('card', m.text)
        bot.send_message(m.chat.id, "✅ Karta saqlandi!")
    elif st == "set_admin_user":
        u_set('admin', m.text)
        bot.send_message(m.chat.id, "✅ Admin username saqlandi!")
    elif st == "set_m_chan":
        u_set('m_chan', " " if m.text == "0" else m.text)
        bot.send_message(m.chat.id, "✅ Kanal sozlamasi saqlandi!")
    elif st == "add_admin_id" and m.text.isdigit():
        admins_db.update_one({"_id": int(m.text)}, {"$set": {"_id": int(m.text)}}, upsert=True)
        bot.send_message(m.chat.id, "✅ Admin qo'shildi!")
    elif st.startswith("setval_") and m.text.isdigit():
        u_set(st[7:], m.text)
        bot.send_message(m.chat.id, "✅ Narx yangilandi!")
    elif st == "broadcast":
        if m.text == "/cancel":
            usr_st[m.from_user.id] = None
            return bot.send_message(m.chat.id, "Bekor qilindi.")
        bot.send_message(m.chat.id, "Xabar tarqatilmoqda...")
        def send_all():
            for u in users_db.find():
                try:
                    bot.copy_message(u["_id"], m.chat.id, m.message_id)
                    time.sleep(0.04)
                except: pass
        threading.Thread(target=send_all).start()

    usr_st[m.from_user.id] = None

# Admin buyurtmaga havola yuborish
@bot.callback_query_handler(func=lambda c: c.data.startswith("snd_"))
def cb_send_order_info(c):
    bot.answer_callback_query(c.id)
    parts = c.data.split('_')
    uid = parts[1]
    oid = parts[2] if len(parts) > 2 else ""
    usr_st[c.from_user.id] = f"fw_{uid}_{oid}"
    bot.send_message(c.message.chat.id, "Mijozga yuboriladigan havolani (link/parol) yuboring:")

@bot.message_handler(func=lambda m: is_adm(m.from_user.id) and str(usr_st.get(m.from_user.id, "")).startswith("fw_"))
def handle_fw_order(m):
    parts = usr_st[m.from_user.id].split('_')
    uid = int(parts[1])
    oid = parts[2] if len(parts) > 2 else ""
    usr_st[m.from_user.id] = None

    try:
        bot.send_message(uid, f"🎁 <b>Sizning buyurtmangiz tayyor!</b>\n\n🔗 <b>Havola / Ma'lumot:</b>\n{m.text}\n\n<i>Obunani o'z akkauntingizga oformit qilishingiz mumkin.</i>", parse_mode='HTML')
        bot.send_message(m.chat.id, "✅ Mijozga yuborildi!")
        if oid:
            try: orders_db.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "Bajarildi ✅"}})
            except: orders_db.update_one({"user_id": uid, "status": "Kutmoqda"}, {"$set": {"status": "Bajarildi ✅"}})
        else:
            orders_db.update_one({"user_id": uid, "status": "Kutmoqda"}, {"$set": {"status": "Bajarildi ✅"}})
    except Exception as e:
        bot.send_message(m.chat.id, f"Xatolik: {e}")

# ==================== FLASK BACKEND & WEBAPP API ====================
app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def webapp_home():
    return render_template('index.html')

@app.route('/api/user_data')
def api_user_data():
    uid = request.args.get('uid', type=int)
    if not uid:
        return jsonify({"ok": False, "message": "UID topilmadi"})

    user = users_db.find_one({"_id": uid})
    if not user:
        users_db.insert_one({"_id": uid, "balance": 0})
        user = {"balance": 0, "skidka": False}

    store_info = {
        "card": g_set('card'),
        "admin": g_set('admin'),
        "p_y1": int(g_set('p_y1')),
        "p_y2": int(g_set('p_y2')),
        "p_2func": int(g_set('p_2func')),
        "p_gemini": int(g_set('p_gemini')),
        "stock_y1": accounts_db.count_documents({"type": "y1"}),
        "stock_y2": accounts_db.count_documents({"type": "y2"}),
        "bot_username": bot.get_me().username
    }

    return jsonify({
        "ok": True,
        "user": {
            "balance": int(user.get("balance", 0)),
            "skidka": user.get("skidka", False)
        },
        "store": store_info
    })

@app.route('/api/numbers_prices')
def api_numbers_prices():
    service = request.args.get('service', 'tg')
    prices = get_gz_prices(service)
    gk = g_k("USD", 12850.0)

    out = []
    for cid, cname in C_LIST:
        cost = prices.get(cid)
        if cost:
            mv = get_country_m(cid)
            price_uzs = int(cost * gk * mv)
            out.append({"id": cid, "name": cname, "price": price_uzs})
        else:
            out.append({"id": cid, "name": cname, "price": 0})

    return jsonify({"ok": True, "countries": out})

@app.route('/api/buy_number', methods=['POST'])
def api_buy_number():
    data = request.json
    uid = int(data.get('uid', 0))
    service = data.get('service', 'tg')
    country = data.get('country', '0')
    price = int(data.get('price', 0))

    if g_bal(uid) < price:
        return jsonify({"ok": False, "message": "Balansingiz yetarli emas!"})

    res = req_gz_number(service, country)
    if res["s"]:
        u_bal(uid, -price)
        orders_db.insert_one({
            "user_id": uid,
            "oid": f"NUM_{service.upper()}",
            "link": f"Nomer: {res['n']} (ID: {res['id']})",
            "quantity": 1,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
            "status": "SMS kutilmoqda"
        })
        return jsonify({"ok": True, "number_id": res["id"], "phone": res["n"]})
    else:
        return jsonify({"ok": False, "message": res.get("m", "Nomer olib bo'lmadi")})

@app.route('/api/check_sms')
def api_check_sms():
    nid = request.args.get('id')
    try:
        url = "https://api.grizzlysms.com/stubs/handler_api.php"
        r = requests.get(url, params={"api_key": GRIZZLY_API_KEY, "action": "getStatus", "id": nid}, timeout=10)
        body = r.text.strip()
        if body.startswith("STATUS_OK:") or body.startswith("OK:"):
            sms_code = body.split(':')[1] if ':' in body else body.replace('OK:', '')
            return jsonify({"ok": True, "code": sms_code})
        return jsonify({"ok": True, "code": None, "status": body})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route('/api/cancel_number', methods=['POST'])
def api_cancel_number():
    data = request.json
    uid = int(data.get('uid', 0))
    nid = data.get('id')

    try:
        url = "https://api.grizzlysms.com/stubs/handler_api.php"
        r = requests.get(url, params={"api_key": GRIZZLY_API_KEY, "action": "setStatus", "status": 8, "id": nid}, timeout=10)
        body = r.text.strip()
        # Nomer narxini buyurtmadan topish
        order = orders_db.find_one({"link": {"$regex": str(nid)}})
        refund_amount = 0
        if order:
            orders_db.update_one({"_id": order["_id"]}, {"$set": {"status": "Bekor qilindi"}})

        return jsonify({"ok": True, "message": "Nomer bekor qilindi", "refund_amount": refund_amount})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route('/api/buy_channel', methods=['POST'])
def api_buy_channel():
    data = request.json
    uid = int(data.get('uid', 0))
    t = data.get('type', 'y2')
    price = int(data.get('price', 120000))

    if g_bal(uid) < price:
        return jsonify({"ok": False, "message": "Balansingiz yetarli emas!"})

    u_bal(uid, -price)
    acc = accounts_db.find_one({"type": t})
    if acc:
        accounts_db.delete_one({"_id": acc["_id"]})
        orders_db.insert_one({
            "user_id": uid,
            "oid": f"YouTube ({t})",
            "link": acc['data'],
            "quantity": 1,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
            "status": "Bajarildi ✅"
        })
        try: bot.send_message(uid, f"🎁 <b>YouTube Kanal xaridingiz:</b>\n<code>{acc['data']}</code>", parse_mode='HTML')
        except: pass
        return jsonify({"ok": True, "account_data": acc['data']})
    else:
        r = orders_db.insert_one({
            "user_id": uid,
            "oid": f"YouTube ({t})",
            "link": "Kanal kutilmoqda",
            "quantity": 1,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
            "status": "Kutmoqda"
        })
        adm_msg(
            f"🔔 <b>YANGI YOUTUBE KANAL BUYURTMASI:</b>\n👤 User: <code>{uid}</code>\n📦 Turi: {t}\n💵 Narx: {price:,} so'm",
            rm=IK().add(IB("📤 Kanal yuborish", callback_data=f"snd_{uid}_{str(r.inserted_id)}"))
        )
        return jsonify({"ok": True, "account_data": None})

@app.route('/api/buy_gemini', methods=['POST'])
def api_buy_gemini():
    data = request.json
    uid = int(data.get('uid', 0))
    price = int(data.get('price', 50000))

    if g_bal(uid) < price:
        return jsonify({"ok": False, "message": "Balansingiz yetarli emas!"})

    u_bal(uid, -price)
    r = orders_db.insert_one({
        "user_id": uid,
        "oid": "Gemini Advanced",
        "link": "Obuna silkasi kutilmoqda",
        "quantity": 1,
        "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "status": "Kutmoqda"
    })
    adm_msg(
        f"🔔 <b>YANGI GEMINI OBUNA BUYURTMASI:</b>\n👤 User: <code>{uid}</code>\n💵 Narx: {price:,} so'm",
        rm=IK().add(IB("📤 Silka yuborish", callback_data=f"snd_{uid}_{str(r.inserted_id)}"))
    )
    return jsonify({"ok": True})

@app.route('/api/buy_twofunc', methods=['POST'])
def api_buy_twofunc():
    data = request.json
    uid = int(data.get('uid', 0))
    price = int(data.get('price', 100000))
    info = data.get('info', '')

    if g_bal(uid) < price:
        return jsonify({"ok": False, "message": "Balansingiz yetarli emas!"})

    u_bal(uid, -price)
    r = orders_db.insert_one({
        "user_id": uid,
        "oid": "2-Funksiya Ulanish",
        "link": info,
        "quantity": 1,
        "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
        "status": "Kutmoqda"
    })
    adm_msg(
        f"🔔 <b>YANGI 2-FUNKSIYA BUYURTMASI:</b>\n👤 User: <code>{uid}</code>\n📝 Ma'lumot: {info}",
        rm=IK().add(IB("📤 Natijani yuborish", callback_data=f"snd_{uid}_{str(r.inserted_id)}"))
    )
    return jsonify({"ok": True})

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    uid = int(request.form.get('uid', 0))
    amount = int(request.form.get('amount', 0))
    file = request.files.get('receipt')

    if not uid or amount < 1000 or not file:
        return jsonify({"ok": False, "message": "Ma'lumotlar to'liq emas!"})

    # Rasmni bot orqali adminga uzatish
    file_bytes = file.read()
    r = payments_db.insert_one({
        "user_id": uid,
        "amount": amount,
        "status": "pending_admin",
        "created_at": datetime.now()
    })
    pid = str(r.inserted_id)

    kb = IK(row_width=2).add(
        IB("✅ TASDIQLASH", callback_data=f"pay_ok_{pid}"),
        IB("❌ RAD ETISH", callback_data=f"pay_no_{pid}")
    )
    cap = f"💳 <b>MINI APP ORQALI CHEK:</b>\n👤 User ID: <code>{uid}</code>\n💵 Summa: <b>{amount:,} so'm</b>"

    for aid in g_adms():
        try:
            bot.send_photo(aid, file_bytes, caption=cap, reply_markup=kb, parse_mode="HTML")
        except: pass

    return jsonify({"ok": True})

@app.route('/api/my_orders')
def api_my_orders():
    uid = request.args.get('uid', type=int)
    if not uid:
        return jsonify({"ok": False, "orders": []})

    orders = list(orders_db.find({"user_id": uid}).sort("_id", -1).limit(15))
    res = []
    for o in orders:
        res.append({
            "oid": o.get("oid", "Xizmat"),
            "link": o.get("link", ""),
            "date": o.get("date", ""),
            "status": o.get("status", "Kutmoqda")
        })
    return jsonify({"ok": True, "orders": res})

# Web serverni ishga tushirish
def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    print("🚀 Flask WebApp va Telegram Bot ishga tushdi...")
    try: bot.remove_webhook()
    except: pass
    time.sleep(1)
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Xatolik: {e}")
            time.sleep(4)
