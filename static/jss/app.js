// Telegram WebApp integratsiyasi
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.expand();
  tg.enableClosingConfirmation();
}

// Global holat (State)
let currentUser = {
  id: 0,
  first_name: "Foydalanuvchi",
  username: "",
  balance: 0,
  skidka: false
};

let storeData = {
  card: "8600 0000 0000 0000",
  admin: "@SizningUserneyim",
  p_y1: 190000,
  p_y2: 120000,
  p_2func: 100000,
  p_gemini: 50000,
  stock_y1: 0,
  stock_y2: 0,
  bot_username: "prosmmmarket_bot"
};

let selectedNetwork = "tg";
let countriesData = [];
let activeNumberInterval = null;
let activeNumberId = null;

// Boshlang'ich yuklash
document.addEventListener("DOMContentLoaded", () => {
  initTelegramUser();
  loadInitialData();
  setupNetworkChips();
});

function initTelegramUser() {
  if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    const u = tg.initDataUnsafe.user;
    currentUser.id = u.id;
    currentUser.first_name = u.first_name || "Foydalanuvchi";
    currentUser.username = u.username || "";
  } else {
    // Brauzer orqali test qilish uchun demo ID
    currentUser.id = 8467707826;
    currentUser.first_name = "Test User";
  }

  document.getElementById("userName").innerText = currentUser.first_name;
  document.getElementById("userId").innerText = `ID: ${currentUser.id}`;
  document.getElementById("profileName").innerText = currentUser.first_name;
  document.getElementById("profileId").innerText = `ID: ${currentUser.id}`;
}

// Backend API bilan ma'lumotlarni sinxronlash
async function loadInitialData() {
  try {
    const res = await fetch(`/api/user_data?uid=${currentUser.id}`);
    const data = await res.json();
    if (data.ok) {
      currentUser.balance = data.user.balance || 0;
      currentUser.skidka = data.user.skidka || false;
      storeData = Object.assign(storeData, data.store);

      updateBalanceUI();
      updateStorePricesUI();
    }
  } catch (e) {
    console.error("Ma'lumot yuklashda xatolik:", e);
  }
}

function updateBalanceUI() {
  const formatted = `${currentUser.balance.toLocaleString()} so'm`;
  document.getElementById("headerBalance").innerText = formatted;
  document.getElementById("profileBalance").innerText = formatted;

  const botName = storeData.bot_username || "bot";
  const refLink = `https://t.me/${botName}?start=${currentUser.id}`;
  document.getElementById("refLinkInput").value = refLink;
}

function updateStorePricesUI() {
  document.getElementById("cardYtPrice").innerText = `${storeData.p_y2.toLocaleString()} so'm dan`;
  document.getElementById("cardGemPrice").innerText = `${storeData.p_gemini.toLocaleString()} so'm`;
  document.getElementById("cardTwoFuncPrice").innerText = `${storeData.p_2func.toLocaleString()} so'm`;

  document.getElementById("adminCardNumber").innerText = storeData.card;
  document.getElementById("stockY1").innerText = `${storeData.stock_y1} ta qoldi`;
  document.getElementById("stockY2").innerText = `${storeData.stock_y2} ta qoldi`;
  document.getElementById("statChannels").innerText = storeData.stock_y1 + storeData.stock_y2;

  const discountY1 = currentUser.skidka ? (storeData.p_y1 - 15000) : storeData.p_y1;
  const discountY2 = currentUser.skidka ? (storeData.p_y2 - 15000) : storeData.p_y2;

  document.getElementById("priceY1").innerText = `${discountY1.toLocaleString()} so'm`;
  document.getElementById("priceY2").innerText = `${discountY2.toLocaleString()} so'm`;
  document.getElementById("modalGemPrice").innerText = `${storeData.p_gemini.toLocaleString()} so'm`;
  document.getElementById("modalTwoFuncPrice").innerText = `${storeData.p_2func.toLocaleString()} so'm`;
}

// Tablarni almashtirish
function switchTab(tabId) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add("active");

  const navMap = {
    "tab-home": 0,
    "tab-numbers": 1,
    "tab-deposit": 2,
    "tab-orders": 3,
    "tab-profile": 4
  };
  const navItems = document.querySelectorAll(".nav-item");
  if (navMap[tabId] !== undefined && navItems[navMap[tabId]]) {
    navItems[navMap[tabId]].classList.add("active");
  }

  if (tabId === "tab-numbers") {
    loadCountries();
  } else if (tabId === "tab-orders") {
    loadOrders();
  }
}

