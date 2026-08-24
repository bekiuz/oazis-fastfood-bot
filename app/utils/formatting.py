from __future__ import annotations

from decimal import Decimal
from typing import Any


STATUS_LABELS = {
    "new": "🆕 Yangi",
    "accepted": "✅ Qabul qilindi",
    "preparing": "👨‍🍳 Tayyorlanmoqda",
    "delivering": "🚚 Yetkazilmoqda",
    "completed": "🏁 Yakunlandi",
    "cancelled": "❌ Bekor qilindi",
}


PAYMENT_LABELS = {
    "cash": "💵 Naqd",
    "online": "🌐 Online",
}


def money(
    value: Decimal | float | int | str,
) -> str:
    return (
        f"{Decimal(str(value)):,.0f}"
        .replace(",", " ")
        + " so'm"
    )


def cart_total(
    cart: list[dict[str, Any]],
) -> Decimal:
    return sum(
        (
            Decimal(str(item["price"]))
            * int(item["quantity"])
            for item in cart
        ),
        Decimal("0"),
    )


def product_text(
    product: dict[str, Any],
) -> str:
    category = product.get("categories") or {}

    category_name = (
        category.get("name", "")
        if isinstance(category, dict)
        else ""
    )

    parts = [
        f"🍔 <b>{product['name']}</b>",
        f"💰 {money(product['price'])}",
    ]

    if category_name:
        parts.append(
            f"📂 {category_name}"
        )

    if product.get("description"):
        parts.append(
            f"\n{product['description']}"
        )

    return "\n".join(parts)


def _location_text(
    order: dict[str, Any],
) -> str:
    latitude = order.get("latitude")
    longitude = order.get("longitude")

    if (
        latitude is not None
        and longitude is not None
    ):
        return (
            f"📍 Lokatsiya: "
            f"{latitude}, {longitude}"
        )

    location = order.get("location")

    if isinstance(location, dict):
        location_latitude = location.get(
            "latitude"
        )
        location_longitude = location.get(
            "longitude"
        )

        if (
            location_latitude is not None
            and location_longitude is not None
        ):
            return (
                f"📍 Lokatsiya: "
                f"{location_latitude}, "
                f"{location_longitude}"
            )

    address = order.get("address")

    if address:
        return f"📍 Manzil: {address}"

    return "📍 Lokatsiya: —"


def _item_total(
    item: dict[str, Any],
) -> Decimal:
    """
    order_items dan kelgan itemda `total` bo‘lsa,
    shuni ishlatadi.

    Cart ichidagi itemda `total` bo‘lmasa,
    price × quantity orqali hisoblaydi.
    """
    if item.get("total") is not None:
        return Decimal(
            str(item["total"])
        )

    price = Decimal(
        str(item.get("price", 0))
    )

    quantity = int(
        item.get("quantity", 0)
    )

    return price * quantity


def order_text(
    order: dict[str, Any],
) -> str:
    order_id = order.get(
        "id",
        "—",
    )

    status = order.get(
        "status",
    )

    payment_method = order.get(
        "payment_method",
    )

    status_label = STATUS_LABELS.get(
        status,
        status or "—",
    )

    payment_label = PAYMENT_LABELS.get(
        payment_method,
        payment_method or "—",
    )

    lines = [
        (
            f"🧾 <b>Buyurtma "
            f"#{str(order_id)[:8]}</b>"
        ),
        f"Holat: {status_label}",
        (
            f"💰 Jami: "
            f"<b>{money(order.get('total_amount', 0))}</b>"
        ),
        f"💳 To‘lov: {payment_label}",
        _location_text(order),
    ]

    customer_name = order.get(
        "customer_name",
    )

    if customer_name:
        lines.append(
            f"👤 Ism: {customer_name}"
        )

    phone = order.get(
        "phone",
    )

    if phone:
        lines.append(
            f"📞 Telefon: {phone}"
        )

    comment = order.get(
        "comment",
    )

    if comment:
        lines.append(
            f"📝 Izoh: {comment}"
        )

    for item in order.get(
        "order_items",
        [],
    ):
        item_total = _item_total(item)

        lines.append(
            (
                f"• {item.get('product_name', item.get('name', 'Mahsulot'))} "
                f"× {item.get('quantity', 0)} — "
                f"{money(item_total)}"
            )
        )

    return "\n".join(lines)