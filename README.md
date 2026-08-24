# Oazis Fast Food Telegram Bot

Oazis Fast Food uchun Python 3.12, aiogram 3.x va Supabase asosidagi ordering bot. Menyu maʼlumotlari kodga hardcode qilinmaydi: kategoriyalar va mahsulotlar har bir so‘rovda Supabase'dan olinadi. Admin orqali kiritilgan o‘zgarishlar keyingi bot menyu so‘rovlarida darhol ko‘rinadi.

## Imkoniyatlar

Foydalanuvchi `🍔 Menyu` orqali aktiv kategoriyalar va mahsulotlarni ko‘radi, mahsulotni savatga qo‘shadi, miqdorni boshqaradi va checkout jarayonida telefon, manzil, izoh hamda to‘lov turini kiritadi. Tasdiqlangan buyurtma `orders` va `order_items` jadvallariga yoziladi hamda adminlarga Telegram xabari yuboriladi.

`⚙️ Admin panel` faqat `.env` dagi `ADMIN_IDS` qiymatlariga kirgan Telegram ID lar uchun ko‘rinadi. U buyurtma statuslarini boshqarishdan tashqari kategoriyalar va mahsulotlar uchun qo‘shish, o‘zgartirish, o‘chirish, aktiv/noaktiv qilish va tartibni boshqarishni taʼminlaydi. Mahsulot qo‘shish ketma-ketligi kategoriya → nom → tavsif → narx → rasm → aktiv/noaktiv ko‘rinishida ishlaydi. Saqlash yoki bekor qilish inline tasdiqlashlari mavjud.

## O‘rnatish

```bash
cp .env.example .env
# .env ichiga BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY va ADMIN_IDS ni kiriting
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Supabase SQL editorida `migrations/001_initial.sql` faylining to‘liq mazmunini bir marta ishga tushiring. Server-side Supabase keyni faqat `.env` da saqlang; uni GitHub yoki frontendga joylamang.

## Ishga tushirish

```bash
source .venv/bin/activate
python -m app.main
```

Docker orqali:

```bash
docker build -t oazis-fastfood-bot .
docker run --env-file .env --restart unless-stopped oazis-fastfood-bot
```

## Tekshiruv

Statik import va syntax tekshiruvi:

```bash
python -m compileall app tests
```

Haqiqiy Telegram va Supabase flow testi uchun `.env` to‘ldirilgan bo‘lishi, migration bajarilgan bo‘lishi va bot token valid bo‘lishi kerak. Test ssenariysi: `/start` → `🍔 Menyu` → kategoriya → mahsulot → `➕ Savatga qo‘shish` → `🛒 Savatim` → `✅ Buyurtma berish` → maʼlumotlar → tasdiqlash. Keyin admin paneldan kategoriya va mahsulot qo‘shib, mahsulotni noaktiv qiling va foydalanuvchi menyusini qayta oching.

## Tuzilma

```text
oazis-fastfood-bot/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database/
│   │   ├── client.py
│   │   └── repository.py
│   ├── handlers/
│   │   ├── user.py
│   │   └── admin.py
│   ├── keyboards/
│   │   ├── common.py
│   │   └── admin.py
│   ├── states/flows.py
│   └── utils/formatting.py
├── migrations/001_initial.sql
├── tests/test_logic.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```