// Modallar
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add("active");
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove("active");
}

function openNumberModal() { switchTab("tab-numbers"); }
function openChannelsModal() { openModal("modalChannels"); }
function openGeminiModal() { openModal("modalGemini"); }
function openTwoFuncModal() { openModal("modalTwoFunc"); }

// Nomer olish bo'limi
function setupNetworkChips() {
  const chips = document.querySelectorAll(".net-chip");
  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      chips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedNetwork = chip.getAttribute("data-service");
      loadCountries();
    });
  });
}

async function loadCountries() {
  const container = document.getElementById("countryList");
  container.innerHTML = '<div class="loading-spinner">Narxlar hisoblanmoqda...</div>';

  try {
    const res = await fetch(`/api/numbers_prices?service=${selectedNetwork}`);
    const data = await res.json();
    if (data.ok) {
      countriesData = data.countries;
      renderCountries(countriesData);
    } else {
      container.innerHTML = '<div class="loading-spinner">Nomerlar topilmadi</div>';
    }
  } catch (e) {
    container.innerHTML = '<div class="loading-spinner">API ulanishida xatolik</div>';
  }
}

function renderCountries(list) {
  const container = document.getElementById("countryList");
  if (!list || list.length === 0) {
    container.innerHTML = '<div class="loading-spinner">Hozirda bu tarmoqda mavjud nomerlar yo\'q</div>';
    return;
  }

  let html = "";
  list.forEach(c => {
    if (c.price > 0) {
      html += `
        <div class="country-row" onclick="buyNumber('${selectedNetwork}', '${c.id}', ${c.price}, '${c.name}')">
          <span class="country-title">${c.name}</span>
          <span class="country-price">${c.price.toLocaleString()} so'm</span>
        </div>
      `;
    } else {
      html += `
        <div class="country-row" style="opacity: 0.5; cursor: not-allowed;">
          <span class="country-title">${c.name}</span>
          <span class="country-out">Mavjud emas</span>
        </div>
      `;
    }
  });
  container.innerHTML = html;
}

function filterCountries() {
  const q = document.getElementById("countrySearch").value.toLowerCase();
  const filtered = countriesData.filter(c => c.name.toLowerCase().includes(q));
  renderCountries(filtered);
}

// Nomer sotib olish
async function buyNumber(service, countryId, price, countryName) {
  if (currentUser.balance < price) {
    showToast("🔴 Balansingiz yetarli emas! Iltimos, hisobingizni to'ldiring.");
    switchTab("tab-deposit");
    return;
  }

  if (!confirm(`${countryName} uchun ${price.toLocaleString()} so'mga nomer olinsinmi?`)) {
    return;
  }

  showToast("⏳ Nomer so'ralmoqda...");

  try {
    const res = await fetch("/api/buy_number", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        uid: currentUser.id,
        service: service,
        country: countryId,
        price: price
      })
    });
    const data = await res.json();
    if (data.ok) {
      currentUser.balance -= price;
      updateBalanceUI();
      showToast("✅ Nomer muvaffaqiyatli xarid qilindi!");

      showActiveNumber(data.number_id, data.phone, price);
    } else {
      showToast(`❌ ${data.message || "Xatolik yuz berdi"}`);
    }
  } catch (e) {
    showToast("Tarmoq xatosi!");
  }
}

function showActiveNumber(id, phone, price) {
  activeNumberId = id;
  const card = document.getElementById("activeNumberCard");
  card.classList.remove("hidden");
  document.getElementById("ancNumberText").innerText = phone;
  document.getElementById("ancCodeText").innerText = "Kutilmoqda...";

  card.scrollIntoView({ behavior: "smooth" });

  if (activeNumberInterval) clearInterval(activeNumberInterval);
  activeNumberInterval = setInterval(checkSmsCode, 4000);
}

async function checkSmsCode() {
  if (!activeNumberId) return;

  try {
    const res = await fetch(`/api/check_sms?id=${activeNumberId}`);
    const data = await res.json();
    if (data.ok) {
      if (data.code) {
        document.getElementById("ancCodeText").innerText = data.code;
        showToast("🎉 SMS KOD KELDI!");
        if (activeNumberInterval) clearInterval(activeNumberInterval);
      } else {
        document.getElementById("ancCodeText").innerText = "Kutilmoqda...";
      }
    }
  } catch (e) {}
}

