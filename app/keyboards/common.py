from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    ReplyKeyboardBuilder,
)


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="🍔 Menyu"),
        KeyboardButton(text="🛒 Savatim"),
    )

    builder.row(
        KeyboardButton(text="📦 Buyurtmalarim"),
        KeyboardButton(text="👤 Profil"),
    )

    builder.row(
        KeyboardButton(text="📞 Aloqa"),
    )

    if is_admin:
        builder.row(
            KeyboardButton(text="⚙️ Admin panel"),
        )

    return builder.as_markup(
        resize_keyboard=True,
    )


def categories_keyboard(
    categories: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in categories:
        builder.button(
            text=item["name"],
            callback_data=f"cat:{item['id']}",
        )

    builder.adjust(2)

    return builder.as_markup()


def products_keyboard(
    products: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in products:
        builder.button(
            text=(
                f"{item['name']} — "
                f"{item['price']:,.0f} so'm"
            ),
            callback_data=f"prod:{item['id']}",
        )

    builder.button(
        text="⬅️ Kategoriyalar",
        callback_data="menu:categories",
    )

    builder.adjust(1)

    return builder.as_markup()


def product_actions(
    product_id: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Savatga qo‘shish",
        callback_data=f"cart:add:{product_id}",
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data="menu:categories",
    )

    builder.adjust(1)

    return builder.as_markup()


def cart_keyboard(
    cart: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in cart:
        builder.row(
            InlineKeyboardButton(
                text=f"➖ {item['name']}",
                callback_data=(
                    f"cart:dec:{item['product_id']}"
                ),
            ),
            InlineKeyboardButton(
                text=str(item["quantity"]),
                callback_data="cart:no-op",
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=(
                    f"cart:inc:{item['product_id']}"
                ),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=(
                    f"cart:del:{item['product_id']}"
                ),
            ),
        )

    if cart:
        builder.row(
            InlineKeyboardButton(
                text="✅ Buyurtma berish",
                callback_data="checkout:start",
            )
        )

    return builder.as_markup()


def confirm_keyboard(
    prefix: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Saqlash",
                    callback_data=f"{prefix}:save",
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"{prefix}:cancel",
                ),
            ]
        ]
    )


def yes_no_keyboard(
    prefix: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Aktiv",
                    callback_data=f"{prefix}:yes",
                ),
                InlineKeyboardButton(
                    text="❌ Noaktiv",
                    callback_data=f"{prefix}:no",
                ),
            ]
        ]
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(
            text="📱 Telefon raqamni yuborish",
            request_contact=True,
        )
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(
            text="📍 Lokatsiyani yuborish",
            request_location=True,
        )
    )

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💵 Naqd",
                    callback_data="payment:cash",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Online",
                    callback_data="payment:online",
                )
            ],
        ]
    )


def cash_warning_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tushundim, tasdiqlayman",
                    callback_data="cash:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cash:cancel",
                )
            ],
        ]
    )