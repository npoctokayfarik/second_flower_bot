from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------- базовые ----------
def kb_start() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Разместить", callback_data="new")
    b.adjust(1)
    return b.as_markup()

def kb_confirm() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Отправить на модерацию", callback_data="send_to_review")
    b.button(text="✏️ Заново", callback_data="restart_new")
    b.button(text="❌ Отмена", callback_data="cancel_new")
    b.adjust(1)
    return b.as_markup()

def kb_finish_media() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Завершить фото/видео", callback_data="finish_media")
    b.adjust(1)
    return b.as_markup()

def kb_request_phone() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ---------- модерация ----------
def kb_admin_review(listing_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Опубликовать", callback_data=f"admin_publish:{listing_id}")
    b.button(text="❌ Отклонить", callback_data=f"admin_reject:{listing_id}")
    b.adjust(1)
    return b.as_markup()

# ---------- продано (в ЛС продавцу) ----------
def kb_user_sold(listing_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Продано", callback_data=f"user_sold:{listing_id}")
    b.adjust(1)
    return b.as_markup()

# ---------- локация ----------
REGIONS = [
    ("Республика Каракалпакстан", "krk"),
    ("Ташкент (город)", "tash_city"),
    ("Ташкентская область", "tash_obl"),
    ("Андижанская область", "and"),
    ("Бухарская область", "bkh"),
    ("Ферганская область", "fer"),
    ("Джизакская область", "jiz"),
    ("Хорезмская область", "khr"),
    ("Кашкадарьинская область", "qsh"),
    ("Навоийская область", "nav"),
    ("Наманганская область", "nam"),
    ("Самаркандская область", "sam"),
    ("Сырдарьинская область", "syr"),
    ("Сурхандарьинская область", "sur"),
    ("Другое", "other"),
]

CITIES = {
    "krk": [("Нукус", "nukus"), ("Ходжейли", "khodjeyli"), ("Турткуль", "turtkul"), ("Беруни", "beruni"),
            ("Кунград", "kungrad"), ("Муйнак", "moynaq"), ("Чимбай", "chimbay"), ("Другое", "other")],

    "tash_city": [("Ташкент", "tashkent"), ("Другое", "other")],

    "tash_obl": [("Чирчик", "chirchiq"), ("Ангрен", "angren"), ("Алмалык", "almalyk"), ("Бекабад", "bekabad"),
                 ("Янгиюль", "yangiyul"), ("Газалкент", "gazalkent"), ("Другое", "other")],

    "and": [("Андижан", "andijan"), ("Асака", "asaka"), ("Шахрихан", "shahrikhan"), ("Ханабад", "khanabad"), ("Другое", "other")],
    "bkh": [("Бухара", "bukhara"), ("Каган", "kagan"), ("Гиждуван", "gijduvan"), ("Другое", "other")],
    "fer": [("Фергана", "fergana"), ("Коканд", "kokand"), ("Маргилан", "margilan"), ("Кува", "kuva"), ("Другое", "other")],
    "jiz": [("Джизак", "jizzakh"), ("Пахтакор", "paxtakor"), ("Другое", "other")],
    "khr": [("Ургенч", "urgench"), ("Хива", "khiva"), ("Хазарасп", "hazorasp"), ("Другое", "other")],
    "qsh": [("Карши", "qarshi"), ("Шахрисабз", "shahrisabz"), ("Гузар", "guzar"), ("Другое", "other")],
    "nav": [("Навои", "navoi"), ("Зарафшан", "zarafshan"), ("Учкудук", "uchquduq"), ("Другое", "other")],
    "nam": [("Наманган", "namangan"), ("Чуст", "chust"), ("Пап", "pap"), ("Другое", "other")],
    "sam": [("Самарканд", "samarkand"), ("Каттакурган", "kattakurgan"), ("Ургут", "urgut"), ("Другое", "other")],
    "syr": [("Гулистан", "gulistan"), ("Янгиер", "yangier"), ("Ширин", "shirin"), ("Другое", "other")],
    "sur": [("Термез", "termez"), ("Денау", "denau"), ("Шерабад", "sherabad"), ("Другое", "other")],
    "other": [("Другое", "other")],
}

TASHKENT_DISTRICTS = [
    ("Алмазар", "almazar"),
    ("Бектемир", "bektemir"),
    ("Мирабад", "mirabad"),
    ("Мирзо-Улугбек", "mirzo_ulugbek"),
    ("Сергелий", "sergeli"),
    ("Учтепа", "uchtepa"),
    ("Чиланзар", "chilanzar"),
    ("Шайхантахур", "shaykhontohur"),
    ("Юнусабад", "yunusabad"),
    ("Яккасарай", "yakkasaray"),
    ("Яшнабад", "yashnabad"),
    ("Другое", "other"),
]

def kb_region() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for name, code in REGIONS:
        b.button(text=f"📍 {name}", callback_data=f"region:{code}")
    b.adjust(1)
    return b.as_markup()

def kb_city(region_code: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    items = CITIES.get(region_code, [("Другое", "other")])
    for name, code in items:
        b.button(text=name, callback_data=f"city:{code}")
    b.adjust(2)
    return b.as_markup()

def kb_district_tashkent() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for name, code in TASHKENT_DISTRICTS:
        b.button(text=name, callback_data=f"district:{code}")
    b.adjust(2)
    return b.as_markup()