async function cancelActiveNumber() {
  if (!activeNumberId) return;
  if (!confirm("Raqamni bekor qilib pulni to'liq qaytarasizmi?")) return;

  try {
    const res = await fetch("/api/cancel_number", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uid: currentUser.id, id: activeNumberId })
    });
    const data = await res.json();
    if (data.ok) {
      showToast("✅ Nomer bekor qilindi, pul qaytarildi!");
      document.getElementById("activeNumberCard").classList.add("hidden");
      if (activeNumberInterval) clearInterval(activeNumberInterval);
      currentUser.balance += data.refund_amount || 0;
      updateBalanceUI();
      activeNumberId = null;
    } else {
      showToast(data.message || "Bekor qilib bo'lmadi");
    }
  } catch (e) {
    showToast("Xatolik yuz berdi");
  }
}

// YouTube Kanal xarid qilish
async function buyChannel(type) {
  closeModal("modalChannels");
  const p = type === "y1" ? storeData.p_y1 : storeData.p_y2;
  const finalPrice = currentUser.skidka ? (p - 15000) : p;

  if (currentUser.balance < finalPrice) {
    showToast("🔴 Balansingiz yetarli emas!");
    switchTab("tab-deposit");
    return;
  }

  if (!confirm(`Kanal xarid qilinsinmi? Narxi: ${finalPrice.toLocaleString()} so'm`)) return;

  showToast("⏳ Rasmiylashtirilmoqda...");
  try {
    const res = await fetch("/api/buy_channel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uid: currentUser.id, type: type, price: finalPrice })
    });
    const data = await res.json();
    if (data.ok) {
      currentUser.balance -= finalPrice;
      updateBalanceUI();
      if (data.account_data) {
        alert(`✅ KANAL LOGINI VA PAROLI:\n\n${data.account_data}`);
      } else {
        alert("✅ Buyurtma qabul qilindi! Admin tez orada bot orqali sizga kanal ma'lumotlarini yuboradi.");
      }
      switchTab("tab-orders");
    } else {
      showToast(data.message || "Xatolik yuz berdi");
    }
  } catch (e) {
    showToast("Server xatosi");
  }
}

// Gemini Obuna sotib olish
async function buyGemini() {
  closeModal("modalGemini");
  const p = storeData.p_gemini;

  if (currentUser.balance < p) {
    showToast("🔴 Balansingiz yetarli emas!");
    switchTab("tab-deposit");
    return;
  }

  if (!confirm(`Gemini Advanced obunasi (${p.toLocaleString()} so'm) xarid qilinsinmi?`)) return;

  showToast("⏳ Buyurtma berilmoqda...");
  try {
    const res = await fetch("/api/buy_gemini", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uid: currentUser.id, price: p })
    });
    const data = await res.json();
    if (data.ok) {
      currentUser.balance -= p;
      updateBalanceUI();
      alert("✅ Buyurtmangiz adminga yuborildi!\n\nTez orada bot orqali akkauntingizga obunani yoqish havolasi (link) keladi.");
      switchTab("tab-orders");
    } else {
      showToast(data.message || "Xatolik yuz berdi");
    }
  } catch (e) {
    showToast("Server xatosi");
  }
}

// 2-Funksiya buyurtma qilish
async function buyTwoFunc() {
  const link = document.getElementById("twoFuncInput").value.trim();
  if (!link) {
    alert("Iltimos, kanal ssilkasi yoki loginini kiriting!");
    return;
  }
  closeModal("modalTwoFunc");

  const p = storeData.p_2func;
  if (currentUser.balance < p) {
    showToast("🔴 Balansingiz yetarli emas!");
    switchTab("tab-deposit");
    return;
  }

  showToast("⏳ Yuborilmoqda...");
  try {
    const res = await fetch("/api/buy_twofunc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uid: currentUser.id, price: p, info: link })
    });
    const data = await res.json();
    if (data.ok) {
      currentUser.balance -= p;
      updateBalanceUI();
      alert("✅ Buyurtma qabul qilindi! Admin ko'rib chiqib xizmatni ulab beradi.");
      switchTab("tab-orders");
    } else {
      showToast(data.message || "Xatolik yuz berdi");
    }
  } catch (e) {
    showToast("Server xatosi");
  }
}

