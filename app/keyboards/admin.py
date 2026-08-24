from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Buyurtmalar",
                    callback_data="admin:orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍔 Menyuni boshqarish",
                    callback_data="admin:menu",
                )
            ],
        ]
    )


def menu_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Kategoriyalar",
                    callback_data="admin:categories",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍔 Mahsulotlar",
                    callback_data="admin:products",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data="admin:home",
                )
            ],
        ]
    )


def category_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Kategoriya qo‘shish",
                    callback_data="catadmin:add",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Kategoriyani o‘zgartirish",
                    callback_data="catadmin:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Kategoriyani o‘chirish",
                    callback_data="catadmin:delete",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Aktiv/noaktiv qilish",
                    callback_data="catadmin:toggle",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔢 Tartibini o‘zgartirish",
                    callback_data="catadmin:sort",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Menyu boshqaruvi",
                    callback_data="admin:menu",
                )
            ],
        ]
    )


def product_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Mahsulot qo‘shish",
                    callback_data="prodadmin:add",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Mahsulotni o‘zgartirish",
                    callback_data="prodadmin:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Mahsulotni o‘chirish",
                    callback_data="prodadmin:delete",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Aktiv/noaktiv qilish",
                    callback_data="prodadmin:toggle",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Narxni o‘zgartirish",
                    callback_data="prodadmin:price",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Rasmni almashtirish",
                    callback_data="prodadmin:image",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Nomini o‘zgartirish",
                    callback_data="prodadmin:name",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Tavsifini o‘zgartirish",
                    callback_data="prodadmin:description",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Kategoriyasini o‘zgartirish",
                    callback_data="prodadmin:category",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔢 Tartibini o‘zgartirish",
                    callback_data="prodadmin:sort",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Menyu boshqaruvi",
                    callback_data="admin:menu",
                )
            ],
        ]
    )


def select_categories(
    categories: list[dict],
    prefix: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in categories:
        status = "✅" if item["is_active"] else "❌"

        builder.button(
            text=f"{item['name']} {status}",
            callback_data=f"{prefix}:{item['id']}",
        )

    builder.adjust(1)

    return builder.as_markup()


def select_products(
    products: list[dict],
    prefix: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in products:
        status = "✅" if item["is_active"] else "❌"

        builder.button(
            text=f"{item['name']} {status}",
            callback_data=f"{prefix}:{item['id']}",
        )

    builder.adjust(1)

    return builder.as_markup()


def order_status_keyboard(
    order_id: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qabul qilish",
                    callback_data=(
                        f"orderstatus:accepted:{order_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🍳 Tayyorlanmoqda",
                    callback_data=(
                        f"orderstatus:preparing:{order_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚚 Yetkazilmoqda",
                    callback_data=(
                        f"orderstatus:delivering:{order_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏁 Yakunlash",
                    callback_data=(
                        f"orderstatus:completed:{order_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=(
                        f"orderstatus:cancelled:{order_id}"
                    ),
                )
            ],
        ]   
    )