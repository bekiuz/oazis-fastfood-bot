from decimal import Decimal

from app.utils.formatting import cart_total, money, product_text


def test_money_format():
    assert money(12500) == "12 500 so'm"


def test_cart_total():
    cart = [
        {"price": "12000", "quantity": 2},
        {"price": "7500", "quantity": 1},
    ]
    assert cart_total(cart) == Decimal("31500")


def test_product_text_contains_core_fields():
    text = product_text({"name": "Burger", "price": "20000", "description": "Mazali", "categories": {"name": "Burgerlar"}})
    assert "Burger" in text
    assert "20 000 so'm" in text
    assert "Mazali" in text
    assert "Burgerlar" in text
