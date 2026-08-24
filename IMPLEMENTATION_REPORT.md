# Oazis Fast Food bot — implementatsiya hisoboti

## Natija

Oazis Fast Food Telegram ordering boti noldan yaratildi. U Python 3.12, aiogram 3.x, Supabase va python-dotenv asosida tuzilgan. Menyu maʼlumotlari kod ichida hardcode qilinmagan: foydalanuvchi menyusi har safar `categories` va `products` jadvallaridan olinadi. Admin paneldagi kategoriya yoki mahsulot o‘zgarishlari Supabase'ga yoziladi va keyingi menyu so‘rovlarida ko‘rinadi.

## Yaratilgan fayllar

| Fayl | Vazifasi |
|---|---|
| `app/main.py` | Bot startup, polling, routerlar va graceful shutdown |
| `app/config.py` | `.env` konfiguratsiyasi va `ADMIN_IDS` validatsiyasi |
| `app/database/client.py` | Supabase client yaratish |
| `app/database/repository.py` | Kategoriya, mahsulot, mijoz va buyurtma CRUD/data access |
| `app/handlers/user.py` | Menyu, mahsulot, savat, checkout, profil va buyurtmalar |
| `app/handlers/admin.py` | Admin buyurtmalari, kategoriya va mahsulot boshqaruvi |
| `app/keyboards/common.py` | Foydalanuvchi inline/reply klaviaturalari |
| `app/keyboards/admin.py` | Admin panel klaviaturalari |
| `app/states/flows.py` | Checkout va admin FSM holatlari |
| `app/utils/formatting.py` | Narx, savat va buyurtma formatlash |
| `migrations/001_initial.sql` | Barcha Supabase jadvallari, indexlar, triggerlar va RLS yoqilishi |
| `.env.example` | Secretlar uchun namuna konfiguratsiya |
| `Dockerfile` | Production container image |
| `tests/test_logic.py` | Narx va savat hisoblash testlari |
| `tests/test_routers.py` | Router startup smoke-testi |
| `README.md` | O‘rnatish, migration va ishga tushirish yo‘riqnomasi |

## Supabase modeli

Migration quyidagi jadvallarni yaratadi: `categories`, `products`, `customers`, `orders` va `order_items`. Buyurtma statuslari `new`, `accepted`, `preparing`, `delivering`, `completed`, `cancelled` qiymatlari bilan cheklanadi. Mahsulot buyurtmaga qo‘shilganda mahsulot nomi va narxi `order_items` ichida snapshot sifatida ham saqlanadi.

Server-side Supabase key faqat `.env` orqali olinadi. Jadvallarda RLS yoqilgan; bot server-side key bilan ishlaydi. Frontend to‘g‘ridan-to‘g‘ri Supabase'ga ulanadigan bo‘lsa, service keyni frontendga bermasdan, alohida anon-key policy yoki backend API qatlamidan foydalanish kerak.

## Admin oqimi

`ADMIN_IDS` ichidagi Telegram ID lar uchun `⚙️ Admin panel` tugmasi chiqadi. `🍔 Menyuni boshqarish` bo‘limida kategoriyalar va mahsulotlar alohida boshqariladi. Qo‘shish, muhim o‘zgartirish va o‘chirish ishlari `✅ Saqlash` hamda `❌ Bekor qilish` tasdiqlashlari bilan bajariladi. Mahsulot qo‘shish ketma-ketligi kategoriya → nom → tavsif → narx → rasm → aktiv/noaktiv tarzida yozilgan.

## Test natijalari

| Tekshiruv | Natija |
|---|---:|
| Python `compileall` | Muvaffaqiyatli |
| Unit va router smoke-testlari | **4 passed** |
| Aiogram/Supabase modul importlari | Muvaffaqiyatli |
| Haqiqiy Telegram API end-to-end | Bajarilmadi: `BOT_TOKEN` berilmagan |
| Haqiqiy Supabase API end-to-end | Bajarilmadi: Supabase URL/key berilmagan |

Live testni bajarish uchun `.env` ni to‘ldirish, Supabase SQL migrationni ishga tushirish va botni ishga tushirish kerak. README ichida aniq komandalar berilgan.

## Muhim ishga tushirish komandasi

```bash
cd oazis-fastfood-bot
cp .env.example .env
# .env ni to‘ldiring
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Cheklov va keyingi qadam

Berilgan spetsifikatsiyada frontend sayt uchun alohida stack, sahifalar yoki mavjud repo ko‘rsatilmagan. Shu sababli ushbu deliverable to‘liq Telegram bot va Supabase backend/migrationga qaratildi. Bot uchun yozilgan repository qatlamidan frontend API yoki alohida web frontend keyingi bosqichda foydalanishi mumkin; menyuning yagona manbai Supabase bo‘lib qoladi.
