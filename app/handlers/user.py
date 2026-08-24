from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

from app.config import Settings
from app.database.repository import Repository
from app.keyboards.admin import order_status_keyboard
from app.keyboards.common import (
    categories_keyboard,
    cart_keyboard,
    cash_warning_keyboard,
    confirm_keyboard,
    location_keyboard,
    main_menu,
    payment_keyboard,
    phone_keyboard,
    product_actions,
    products_keyboard,
)
from app.states.flows import CheckoutStates
from app.utils.formatting import (
    cart_total,
    money,
    order_text,
    product_text,
)


def create_user_router(
    repo: Repository,
    settings: Settings,
) -> Router:
    router = Router(name="user")

    checkout_locks: set[int] = set()

    async def show_categories(
        target: Message | CallbackQuery,
    ) -> None:
        categories = await repo.list_categories(
            active_only=True,
        )

        text = (
            "🍔 <b>Menyu</b>\n\n"
            "Kategoriyani tanlang:"
            if categories
            else "🍔 Hozircha menyu bo‘sh."
        )

        markup = (
            categories_keyboard(categories)
            if categories
            else None
        )

        if isinstance(target, CallbackQuery):
            await target.message.edit_text(
                text,
                reply_markup=markup,
            )
        else:
            await target.answer(
                text,
                reply_markup=markup,
            )

    # ============================================================
    # START
    # ============================================================

    @router.message(CommandStart())
    async def start(
        message: Message,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await repo.upsert_customer(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
        )

        await message.answer(
            "🍔 <b>Oazis Fast Food</b> botiga xush kelibsiz!",
            reply_markup=main_menu(
                message.from_user.id
                in settings.admin_ids
            ),
        )

    # ============================================================
    # MENU
    # ============================================================

    @router.message(F.text == "🍔 Menyu")
    async def menu(
        message: Message,
    ) -> None:
        await show_categories(message)

    @router.callback_query(F.data == "menu:categories")
    async def categories_callback(
        callback: CallbackQuery,
    ) -> None:
        await callback.answer()
        await show_categories(callback)

    @router.callback_query(F.data.startswith("cat:"))
    async def category_products(
        callback: CallbackQuery,
    ) -> None:
        category_id = callback.data.split(
            ":",
            1,
        )[1]

        category = await repo.get_category(
            category_id,
        )

        products = await repo.list_products(
            category_id=category_id,
            active_only=True,
        )

        if not products:
            await callback.answer(
                "Bu kategoriyada hozircha mahsulot yo‘q.",
                show_alert=True,
            )
            return

        category_name = (
            category["name"]
            if category
            else "Mahsulotlar"
        )

        await callback.message.edit_text(
            (
                f"📂 <b>{category_name}</b>\n\n"
                "Mahsulotni tanlang:"
            ),
            reply_markup=products_keyboard(
                products,
            ),
        )

        await callback.answer()

    @router.callback_query(F.data.startswith("prod:"))
    async def product_detail(
        callback: CallbackQuery,
    ) -> None:
        product = await repo.get_product(
            callback.data.split(
                ":",
                1,
            )[1],
        )

        if (
            not product
            or not product.get("is_active")
        ):
            await callback.answer(
                "Mahsulot mavjud emas yoki noaktiv.",
                show_alert=True,
            )
            return

        text = product_text(product)

        if product.get("image_file_id"):
            await callback.message.answer_photo(
                product["image_file_id"],
                caption=text,
                reply_markup=product_actions(
                    product["id"],
                ),
            )
        else:
            await callback.message.answer(
                text,
                reply_markup=product_actions(
                    product["id"],
                ),
            )

        await callback.answer()

    # ============================================================
    # CART
    # ============================================================

    async def get_cart(
        state: FSMContext,
    ) -> list[dict]:
        data = await state.get_data()
        return data.get("cart", [])

    async def save_cart(
        state: FSMContext,
        cart: list[dict],
    ) -> None:
        await state.update_data(
            cart=cart,
        )

    @router.callback_query(F.data.startswith("cart:add:"))
    async def add_to_cart(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        product_id = callback.data.split(
            ":",
            2,
        )[2]

        product = await repo.get_product(
            product_id,
        )

        if (
            not product
            or not product.get("is_active")
        ):
            await callback.answer(
                "Mahsulot mavjud emas.",
                show_alert=True,
            )
            return

        cart = await get_cart(state)

        existing = next(
            (
                item
                for item in cart
                if item["product_id"] == product_id
            ),
            None,
        )

        if existing:
            existing["quantity"] += 1
        else:
            cart.append(
                {
                    "product_id": product_id,
                    "name": product["name"],
                    "price": str(product["price"]),
                    "quantity": 1,
                }
            )

        await save_cart(
            state,
            cart,
        )

        await callback.answer(
            "Savatga qo‘shildi ✅",
        )

    @router.callback_query(F.data.startswith("cart:inc:"))
    async def increment_cart(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        product_id = callback.data.split(
            ":",
            2,
        )[2]

        cart = await get_cart(state)

        for item in cart:
            if item["product_id"] == product_id:
                item["quantity"] += 1
                break

        await save_cart(
            state,
            cart,
        )

        await render_cart(
            callback,
            cart,
        )

    @router.callback_query(F.data.startswith("cart:dec:"))
    async def decrement_cart(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        product_id = callback.data.split(
            ":",
            2,
        )[2]

        cart = await get_cart(state)

        for item in cart:
            if item["product_id"] == product_id:
                item["quantity"] -= 1
                break

        cart = [
            item
            for item in cart
            if item["quantity"] > 0
        ]

        await save_cart(
            state,
            cart,
        )

        await render_cart(
            callback,
            cart,
        )

    @router.callback_query(F.data.startswith("cart:del:"))
    async def delete_cart_item(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        product_id = callback.data.split(
            ":",
            2,
        )[2]

        cart = [
            item
            for item in await get_cart(state)
            if item["product_id"] != product_id
        ]

        await save_cart(
            state,
            cart,
        )

        await render_cart(
            callback,
            cart,
        )

    @router.callback_query(F.data == "cart:no-op")
    async def cart_no_op(
        callback: CallbackQuery,
    ) -> None:
        await callback.answer()

    async def render_cart(
        callback: CallbackQuery,
        cart: list[dict],
    ) -> None:
        if not cart:
            await callback.message.edit_text(
                "🛒 Savatingiz bo‘sh.",
            )
        else:
            lines = [
                "🛒 <b>Savatim</b>",
                *[
                    (
                        f"• {item['name']} × "
                        f"{item['quantity']} — "
                        f"{money(Decimal(str(item['price'])) * item['quantity'])}"
                    )
                    for item in cart
                ],
                "",
                (
                    f"Jami: "
                    f"<b>{money(cart_total(cart))}</b>"
                ),
            ]

            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=cart_keyboard(cart),
            )

        await callback.answer()

    @router.message(F.text == "🛒 Savatim")
    async def cart_message(
        message: Message,
        state: FSMContext,
    ) -> None:
        cart = await get_cart(state)

        if not cart:
            await message.answer(
                "🛒 Savatingiz bo‘sh.",
            )
            return

        lines = [
            "🛒 <b>Savatim</b>",
            *[
                (
                    f"• {item['name']} × "
                    f"{item['quantity']} — "
                    f"{money(Decimal(str(item['price'])) * item['quantity'])}"
                )
                for item in cart
            ],
            "",
            (
                f"Jami: "
                f"<b>{money(cart_total(cart))}</b>"
            ),
        ]

        await message.answer(
            "\n".join(lines),
            reply_markup=cart_keyboard(cart),
        )

    # ============================================================
    # CHECKOUT START
    # ============================================================

    @router.callback_query(F.data == "checkout:start")
    async def checkout_start(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not await get_cart(state):
            await callback.answer(
                "Savat bo‘sh.",
                show_alert=True,
            )
            return

        user_id = callback.from_user.id

        if user_id in checkout_locks:
            await callback.answer(
                "Sizda buyurtma jarayoni allaqachon boshlangan.",
                show_alert=True,
            )
            return

        await state.set_state(
            CheckoutStates.name,
        )

        await callback.message.answer(
            "👤 <b>Ismingizni kiriting:</b>",
        )

        await callback.answer()

    # ============================================================
    # NAME
    # ============================================================

    @router.message(CheckoutStates.name)
    async def checkout_name(
        message: Message,
        state: FSMContext,
    ) -> None:
        name = (message.text or "").strip()

        if not name:
            await message.answer(
                "👤 Iltimos, ismingizni kiriting.",
            )
            return

        await state.update_data(
            customer_name=name,
        )

        await state.set_state(
            CheckoutStates.phone,
        )

        await message.answer(
            (
                "📞 <b>Telefon raqamingizni yuboring:</b>\n\n"
                "Pastdagi tugmani bosing."
            ),
            reply_markup=phone_keyboard(),
        )

    # ============================================================
    # PHONE
    # ============================================================

    @router.message(CheckoutStates.phone)
    async def checkout_phone(
        message: Message,
        state: FSMContext,
    ) -> None:
        phone: str | None = None

        if message.contact:
            phone = message.contact.phone_number

        elif message.text:
            text = message.text.strip()

            if text and text != "📱 Telefon raqamni yuborish":
                phone = text

        if not phone:
            await message.answer(
                (
                    "📞 Telefon raqamingizni "
                    "pastdagi tugma orqali yuboring."
                ),
            )
            return

        await state.update_data(
            phone=phone,
        )

        await state.set_state(
            CheckoutStates.location,
        )

        await message.answer(
            (
                "📍 <b>Yetkazib berish lokatsiyasini yuboring:</b>\n\n"
                "Pastdagi tugmani bosing. "
                "Telegram lokatsiyangizni olamiz."
            ),
            reply_markup=location_keyboard(),
        )

    # ============================================================
    # LOCATION
    # ============================================================

    @router.message(
        CheckoutStates.location,
        F.location,
    )
    async def checkout_location(
        message: Message,
        state: FSMContext,
    ) -> None:
        location = message.location

        if location is None:
            await message.answer(
                "📍 Lokatsiya olinmadi.",
            )
            return

        latitude = float(
            location.latitude,
        )
        longitude = float(
            location.longitude,
        )

        await state.update_data(
            latitude=latitude,
            longitude=longitude,
        )

        await state.set_state(
            CheckoutStates.comment,
        )

        await message.answer(
            (
                "✅ <b>Lokatsiya qabul qilindi.</b>\n\n"
                "📝 Buyurtmaga izoh yozing yoki "
                "<code>-</code> yuboring:"
            ),
            reply_markup=ReplyKeyboardRemove(),
        )

    @router.message(CheckoutStates.location)
    async def checkout_location_invalid(
        message: Message,
    ) -> None:
        await message.answer(
            (
                "📍 Iltimos, lokatsiyani aynan "
                "«📍 Lokatsiyani yuborish» tugmasi orqali yuboring."
            ),
            reply_markup=location_keyboard(),
        )

    # ============================================================
    # COMMENT
    # ============================================================

    @router.message(CheckoutStates.comment)
    async def checkout_comment(
        message: Message,
        state: FSMContext,
    ) -> None:
        text = (message.text or "").strip()

        await state.update_data(
            comment=None if text == "-" else text,
        )

        await state.set_state(
            CheckoutStates.payment_method,
        )

        await message.answer(
            "💳 <b>To‘lov turini tanlang:</b>",
            reply_markup=payment_keyboard(),
        )

    # ============================================================
    # CASH
    # ============================================================

    @router.callback_query(
        CheckoutStates.payment_method,
        F.data == "payment:cash",
    )
    async def checkout_cash(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.set_state(
            CheckoutStates.cash_confirmation,
        )

        await callback.message.answer(
            (
                "⚠️ <b>Naqd to‘lov</b>\n\n"
                "Buyurtma yetkazib berilganda, "
                "to‘lovni yetkazib beruvchiga naqd "
                "pul ko‘rinishida amalga oshirasiz.\n\n"
                "Buyurtmani qabul qilib olganingizda "
                "to‘lovni amalga oshirishingiz kerak."
            ),
            reply_markup=cash_warning_keyboard(),
        )

        await callback.answer()

    @router.callback_query(
        CheckoutStates.cash_confirmation,
        F.data == "cash:confirm",
    )
    async def cash_confirm(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await prepare_payment_confirmation(
            callback,
            state,
            "cash",
        )

    @router.callback_query(
        CheckoutStates.cash_confirmation,
        F.data == "cash:cancel",
    )
    async def cash_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.set_state(
            CheckoutStates.payment_method,
        )

        await callback.message.answer(
            "💳 <b>To‘lov turini tanlang:</b>",
            reply_markup=payment_keyboard(),
        )

        await callback.answer(
            "Naqd to‘lov bekor qilindi.",
        )

    # ============================================================
    # ONLINE - VAQTINCHA O‘CHIRILGAN
    # ============================================================

    @router.callback_query(
        CheckoutStates.payment_method,
        F.data == "payment:online",
    )
    async def checkout_online(
        callback: CallbackQuery,
    ) -> None:
        await callback.answer(
            "🌐 Online to‘lov vaqtincha ishlamayapti.",
            show_alert=True,
        )

        await callback.message.answer(
            (
                "🌐 <b>Online to‘lov</b>\n\n"
                "⚠️ Hozircha online to‘lov xizmati "
                "vaqtincha ishlamayapti.\n\n"
                "Tez orada ishga tushiriladi.\n\n"
                "💵 Hozircha <b>Naqd</b> to‘lovni "
                "tanlashingiz mumkin."
            ),
            reply_markup=payment_keyboard(),
        )

    # ============================================================
    # PAYMENT CONFIRMATION
    # ============================================================

    async def prepare_payment_confirmation(
        callback: CallbackQuery,
        state: FSMContext,
        payment: str,
    ) -> None:
        if payment != "cash":
            await callback.answer(
                "Noto‘g‘ri to‘lov turi.",
                show_alert=True,
            )
            return

        await state.update_data(
            payment_method=payment,
        )

        data = await state.get_data()

        cart = data.get(
            "cart",
            [],
        )

        if not cart:
            await state.clear()

            await callback.answer(
                "Savat bo‘sh.",
                show_alert=True,
            )
            return

        latitude = data.get(
            "latitude",
        )

        longitude = data.get(
            "longitude",
        )

        summary_lines = [
            "✅ <b>Buyurtmani tasdiqlang</b>",
            "",
            (
                f"👤 Ism: "
                f"{data.get('customer_name', '—')}"
            ),
            (
                f"📞 Telefon: "
                f"{data.get('phone', '—')}"
            ),
            (
                f"📍 Lokatsiya: "
                f"{latitude}, {longitude}"
            ),
            "💳 To‘lov: 💵 Naqd",
            (
                f"💰 Jami: "
                f"{money(cart_total(cart))}"
            ),
        ]

        if data.get("comment"):
            summary_lines.append(
                f"📝 Izoh: {data['comment']}"
            )

        await state.set_state(
            CheckoutStates.confirmation,
        )

        await callback.message.answer(
            "\n".join(summary_lines),
            reply_markup=confirm_keyboard(
                "checkout",
            ),
        )

        await callback.answer()

    # ============================================================
    # FINAL CANCEL
    # ============================================================

    @router.callback_query(
        CheckoutStates.confirmation,
        F.data == "checkout:cancel",
    )
    async def checkout_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        checkout_locks.discard(
            callback.from_user.id,
        )

        await state.clear()

        await callback.message.answer(
            "❌ <b>Buyurtma bekor qilindi.</b>",
            reply_markup=main_menu(
                callback.from_user.id
                in settings.admin_ids
            ),
        )

        await callback.answer()

    # ============================================================
    # SAVE ORDER
    # ============================================================

    @router.callback_query(
        CheckoutStates.confirmation,
        F.data == "checkout:save",
    )
    async def checkout_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        user_id = callback.from_user.id

        if user_id in checkout_locks:
            await callback.answer(
                "✅ Buyurtmangiz allaqachon qabul qilinmoqda.",
                show_alert=True,
            )
            return

        checkout_locks.add(
            user_id,
        )

        try:
            data = await state.get_data()

            cart = data.get(
                "cart",
                [],
            )

            if not cart:
                await state.clear()

                await callback.answer(
                    "Savat bo‘sh.",
                    show_alert=True,
                )
                return

            latitude = data.get(
                "latitude",
            )

            longitude = data.get(
                "longitude",
            )

            if (
                latitude is None
                or longitude is None
            ):
                await callback.answer(
                    (
                        "📍 Lokatsiya olinmagan. "
                        "Buyurtmani qayta boshlang."
                    ),
                    show_alert=True,
                )
                return

            payment_method = data.get(
                "payment_method",
            )

            if payment_method != "cash":
                await callback.answer(
                    "❌ Hozircha faqat Naqd to‘lov ishlaydi.",
                    show_alert=True,
                )
                return

            customer = await repo.upsert_customer(
                user_id,
                callback.from_user.username,
                data.get(
                    "customer_name",
                )
                or callback.from_user.first_name,
                phone=data["phone"],
                address=(
                    f"LAT: {latitude}, "
                    f"LON: {longitude}"
                ),
            )

            order = await repo.create_order(
                customer["id"],
                cart,
                cart_total(cart),
                payment_method,
                (
                    f"LAT: {latitude}, "
                    f"LON: {longitude}"
                ),
                data.get("comment"),
                latitude=latitude,
                longitude=longitude,
            )

            order_data = {
                **order,
                "customer_name": data.get(
                    "customer_name",
                ),
                "phone": data.get(
                    "phone",
                ),
                "latitude": latitude,
                "longitude": longitude,
                "order_items": cart,
            }

            text = order_text(
                order_data,
            )

            await state.clear()

            # ----------------------------------------------------
            # MIJOZGA TASDIQ
            # ----------------------------------------------------

            try:
                await callback.message.edit_text(
                    (
                        "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
                        f"{text}"
                    ),
                )
            except Exception:
                await callback.message.answer(
                    (
                        "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
                        f"{text}"
                    ),
                )

            await callback.message.answer(
                "Asosiy menyu:",
                reply_markup=main_menu(
                    user_id
                    in settings.admin_ids
                ),
            )

            await callback.answer(
                "Buyurtma qabul qilindi ✅",
            )

            # ----------------------------------------------------
            # ADMINGA BUYURTMA + STATUS TUGMALARI
            # ----------------------------------------------------

            admin_markup = order_status_keyboard(
                order["id"],
            )

            for admin_id in settings.admin_ids:
                try:
                    # 1. Avval buyurtma ma'lumoti.
                    await callback.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            "🔔 <b>YANGI BUYURTMA!</b>\n\n"
                            f"{text}"
                        ),
                        reply_markup=admin_markup,
                    )

                    # 2. Keyin mijozning haqiqiy Telegram
                    #    lokatsiyasi alohida yuboriladi.
                    await callback.bot.send_location(
                        chat_id=admin_id,
                        latitude=latitude,
                        longitude=longitude,
                    )

                except Exception:
                    pass

        except Exception:
            await callback.answer(
                (
                    "❌ Buyurtma yaratishda xatolik yuz berdi. "
                    "Qayta urinib ko‘ring."
                ),
                show_alert=True,
            )

        finally:
            checkout_locks.discard(
                user_id,
            )

    # ============================================================
    # MY ORDERS
    # ============================================================

    @router.message(F.text == "📦 Buyurtmalarim")
    async def my_orders(
        message: Message,
    ) -> None:
        orders = await repo.get_customer_orders(
            message.from_user.id,
        )

        if not orders:
            await message.answer(
                "Sizda hali buyurtmalar yo‘q.",
            )
            return

        await message.answer(
            "\n\n".join(
                order_text(order)
                for order in orders
            ),
        )

    # ============================================================
    # PROFILE
    # ============================================================

    @router.message(F.text == "👤 Profil")
    async def profile(
        message: Message,
    ) -> None:
        customer = await repo.get_customer(
            message.from_user.id,
        )

        if not customer:
            await message.answer(
                (
                    "Profil maʼlumotlari topilmadi. "
                    "/start ni bosing."
                ),
            )
            return

        await message.answer(
            "\n".join(
                [
                    "👤 <b>Profil</b>",
                    (
                        f"Ism: "
                        f"{customer.get('first_name') or '—'}"
                    ),
                    (
                        f"Telefon: "
                        f"{customer.get('phone') or '—'}"
                    ),
                    (
                        f"Manzil: "
                        f"{customer.get('address') or '—'}"
                    ),
                ],
            ),
        )

    # ============================================================
    # CONTACT
    # ============================================================

    @router.message(F.text == "📞 Aloqa")
    async def contact(
        message: Message,
    ) -> None:
        await message.answer(
            f"📞 {settings.restaurant_phone}\n"
            f"📍 {settings.restaurant_address}",
        )

    return router