// Hisob to'ldirish (Deposit)
function setDepAmount(val) {
  document.getElementById("depAmountInput").value = val;
}

function copyCard() {
  const card = document.getElementById("adminCardNumber").innerText.replace(/\s+/g, "");
  navigator.clipboard.writeText(card);
  showToast("📋 Karta raqami nusxalandi!");
}

function copyRefLink() {
  const link = document.getElementById("refLinkInput").value;
  navigator.clipboard.writeText(link);
  showToast("📋 Taklif havolasi nusxalandi!");
}

function previewReceipt(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
      document.getElementById("uploadPlaceholder").classList.add("hidden");
      const preview = document.getElementById("uploadPreview");
      preview.classList.remove("hidden");
      document.getElementById("previewImg").src = e.target.result;
      document.getElementById("previewName").innerText = file.name;
    };
    reader.readAsDataURL(file);
  }
}

async function submitDeposit() {
  const amt = parseInt(document.getElementById("depAmountInput").value);
  const fileInput = document.getElementById("receiptFileInput");

  if (!amt || amt < 1000) {
    alert("Minimal to'lov miqdori 1,000 so'm!");
    return;
  }

  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Iltimos, to'lov cheki (screenshot) rasmini yuklang!");
    return;
  }

  const formData = new FormData();
  formData.append("uid", currentUser.id);
  formData.append("amount", amt);
  formData.append("receipt", fileInput.files[0]);

  const btn = document.getElementById("btnSubmitPayment");
  btn.disabled = true;
  btn.innerText = "⏳ Yuborilmoqda...";

  try {
    const res = await fetch("/api/deposit", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.ok) {
      alert("✅ Chek qabul qilindi!\n\nAdmin tekshirib 5-15 daqiqa ichida hisobingizga pul o'tkazadi.");
      document.getElementById("depAmountInput").value = "";
      document.getElementById("uploadPreview").classList.add("hidden");
      document.getElementById("uploadPlaceholder").classList.remove("hidden");
      fileInput.value = "";
      switchTab("tab-orders");
    } else {
      showToast(data.message || "Xatolik yuz berdi");
    }
  } catch (e) {
    showToast("Yuklashda xatolik yuz berdi!");
  } finally {
    btn.disabled = false;
    btn.innerText = "✅ To'lovni Yuborish";
  }
}

// Buyurtmalar tarixi
async function loadOrders() {
  const container = document.getElementById("ordersList");
  container.innerHTML = '<div class="loading-spinner">Yuklanmoqda...</div>';

  try {
    const res = await fetch(`/api/my_orders?uid=${currentUser.id}`);
    const data = await res.json();
    if (data.ok && data.orders && data.orders.length > 0) {
      let html = "";
      data.orders.forEach(o => {
        let statusBadge = `<span style="color:#f59e0b">⏳ ${o.status}</span>`;
        if (o.status && o.status.includes("Bajarildi")) {
          statusBadge = `<span style="color:#10b981">✅ Bajarildi</span>`;
        }
        html += `
          <div class="order-card">
            <div class="order-top">
              <span class="order-title">📦 ${o.oid || "Xizmat"}</span>
              <span class="order-date">${o.date || ""}</span>
            </div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
              ${o.link || ""}
            </div>
            <div style="font-size: 11px; display: flex; justify-content: space-between;">
              <span>Holat: ${statusBadge}</span>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
    } else {
      container.innerHTML = '<div class="loading-spinner">Hozircha buyurtmalar yo\'q</div>';
    }
  } catch (e) {
    container.innerHTML = '<div class="loading-spinner">Yuklab bo\'lmadi</div>';
  }
}

function openSupport() {
  const admin = storeData.admin.replace("@", "");
  if (tg) {
    tg.openTelegramLink(`https://t.me/${admin}`);
  } else {
    window.open(`https://t.me/${admin}`, "_blank");
  }
}

// Toast xabarnomasi
function showToast(msg) {
  const t = document.getElementById("toast");
  t.innerText = msg;
  t.classList.add("show");
  setTimeout(() => {
    t.classList.remove("show");
  }, 3000);
}
