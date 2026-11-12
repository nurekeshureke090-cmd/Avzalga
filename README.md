# 🚀 Digital Market — Telegram Mini App & Bot

Nakrutka (SMM) qismi to'liq olib tashlanib, qolgan barcha xizmatlar **zamonaviy va chiroyli Telegram Mini App (Web App)** interfeysiga joylashtirildi.

---

## 📁 Loyiha Strukturasi:
Loyiha `c:\Users\User\Downloads\smm_webapp\` papkasida tayyorlandi:

```
smm_webapp/
├── app.py                # Asosiy Telegram Bot + Flask WebApp API backend
├── templates/
│   └── index.html        # Zamonaviy Telegram WebApp interfeysi
└── static/
    ├── css/
    │   └── style.css     # Premium Dark UI dizayn, animatsiyalar
    └── js/
        └── app.js        # WebApp frontend mantig'i, API integratsiya
```

---

## ✨ Mini App Imkoniyatlari & Dizayni:

1. **🏪 Asosiy Vitrina (Do'kon):**
   - Chiroyli statistika va gradientli kartalar
   - Virtual nomerlar (20+ davlatlar)
   - Tayyor YouTube kanallar (2006-2009 va 2010-2019)
   - Gemini Advanced AI obunasi
   - YouTube 2-funksiya ulanish xizmati

2. **📱 Virtual Nomerlar (To'liq interaktiv):**
   - Tarmoqni tanlash (Telegram, WhatsApp, Google, Instagram, TikTok, VK)
   - Davlatlar ro'yxati, real vaqtdagi narxlar va qidiruv tizimi
   - Nomer sotib olingach, sahifaning o'zida SMS kodni avtomat kutish va bekor qilish taymeri

3. **💳 Hisob To'ldirish (Deposit):**
   - Karta raqamini bitta bosishda nusxalash
   - Summani kiritish (tezkor 10k, 30k, 50k, 100k tugmalari)
   - To'lov cheki (screenshot) rasmini to'g'ridan-to'g'ri Web App orqali yuklash (adminga tasdiqlash uchun boradi)

4. **📦 Buyurtmalar Tarixi:**
   - Barcha berilgan buyurtmalar holati (Kutmoqda, Bajarildi) va sanasi

5. **👤 Shaxsiy Kabinet (Profil):**
   - Foydalanuvchi balansi va ID raqami
   - 5% Referal tizimi havolasi
   - Qo'llab-quvvatlash va admin bilan bog'lanish

---

## 🛠 Ishga tushirish:

1. **Talab qilinadigan kutubxonalar:**
   ```bash
   pip install pyTelegramBotAPI flask pymongo dnspython requests
   ```

2. **Ishga tushirish:**
   ```bash
   python c:\Users\User\Downloads\smm_webapp\app.py
   ```

3. **Telegram Mini App havolasi (Domain/Ngrok):**
   - Agar lokalda (kompyuterda) sinamoqchi bo'lsangiz:
     `ngrok http 8080` qilib olingan HTTPS manzilni `app.py` ichidagi `WEBAPP_URL` o'zgaruvchisiga qo'yasiz.
   - Botdagi **"🚀 Do'konni ochish (Mini App)"** tugmasi orqali to'g'ridan-to'g'ri ochiladi!
