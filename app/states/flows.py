from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    name = State()
    phone = State()
    location = State()
    comment = State()
    payment_method = State()
    cash_confirmation = State()
    confirmation = State()


class CategoryStates(StatesGroup):
    create_name = State()
    create_order = State()
    create_active = State()
    edit_name = State()
    edit_order = State()
    edit_active = State()


class ProductStates(StatesGroup):
    create_category = State()
    create_name = State()
    create_description = State()
    create_price = State()
    create_image = State()
    create_active = State()
    edit_value = State()


class AdminOrderStates(StatesGroup):
    change_status = State()