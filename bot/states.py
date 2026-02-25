from aiogram.fsm.state import State, StatesGroup

class NewListing(StatesGroup):
    title = State()

    region = State()
    city = State()
    district = State()  # только для Ташкент (город)
    address = State()

    freshness = State()
    comment = State()
    price = State()
    contact = State()

    media = State()
    confirm = State()

class AdminExamples(StatesGroup):
    collecting = State()