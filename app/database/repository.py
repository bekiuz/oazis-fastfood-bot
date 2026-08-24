from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Callable

from supabase import Client


class Repository:
    """Supabase data access layer. Blocking SDK calls run in worker threads."""

    ALLOWED_PAYMENT_METHODS = {"cash", "online"}

    def __init__(self, client: Client) -> None:
        self.client = client

    async def _call(self, operation: Callable[[], Any]) -> Any:
        return await asyncio.to_thread(operation)

    # ============================================================
    # CATEGORIES
    # ============================================================

    async def list_categories(
        self,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        def op():
            query = (
                self.client
                .table("categories")
                .select("*")
                .order("sort_order")
            )

            if active_only:
                query = query.eq("is_active", True)

            return query.execute().data or []

        return await self._call(op)

    async def get_category(
        self,
        category_id: str,
    ) -> dict[str, Any] | None:
        def op():
            result = (
                self.client
                .table("categories")
                .select("*")
                .eq("id", category_id)
                .maybe_single()
                .execute()
            )
            return result.data

        return await self._call(op)

    async def create_category(
        self,
        name: str,
        sort_order: int,
        is_active: bool,
    ) -> dict[str, Any]:
        def op():
            result = (
                self.client
                .table("categories")
                .insert(
                    {
                        "name": name,
                        "sort_order": sort_order,
                        "is_active": is_active,
                    }
                )
                .execute()
            )

            return result.data[0]

        return await self._call(op)

    async def update_category(
        self,
        category_id: str,
        **values: Any,
    ) -> dict[str, Any]:
        def op():
            result = (
                self.client
                .table("categories")
                .update(values)
                .eq("id", category_id)
                .execute()
            )

            return result.data[0]

        return await self._call(op)

    async def delete_category(
        self,
        category_id: str,
    ) -> None:
        await self._call(
            lambda: (
                self.client
                .table("categories")
                .delete()
                .eq("id", category_id)
                .execute()
            )
        )

    # ============================================================
    # PRODUCTS
    # ============================================================

    async def list_products(
        self,
        category_id: str | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        def op():
            query = (
                self.client
                .table("products")
                .select("*, categories(name)")
                .order("sort_order")
            )

            if category_id:
                query = query.eq("category_id", category_id)

            if active_only:
                query = query.eq("is_active", True)

            return query.execute().data or []

        return await self._call(op)

    async def get_product(
        self,
        product_id: str,
    ) -> dict[str, Any] | None:
        def op():
            result = (
                self.client
                .table("products")
                .select("*, categories(name)")
                .eq("id", product_id)
                .maybe_single()
                .execute()
            )

            return result.data

        return await self._call(op)

    async def create_product(
        self,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        def op():
            result = (
                self.client
                .table("products")
                .insert(values)
                .execute()
            )

            return result.data[0]

        return await self._call(op)

    async def update_product(
        self,
        product_id: str,
        **values: Any,
    ) -> dict[str, Any]:
        def op():
            result = (
                self.client
                .table("products")
                .update(values)
                .eq("id", product_id)
                .execute()
            )

            return result.data[0]

        return await self._call(op)

    async def delete_product(
        self,
        product_id: str,
    ) -> None:
        await self._call(
            lambda: (
                self.client
                .table("products")
                .delete()
                .eq("id", product_id)
                .execute()
            )
        )

    # ============================================================
    # CUSTOMERS
    # ============================================================

    async def upsert_customer(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        **values: Any,
    ) -> dict[str, Any]:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            **values,
        }

        def op():
            result = (
                self.client
                .table("customers")
                .upsert(
                    payload,
                    on_conflict="telegram_id",
                )
                .execute()
            )

            return result.data[0]

        return await self._call(op)

    async def get_customer(
        self,
        telegram_id: int,
    ) -> dict[str, Any] | None:
        def op():
            result = (
                self.client
                .table("customers")
                .select("*")
                .eq("telegram_id", telegram_id)
                .maybe_single()
                .execute()
            )

            return result.data

        return await self._call(op)

    # ============================================================
    # ORDERS
    # ============================================================

    async def create_order(
        self,
        customer_id: str,
        cart: list[dict[str, Any]],
        total_amount: Decimal,
        payment_method: str,
        address: str,
        comment: str | None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict[str, Any]:
        if payment_method not in self.ALLOWED_PAYMENT_METHODS:
            raise ValueError(
                "Noto‘g‘ri to‘lov turi. "
                "Faqat 'cash' yoki 'online' ruxsat etilgan."
            )

        if not cart:
            raise ValueError("Buyurtma savati bo‘sh.")

        order_payload = {
            "customer_id": customer_id,
            "total_amount": float(total_amount),
            "status": "new",
            "payment_method": payment_method,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "comment": comment,
        }

        def op():
            # 1. Buyurtmani yaratish
            order_result = (
                self.client
                .table("orders")
                .insert(order_payload)
                .execute()
            )

            if not order_result.data:
                raise RuntimeError(
                    "Buyurtma yaratilmadi."
                )

            order = order_result.data[0]

            # 2. Buyurtma mahsulotlarini tayyorlash
            items: list[dict[str, Any]] = []

            for item in cart:
                price = Decimal(
                    str(item["price"])
                )
                quantity = int(
                    item["quantity"]
                )

                if quantity <= 0:
                    continue

                item_total = (
                    price * quantity
                )

                items.append(
                    {
                        "order_id": order["id"],
                        "product_id": item["product_id"],
                        "product_name": item["name"],
                        "quantity": quantity,
                        "price": float(price),
                        "total": float(item_total),
                    }
                )

            # 3. Order items saqlash
            if items:
                items_result = (
                    self.client
                    .table("order_items")
                    .insert(items)
                    .execute()
                )

                if not items_result.data:
                    raise RuntimeError(
                        "Buyurtma mahsulotlari saqlanmadi."
                    )

            return order

        return await self._call(op)

    async def list_orders(
        self,
        statuses: list[str] | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        def op():
            query = (
                self.client
                .table("orders")
                .select(
                    "*, customers(*), order_items(*)"
                )
                .order(
                    "created_at",
                    desc=True,
                )
                .limit(limit)
            )

            if statuses:
                query = query.in_(
                    "status",
                    statuses,
                )

            return query.execute().data or []

        return await self._call(op)

    async def get_customer_orders(
        self,
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        customer = await self.get_customer(
            telegram_id
        )

        if not customer:
            return []

        def op():
            result = (
                self.client
                .table("orders")
                .select(
                    "*, order_items(*)"
                )
                .eq(
                    "customer_id",
                    customer["id"],
                )
                .order(
                    "created_at",
                    desc=True,
                )
                .limit(limit)
                .execute()
            )

            return result.data or []

        return await self._call(op)

    async def update_order_status(
        self,
        order_id: str,
        status: str,
    ) -> dict[str, Any]:
        def op():
            result = (
                self.client
                .table("orders")
                .update(
                    {"status": status}
                )
                .eq("id", order_id)
                .execute()
            )

            return result.data[0]

        return await self._call(op)