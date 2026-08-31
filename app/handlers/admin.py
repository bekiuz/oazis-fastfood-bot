from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.database.repository import Repository
from app.keyboards.admin import (
    admin_panel_keyboard,
    category_admin_keyboard,
    menu_admin_keyboard,
    order_status_keyboard,
    product_admin_keyboard,
    select_categories,
    select_products,
)
from app.keyboards.common import (
    confirm_keyboard,
    yes_no_keyboard,
)
from app.states.flows import CategoryStates, ProductStates
from app.utils.formatting import money, order_text


def create_admin_router(
    repo: Repository,
    settings: Settings,
) -> Router:
    router = Router(name="admin")

    # ============================================================
    # ADMIN ACCESS
    # ============================================================

    def allowed(user_id: int) -> bool:
        return user_id in settings.admin_ids

    async def deny(callback: CallbackQuery) -> None:
        await callback.answer(
            "Bu bo‘lim faqat adminlar uchun.",
            show_alert=True,
        )

    # ============================================================
    # ADMIN PANEL
    # ============================================================

    @router.message(F.text == "⚙️ Admin panel")
    async def admin_panel(message: Message) -> None:
        if not allowed(message.from_user.id):
            return

        await message.answer(
            "⚙️ <b>Admin panel</b>",
            reply_markup=admin_panel_keyboard(),
        )

    @router.callback_query(F.data == "admin:home")
    async def admin_home(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        await callback.message.edit_text(
            "⚙️ <b>Admin panel</b>",
            reply_markup=admin_panel_keyboard(),
        )
        await callback.answer()

    # ============================================================
    # MENU ADMIN
    # ============================================================

    @router.callback_query(F.data == "admin:menu")
    async def admin_menu(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        await callback.message.edit_text(
            "🍔 <b>Menyuni boshqarish</b>",
            reply_markup=menu_admin_keyboard(),
        )
        await callback.answer()

    # ============================================================
    # CATEGORIES
    # ============================================================

    @router.callback_query(F.data == "admin:categories")
    async def categories_admin(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        categories = await repo.list_categories(
            active_only=False,
        )

        lines = [
            "📂 <b>Kategoriyalar</b>",
            "",
        ]

        if categories:
            for category in categories:
                status = (
                    "✅"
                    if category["is_active"]
                    else "❌"
                )

                lines.append(
                    (
                        f"{category['sort_order']}. "
                        f"{category['name']} {status}"
                    )
                )
        else:
            lines.append(
                "Hozircha kategoriya yo‘q."
            )

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=category_admin_keyboard(),
        )
        await callback.answer()

    # ============================================================
    # PRODUCTS
    # ============================================================

    @router.callback_query(F.data == "admin:products")
    async def products_admin(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        products = await repo.list_products(
            active_only=False,
        )

        lines = [
            "🍔 <b>Mahsulotlar</b>",
            "",
        ]

        if products:
            for product in products:
                status = (
                    "✅"
                    if product["is_active"]
                    else "❌"
                )

                lines.append(
                    (
                        f"{product['sort_order']}. "
                        f"{product['name']} — "
                        f"{money(product['price'])} "
                        f"{status}"
                    )
                )
        else:
            lines.append(
                "Hozircha mahsulot yo‘q."
            )

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=product_admin_keyboard(),
        )
        await callback.answer()

    # ============================================================
    # ORDERS
    # ============================================================

    @router.callback_query(F.data == "admin:orders")
    async def orders_admin(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        orders = await repo.list_orders(
            statuses=[
                "new",
                "accepted",
                "preparing",
                "delivering",
            ],
            limit=30,
        )

        if not orders:
            await callback.message.edit_text(
                "📋 <b>Faol buyurtmalar yo‘q.</b>",
                reply_markup=admin_panel_keyboard(),
            )
            await callback.answer()
            return

        for order in orders:
            await callback.message.answer(
                order_text(order),
                reply_markup=order_status_keyboard(
                    order["id"],
                ),
            )

        await callback.message.edit_text(
            "📋 <b>Buyurtmalar ro‘yxati</b>",
            reply_markup=admin_panel_keyboard(),
        )

        await callback.answer()

    # ============================================================
    # ORDER STATUS
    # ============================================================

    @router.callback_query(
        F.data.startswith("orderstatus:")
    )
    async def order_status(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        try:
            _, status, order_id = callback.data.split(
                ":",
                2,
            )
        except ValueError:
            await callback.answer(
                "❌ Noto‘g‘ri buyurtma tugmasi.",
                show_alert=True,
            )
            return

        try:
            updated = await repo.update_order_status(
                order_id,
                status,
            )
        except Exception as error:
            print(
                "ORDER STATUS ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Statusni o‘zgartirib bo‘lmadi.",
                show_alert=True,
            )
            return

        keyboard = None

        if status not in {
            "completed",
            "cancelled",
        }:
            keyboard = order_status_keyboard(
                order_id,
            )

        await callback.message.edit_text(
            order_text(
                {
                    **updated,
                    "order_items": [],
                }
            ),
            reply_markup=keyboard,
        )

        await callback.answer(
            "✅ Status yangilandi.",
        )

    # ============================================================
    # CATEGORY CREATE
    # ============================================================

    @router.callback_query(F.data == "catadmin:add")
    async def category_add_start(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        await state.clear()

        await state.set_state(
            CategoryStates.create_name,
        )

        await callback.message.answer(
            "Kategoriya nomini kiriting:",
        )

        await callback.answer()

    @router.message(CategoryStates.create_name)
    async def category_create_name(
        message: Message,
        state: FSMContext,
    ) -> None:
        text = (message.text or "").strip()

        if not text:
            await message.answer(
                "Kategoriya nomini kiriting.",
            )
            return

        await state.update_data(
            name=text,
        )

        await state.set_state(
            CategoryStates.create_order,
        )

        await message.answer(
            "Tartib raqamini kiriting (masalan, 1):",
        )

    @router.message(CategoryStates.create_order)
    async def category_create_order(
        message: Message,
        state: FSMContext,
    ) -> None:
        try:
            order = int(
                (message.text or "").strip()
            )
        except ValueError:
            await message.answer(
                "Tartib raqami butun son bo‘lishi kerak.",
            )
            return

        await state.update_data(
            sort_order=order,
        )

        await state.set_state(
            CategoryStates.create_active,
        )

        await message.answer(
            "Kategoriya holatini tanlang:",
            reply_markup=yes_no_keyboard(
                "catcreateactive",
            ),
        )

    @router.callback_query(
        CategoryStates.create_active,
        F.data.startswith("catcreateactive:")
    )
    async def category_create_active(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()

        is_active = callback.data.endswith(
            ":yes"
        )

        await state.update_data(
            is_active=is_active,
        )

        await callback.message.answer(
            (
                f"📂 <b>{data['name']}</b>\n"
                f"Tartib: {data['sort_order']}\n"
                f"Holat: "
                f"{'aktiv' if is_active else 'noaktiv'}\n\n"
                "Saqlansinmi?"
            ),
            reply_markup=confirm_keyboard(
                "catcreate",
            ),
        )

        await callback.answer()

    @router.callback_query(F.data == "catcreate:cancel")
    async def category_create_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ Kategoriya qo‘shish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "catcreate:save")
    async def category_create_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        try:
            await repo.create_category(
                data["name"],
                data["sort_order"],
                data["is_active"],
            )
        except Exception as error:
            print(
                "CATEGORY CREATE ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Kategoriya saqlanmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Kategoriya saqlandi.",
        )

        await callback.answer()

    # ============================================================
    # CATEGORY ACTIONS
    # ============================================================

    @router.callback_query(
        F.data.in_(
            {
                "catadmin:edit",
                "catadmin:delete",
                "catadmin:toggle",
                "catadmin:sort",
            }
        )
    )
    async def category_action_start(
        callback: CallbackQuery,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        action = callback.data.split(
            ":",
            1,
        )[1]

        categories = await repo.list_categories(
            active_only=False,
        )

        if not categories:
            await callback.answer(
                "Kategoriyalar yo‘q.",
                show_alert=True,
            )
            return

        await callback.message.edit_text(
            "Kategoriyani tanlang:",
            reply_markup=select_categories(
                categories,
                f"cataction:{action}",
            ),
        )

        await callback.answer()

    @router.callback_query(
        F.data.startswith("cataction:")
    )
    async def category_action_select(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        try:
            _, action, category_id = (
                callback.data.split(
                    ":",
                    2,
                )
            )
        except ValueError:
            await callback.answer(
                "❌ Noto‘g‘ri kategoriya tugmasi.",
                show_alert=True,
            )
            return

        category = await repo.get_category(
            category_id,
        )

        if not category:
            await callback.answer(
                "Kategoriya topilmadi.",
                show_alert=True,
            )
            return

        await state.update_data(
            category_id=category_id,
            action=action,
        )

        if action == "delete":
            await callback.message.answer(
                (
                    f"🗑 <b>{category['name']}</b>\n\n"
                    "Kategoriyani o‘chirishni tasdiqlaysizmi?"
                ),
                reply_markup=confirm_keyboard(
                    "catdelete",
                ),
            )

        elif action == "toggle":
            await callback.message.answer(
                (
                    f"📂 <b>{category['name']}</b>\n\n"
                    f"Holatini "
                    f"{'noaktiv' if category['is_active'] else 'aktiv'} "
                    "qilaymi?"
                ),
                reply_markup=confirm_keyboard(
                    "cattoggle",
                ),
            )

        elif action == "edit":
            await state.set_state(
                CategoryStates.edit_name,
            )

            await callback.message.answer(
                "Yangi kategoriya nomini kiriting:",
            )

        elif action == "sort":
            await state.set_state(
                CategoryStates.edit_order,
            )

            await callback.message.answer(
                "Yangi tartib raqamini kiriting:",
            )

        await callback.answer()

    # ============================================================
    # CATEGORY EDIT
    # ============================================================

    @router.message(CategoryStates.edit_name)
    async def category_edit_name(
        message: Message,
        state: FSMContext,
    ) -> None:
        value = (message.text or "").strip()

        if not value:
            await message.answer(
                "Yangi kategoriya nomini kiriting.",
            )
            return

        await state.update_data(
            new_value=value,
        )

        await message.answer(
            "O‘zgarish saqlansinmi?",
            reply_markup=confirm_keyboard(
                "catedit",
            ),
        )

    @router.message(CategoryStates.edit_order)
    async def category_edit_order(
        message: Message,
        state: FSMContext,
    ) -> None:
        try:
            value = int(
                (message.text or "").strip()
            )
        except ValueError:
            await message.answer(
                "Tartib raqami butun son bo‘lishi kerak.",
            )
            return

        await state.update_data(
            new_value=value,
        )

        await message.answer(
            "O‘zgarish saqlansinmi?",
            reply_markup=confirm_keyboard(
                "catedit",
            ),
        )

    @router.callback_query(F.data == "catedit:cancel")
    async def category_edit_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘zgarish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "catedit:save")
    async def category_edit_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        field = (
            "name"
            if data.get("action") == "edit"
            else "sort_order"
        )

        try:
            await repo.update_category(
                data["category_id"],
                **{
                    field: data["new_value"],
                },
            )
        except Exception as error:
            print(
                "CATEGORY EDIT ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Kategoriyani yangilab bo‘lmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Kategoriya yangilandi.",
        )

        await callback.answer()

    # ============================================================
    # CATEGORY DELETE
    # ============================================================

    @router.callback_query(F.data == "catdelete:cancel")
    async def category_delete_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘chirish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "catdelete:save")
    async def category_delete_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        try:
            await repo.delete_category(
                data["category_id"],
            )
        except Exception as error:
            print(
                "CATEGORY DELETE ERROR:",
                repr(error),
            )

            await state.clear()

            await callback.message.answer(
                (
                    "❌ Kategoriyani o‘chirib bo‘lmadi.\n\n"
                    "Unga mahsulotlar biriktirilgan bo‘lishi mumkin."
                )
            )

            await callback.answer()
            return

        await state.clear()

        await callback.message.answer(
            "✅ Kategoriya o‘chirildi.",
        )

        await callback.answer()

    # ============================================================
    # CATEGORY TOGGLE
    # ============================================================

    @router.callback_query(F.data == "cattoggle:cancel")
    async def category_toggle_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘zgarish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "cattoggle:save")
    async def category_toggle_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        category = await repo.get_category(
            data["category_id"],
        )

        if not category:
            await state.clear()

            await callback.answer(
                "Kategoriya topilmadi.",
                show_alert=True,
            )
            return

        try:
            await repo.update_category(
                data["category_id"],
                is_active=not category["is_active"],
            )
        except Exception as error:
            print(
                "CATEGORY TOGGLE ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Kategoriya holatini o‘zgartirib bo‘lmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Kategoriya holati yangilandi.",
        )

        await callback.answer()

    # ============================================================
    # PRODUCT CREATE
    # ============================================================

    @router.callback_query(F.data == "prodadmin:add")
    async def product_add_start(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        categories = await repo.list_categories(
            active_only=False,
        )

        if not categories:
            await callback.answer(
                "Avval kamida bitta kategoriya yarating.",
                show_alert=True,
            )
            return

        await state.clear()

        await state.set_state(
            ProductStates.create_category,
        )

        await callback.message.answer(
            "1/6. Kategoriyani tanlang:",
            reply_markup=select_categories(
                categories,
                "prodcreatecat",
            ),
        )

        await callback.answer()

    @router.callback_query(
        ProductStates.create_category,
        F.data.startswith("prodcreatecat:")
    )
    async def product_create_category(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        category_id = callback.data.split(
            ":",
            1,
        )[1]

        category = await repo.get_category(
            category_id,
        )

        if not category:
            await callback.answer(
                "Kategoriya topilmadi.",
                show_alert=True,
            )
            return

        await state.update_data(
            category_id=category_id,
        )

        await state.set_state(
            ProductStates.create_name,
        )

        await callback.message.answer(
            "2/6. Mahsulot nomi:",
        )

        await callback.answer()

    @router.message(ProductStates.create_name)
    async def product_create_name(
        message: Message,
        state: FSMContext,
    ) -> None:
        name = (message.text or "").strip()

        if not name:
            await message.answer(
                "Mahsulot nomini kiriting.",
            )
            return

        await state.update_data(
            name=name,
        )

        await state.set_state(
            ProductStates.create_description,
        )

        await message.answer(
            "3/6. Tavsifni kiriting:\n"
            "Tavsif bo‘lmasa, - yuboring.",
        )

    @router.message(ProductStates.create_description)
    async def product_create_description(
        message: Message,
        state: FSMContext,
    ) -> None:
        description = (
            message.text or ""
        ).strip()

        if description == "-":
            description = ""

        await state.update_data(
            description=description,
        )

        await state.set_state(
            ProductStates.create_price,
        )

        await message.answer(
            "4/6. Narxni so‘mda kiriting:",
        )

    @router.message(ProductStates.create_price)
    async def product_create_price(
        message: Message,
        state: FSMContext,
    ) -> None:
        try:
            price = Decimal(
                (message.text or "")
                .replace(" ", "")
                .replace(",", ".")
            )
        except InvalidOperation:
            await message.answer(
                "Narx son bo‘lishi kerak.",
            )
            return

        if price < 0:
            await message.answer(
                "Narx manfiy bo‘lishi mumkin emas.",
            )
            return

        await state.update_data(
            price=str(price),
        )

        await state.set_state(
            ProductStates.create_image,
        )

        await message.answer(
            "5/6. Mahsulot rasmini yuboring:",
        )

    @router.message(
        ProductStates.create_image,
        F.photo,
    )
    async def product_create_image(
        message: Message,
        state: FSMContext,
    ) -> None:
        await state.update_data(
            image_file_id=message.photo[-1].file_id,
        )

        await state.set_state(
            ProductStates.create_active,
        )

        await message.answer(
            "6/6. Mahsulot holatini tanlang:",
            reply_markup=yes_no_keyboard(
                "prodcreateactive",
            ),
        )

    @router.message(ProductStates.create_image)
    async def product_create_image_invalid(
        message: Message,
    ) -> None:
        await message.answer(
            "Iltimos, mahsulot rasmini Telegram orqali yuboring.",
        )

    @router.callback_query(
        ProductStates.create_active,
        F.data.startswith("prodcreateactive:")
    )
    async def product_create_active(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()

        is_active = callback.data.endswith(
            ":yes"
        )

        await state.update_data(
            is_active=is_active,
        )

        await callback.message.answer(
            (
                f"🍔 <b>{data['name']}</b>\n"
                f"Tavsif: {data['description'] or '—'}\n"
                f"Narx: {money(data['price'])}\n"
                f"Holat: "
                f"{'aktiv' if is_active else 'noaktiv'}\n\n"
                "Saqlansinmi?"
            ),
            reply_markup=confirm_keyboard(
                "prodcreate",
            ),
        )

        await callback.answer()

    @router.callback_query(F.data == "prodcreate:cancel")
    async def product_create_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ Mahsulot qo‘shish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "prodcreate:save")
    async def product_create_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        product_data = {
            "category_id": data["category_id"],
            "name": data["name"],
            "description": data.get("description", ""),
            "price": data["price"],
            "image_file_id": data.get("image_file_id"),
            "is_active": data["is_active"],
            "sort_order": 0,
        }

        try:
            await repo.create_product(
                product_data,
            )
        except Exception as error:
            print(
                "PRODUCT CREATE ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Mahsulot saqlanmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Mahsulot saqlandi.",
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer()

    # ============================================================
    # PRODUCT ACTION START
    # ============================================================

    @router.callback_query(
        F.data.in_(
            {
                "prodadmin:edit",
                "prodadmin:delete",
                "prodadmin:toggle",
                "prodadmin:price",
                "prodadmin:image",
                "prodadmin:name",
                "prodadmin:description",
                "prodadmin:category",
                "prodadmin:sort",
            }
        )
    )
    async def product_action_start(
        callback: CallbackQuery,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        action = callback.data.split(
            ":",
            1,
        )[1]

        products = await repo.list_products(
            active_only=False,
        )

        if not products:
            await callback.answer(
                "Mahsulotlar yo‘q.",
                show_alert=True,
            )
            return

        await callback.message.edit_text(
            "Mahsulotni tanlang:",
            reply_markup=select_products(
                products,
                f"prodaction:{action}",
            ),
        )

        await callback.answer()

    # ============================================================
    # PRODUCT ACTION SELECT
    # ============================================================

    @router.callback_query(
        F.data.startswith("prodaction:")
    )
    async def product_action_select(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        try:
            _, action, product_id = (
                callback.data.split(
                    ":",
                    2,
                )
            )
        except ValueError:
            await callback.answer(
                "❌ Noto‘g‘ri mahsulot tugmasi.",
                show_alert=True,
            )
            return

        product = await repo.get_product(
            product_id,
        )

        if not product:
            await callback.answer(
                "Mahsulot topilmadi.",
                show_alert=True,
            )
            return

        await state.update_data(
            product_id=product_id,
            action=action,
        )

        if action == "delete":
            await callback.message.answer(
                (
                    f"🗑 <b>{product['name']}</b>\n\n"
                    "Bu mahsulotni o‘chirishni tasdiqlaysizmi?"
                ),
                reply_markup=confirm_keyboard(
                    "proddelete",
                ),
            )

        elif action == "toggle":
            await callback.message.answer(
                (
                    f"🍔 <b>{product['name']}</b>\n\n"
                    f"Holatini "
                    f"{'noaktiv' if product['is_active'] else 'aktiv'} "
                    "qilaymi?"
                ),
                reply_markup=confirm_keyboard(
                    "prodtoggle",
                ),
            )

        elif action == "category":
            categories = await repo.list_categories(
                active_only=False,
            )

            await callback.message.answer(
                "Yangi kategoriyani tanlang:",
                reply_markup=select_categories(
                    categories,
                    f"prodcat:{product_id}",
                ),
            )

        elif action == "image":
            await state.set_state(
                ProductStates.edit_value,
            )

            await callback.message.answer(
                "Yangi mahsulot rasmini yuboring:",
            )

        else:
            await state.set_state(
                ProductStates.edit_value,
            )

            prompts = {
                "price": "Yangi narxni kiriting:",
                "name": "Yangi nomni kiriting:",
                "description": "Yangi tavsifni kiriting:",
                "sort": "Yangi tartib raqamini kiriting:",
                "edit": "Yangi mahsulot nomini kiriting:",
            }

            await callback.message.answer(
                prompts.get(
                    action,
                    "Yangi qiymatni kiriting:",
                )
            )

        await callback.answer()

    # ============================================================
    # PRODUCT CATEGORY CHANGE
    # ============================================================

    @router.callback_query(
        F.data.startswith("prodcat:")
    )
    async def product_category_selected(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        try:
            _, product_id, category_id = (
                callback.data.split(
                    ":",
                    2,
                )
            )
        except ValueError:
            await callback.answer(
                "❌ Noto‘g‘ri kategoriya tugmasi.",
                show_alert=True,
            )
            return

        category = await repo.get_category(
            category_id,
        )

        if not category:
            await callback.answer(
                "Kategoriya topilmadi.",
                show_alert=True,
            )
            return

        await state.update_data(
            product_id=product_id,
            new_value=category_id,
            action="category",
        )

        await callback.message.answer(
            (
                f"📂 Yangi kategoriya: "
                f"<b>{category['name']}</b>\n\n"
                "Saqlansinmi?"
            ),
            reply_markup=confirm_keyboard(
                "prodedit",
            ),
        )

        await callback.answer()

    # ============================================================
    # PRODUCT EDIT
    # ============================================================

    @router.message(
        ProductStates.edit_value,
        F.photo,
    )
    async def product_edit_photo(
        message: Message,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()

        if data.get("action") != "image":
            await message.answer(
                "Bu yerda rasm kerak emas.",
            )
            return

        await state.update_data(
            new_value=message.photo[-1].file_id,
        )

        await message.answer(
            "Rasm almashtirilsinmi?",
            reply_markup=confirm_keyboard(
                "prodedit",
            ),
        )

    @router.message(ProductStates.edit_value)
    async def product_edit_value(
        message: Message,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()

        action = data.get(
            "action",
        )

        value = (
            message.text or ""
        ).strip()

        if not value:
            await message.answer(
                "Qiymatni kiriting.",
            )
            return

        if action == "image":
            await message.answer(
                "Iltimos, rasm yuboring.",
            )
            return

        if action == "price":
            try:
                value = str(
                    Decimal(
                        value
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                )
            except InvalidOperation:
                await message.answer(
                    "Narx son bo‘lishi kerak.",
                )
                return

            if Decimal(value) < 0:
                await message.answer(
                    "Narx manfiy bo‘lishi mumkin emas.",
                )
                return

        if action == "sort":
            try:
                value = int(value)
            except ValueError:
                await message.answer(
                    "Tartib raqami butun son bo‘lishi kerak.",
                )
                return

        if action == "description" and value == "-":
            value = ""

        await state.update_data(
            new_value=value,
        )

        await message.answer(
            "O‘zgarish saqlansinmi?",
            reply_markup=confirm_keyboard(
                "prodedit",
            ),
        )

    @router.callback_query(F.data == "prodedit:cancel")
    async def product_edit_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘zgarish bekor qilindi.",
        )

        await callback.answer()

    @router.callback_query(F.data == "prodedit:save")
    async def product_edit_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        action = data.get(
            "action",
        )

        field_map = {
            "price": "price",
            "name": "name",
            "description": "description",
            "sort": "sort_order",
            "image": "image_file_id",
            "category": "category_id",
            "edit": "name",
        }

        field = field_map.get(
            action,
        )

        if not field:
            await callback.answer(
                "Noma‘lum amal.",
                show_alert=True,
            )
            return

        try:
            await repo.update_product(
                data["product_id"],
                **{
                    field: data["new_value"],
                },
            )
        except Exception as error:
            print(
                "PRODUCT EDIT ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Mahsulotni yangilab bo‘lmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Mahsulot yangilandi.",
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer()

    # ============================================================
    # PRODUCT DELETE
    # ============================================================

    @router.callback_query(F.data == "proddelete:cancel")
    async def product_delete_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘chirish bekor qilindi.",
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer()

    @router.callback_query(F.data == "proddelete:save")
    async def product_delete_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        product_id = data.get(
            "product_id",
        )

        if not product_id:
            await state.clear()

            await callback.answer(
                "Mahsulot topilmadi.",
                show_alert=True,
            )
            return

        product = await repo.get_product(
            product_id,
        )

        if not product:
            await state.clear()

            await callback.answer(
                "Mahsulot topilmadi.",
                show_alert=True,
            )
            return

        try:
            await repo.delete_product(
                product_id,
            )
        except Exception as error:
            print(
                "PRODUCT DELETE ERROR:",
                repr(error),
            )

            await state.clear()

            await callback.message.answer(
                (
                    "❌ Mahsulotni o‘chirib bo‘lmadi.\n\n"
                    "Bu mahsulot eski buyurtmalarda ishlatilgan "
                    "bo‘lishi mumkin. Bunday holatda uni "
                    "o‘chirish o‘rniga noaktiv qilish kerak."
                ),
                reply_markup=product_admin_keyboard(),
            )

            await callback.answer()
            return

        await state.clear()

        await callback.message.answer(
            (
                f"✅ <b>{product['name']}</b> "
                "muvaffaqiyatli o‘chirildi."
            ),
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer(
            "Mahsulot o‘chirildi.",
        )

    # ============================================================
    # PRODUCT TOGGLE
    # ============================================================

    @router.callback_query(F.data == "prodtoggle:cancel")
    async def product_toggle_cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()

        await callback.message.answer(
            "❌ O‘zgarish bekor qilindi.",
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer()

    @router.callback_query(F.data == "prodtoggle:save")
    async def product_toggle_save(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if not allowed(callback.from_user.id):
            await deny(callback)
            return

        data = await state.get_data()

        product_id = data.get(
            "product_id",
        )

        if not product_id:
            await state.clear()

            await callback.answer(
                "Mahsulot topilmadi.",
                show_alert=True,
            )
            return

        product = await repo.get_product(
            product_id,
        )

        if not product:
            await state.clear()

            await callback.answer(
                "Mahsulot topilmadi.",
                show_alert=True,
            )
            return

        try:
            await repo.update_product(
                product_id,
                is_active=not product["is_active"],
            )
        except Exception as error:
            print(
                "PRODUCT TOGGLE ERROR:",
                repr(error),
            )

            await callback.answer(
                "❌ Mahsulot holatini o‘zgartirib bo‘lmadi.",
                show_alert=True,
            )
            return

        await state.clear()

        await callback.message.answer(
            "✅ Mahsulot holati yangilandi.",
            reply_markup=product_admin_keyboard(),
        )

        await callback.answer()

    return router