import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from .states import NewListing
from .texts import RULES_TEXT, build_public_caption
from .keyboards import (
    kb_start, kb_confirm, kb_request_phone,
    kb_region, kb_city, kb_district_tashkent, kb_finish_media
)
from .db import DB
from .utils import build_media_group

user_router = Router()

PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{7,}$")

REGION_NAME = {
    "krk": "Республика Каракалпакстан",
    "tash_city": "Ташкент (город)",
    "tash_obl": "Ташкентская область",
    "and": "Андижанская область",
    "bkh": "Бухарская область",
    "fer": "Ферганская область",
    "jiz": "Джизакская область",
    "khr": "Хорезмская область",
    "qsh": "Кашкадарьинская область",
    "nav": "Навоийская область",
    "nam": "Наманганская область",
    "sam": "Самаркандская область",
    "syr": "Сырдарьинская область",
    "sur": "Сурхандарьинская область",
    "other": "Другое",
}

CITY_NAME = {
    "nukus":"Нукус","khodjeyli":"Ходжейли","turtkul":"Турткуль","beruni":"Беруни","kungrad":"Кунград","moynaq":"Муйнак","chimbay":"Чимбай",
    "tashkent":"Ташкент","chirchiq":"Чирчик","angren":"Ангрен","almalyk":"Алмалык","bekabad":"Бекабад","yangiyul":"Янгиюль","gazalkent":"Газалкент",
    "andijan":"Андижан","asaka":"Асака","shahrikhan":"Шахрихан","khanabad":"Ханабад",
    "bukhara":"Бухара","kagan":"Каган","gijduvan":"Гиждуван",
    "fergana":"Фергана","kokand":"Коканд","margilan":"Маргилан","kuva":"Кува",
    "jizzakh":"Джизак","paxtakor":"Пахтакор",
    "urgench":"Ургенч","khiva":"Хива","hazorasp":"Хазарасп",
    "qarshi":"Карши","shahrisabz":"Шахрисабз","guzar":"Гузар",
    "navoi":"Навои","zarafshan":"Зарафшан","uchquduq":"Учкудук",
    "namangan":"Наманган","chust":"Чуст","pap":"Пап",
    "samarkand":"Самарканд","kattakurgan":"Каттакурган","urgut":"Ургут",
    "gulistan":"Гулистан","yangier":"Янгиер","shirin":"Ширин",
    "termez":"Термез","denau":"Денау","sherabad":"Шерабад",
    "other":"Другое",
}

DISTRICT_NAME = {
    "almazar":"Алмазар","bektemir":"Бектемир","mirabad":"Мирабад","mirzo_ulugbek":"Мирзо-Улугбек",
    "sergeli":"Сергелий","uchtepa":"Учтепа","chilanzar":"Чиланзар","shaykhontohur":"Шайхантахур",
    "yunusabad":"Юнусабад","yakkasaray":"Яккасарай","yashnabad":"Яшнабад","other":"Другое"
}

def digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def normalize_phone(raw: str) -> str:
    raw = (raw or "").strip()
    d = digits_only(raw)
    if d.startswith("998") and len(d) >= 12:
        return "+" + d[:12]
    if len(d) == 9:
        return "+998" + d
    if raw.startswith("+") and d.startswith("998") and len(d) >= 12:
        return "+" + d[:12]
    return raw

def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone)) and digits_only(phone).startswith("998")

def fmt_sum(num: int) -> str:
    return f"{num:,}".replace(",", " ")

def parse_price_int(text: str) -> int | None:
    d = digits_only((text or "").strip())
    if not d:
        return None
    try:
        return int(d)
    except ValueError:
        return None

@user_router.message(CommandStart())
async def start(m: Message, db: DB):
    photo_ids = await db.get_examples()
    if len(photo_ids) == 3:
        media = [InputMediaPhoto(media=pid) for pid in photo_ids]
        media[0].caption = "✅ Пример правильной записки"
        await m.bot.send_media_group(chat_id=m.chat.id, media=media)

    await m.answer(RULES_TEXT, reply_markup=kb_start())

@user_router.callback_query(F.data == "new")
async def new(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.clear()
    await cb.message.answer("Название букета:")
    await state.set_state(NewListing.title)

@user_router.callback_query(F.data == "restart_new")
async def restart_new(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.clear()
    await cb.message.answer("Название букета:")
    await state.set_state(NewListing.title)

@user_router.callback_query(F.data == "cancel_new")
async def cancel_new(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.clear()
    await cb.message.answer("Ок ✅", reply_markup=ReplyKeyboardRemove())

@user_router.message(NewListing.title)
async def st_title(m: Message, state: FSMContext):
    await state.update_data(title=(m.text or "").strip())
    await m.answer("📍 Регион:", reply_markup=kb_region())
    await state.set_state(NewListing.region)

@user_router.callback_query(NewListing.region, F.data.startswith("region:"))
async def pick_region(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    code = cb.data.split(":", 1)[1]
    if code == "other":
        await cb.message.answer("Напиши регион:")
        return
    await state.update_data(region=REGION_NAME.get(code, code), region_code=code)
    await cb.message.answer("🏙️ Город:", reply_markup=kb_city(code))
    await state.set_state(NewListing.city)

@user_router.message(NewListing.region)
async def region_text(m: Message, state: FSMContext):
    txt = (m.text or "").strip()
    if not txt:
        return await m.answer("Напиши регион:")
    await state.update_data(region=txt, region_code="other")
    await m.answer("🏙️ Город:", reply_markup=kb_city("other"))
    await state.set_state(NewListing.city)

@user_router.callback_query(NewListing.city, F.data.startswith("city:"))
async def pick_city(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    code = cb.data.split(":", 1)[1]
    data = await state.get_data()
    region_code = data.get("region_code", "other")

    if code == "other":
        await cb.message.answer("Напиши город:")
        return

    city_name = CITY_NAME.get(code, code)
    await state.update_data(city=city_name)

    if region_code == "tash_city" and city_name == "Ташкент":
        await cb.message.answer("Район:", reply_markup=kb_district_tashkent())
        await state.set_state(NewListing.district)
    else:
        await state.update_data(district="")  # ✅ важно (NOT NULL в БД)
        await cb.message.answer("Адрес (улица, дом, ориентир):")
        await state.set_state(NewListing.address)

@user_router.message(NewListing.city)
async def city_text(m: Message, state: FSMContext):
    txt = (m.text or "").strip()
    if not txt:
        return await m.answer("Напиши город:")
    await state.update_data(city=txt)

    data = await state.get_data()
    region_code = data.get("region_code", "other")

    if region_code == "tash_city" and txt.lower() == "ташкент":
        await m.answer("Район:", reply_markup=kb_district_tashkent())
        await state.set_state(NewListing.district)
    else:
        await state.update_data(district="")  # ✅ важно (NOT NULL в БД)
        await m.answer("Адрес (улица, дом, ориентир):")
        await state.set_state(NewListing.address)

@user_router.callback_query(NewListing.district, F.data.startswith("district:"))
async def pick_district(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    code = cb.data.split(":", 1)[1]
    if code == "other":
        await cb.message.answer("Напиши район:")
        return
    await state.update_data(district=DISTRICT_NAME.get(code, code))
    await cb.message.answer("Адрес (улица, дом, ориентир):")
    await state.set_state(NewListing.address)

@user_router.message(NewListing.district)
async def district_text(m: Message, state: FSMContext):
    txt = (m.text or "").strip()
    if not txt:
        return await m.answer("Напиши район:")
    await state.update_data(district=txt)
    await m.answer("Адрес (улица, дом, ориентир):")
    await state.set_state(NewListing.address)

@user_router.message(NewListing.address)
async def st_address(m: Message, state: FSMContext):
    txt = (m.text or "").strip()
    if not txt:
        return await m.answer("Адрес (улица, дом, ориентир):")
    await state.update_data(address=txt)
    await m.answer("Свежесть:")
    await state.set_state(NewListing.freshness)

@user_router.message(NewListing.freshness)
async def st_fresh(m: Message, state: FSMContext):
    await state.update_data(freshness=(m.text or "").strip())
    await m.answer("Комментарий:")
    await state.set_state(NewListing.comment)

@user_router.message(NewListing.comment)
async def st_comment(m: Message, state: FSMContext):
    await state.update_data(comment=(m.text or "").strip())
    await m.answer("Цена (сум):")
    await state.set_state(NewListing.price)

@user_router.message(NewListing.price)
async def st_price(m: Message, state: FSMContext):
    price_int = parse_price_int(m.text)
    if price_int is None or price_int <= 0:
        return await m.answer("Введи цену числом 🙂")

    await state.update_data(price=str(price_int))
    await m.answer("Отправь номер телефона:", reply_markup=kb_request_phone())
    await state.set_state(NewListing.contact)

@user_router.message(NewListing.contact, F.contact)
async def st_contact_by_contact(m: Message, state: FSMContext):
    phone = normalize_phone(m.contact.phone_number if m.contact else "")
    if not is_valid_phone(phone):
        return await m.answer("Отправь номер телефона 🙂", reply_markup=kb_request_phone())

    await state.update_data(contact=phone, media=[])
    await m.answer("Отправь фото/видео\nПотом нажми ✅ Завершить", reply_markup=kb_finish_media())
    await m.answer("⬇️", reply_markup=ReplyKeyboardRemove())
    await state.set_state(NewListing.media)

@user_router.message(NewListing.contact)
async def st_contact_manual(m: Message, state: FSMContext):
    phone = normalize_phone(m.text or "")
    if not is_valid_phone(phone):
        return await m.answer("Отправь номер телефона 🙂", reply_markup=kb_request_phone())

    await state.update_data(contact=phone, media=[])
    await m.answer("Отправь фото/видео\nПотом нажми ✅ Завершить", reply_markup=kb_finish_media())
    await m.answer("⬇️", reply_markup=ReplyKeyboardRemove())
    await state.set_state(NewListing.media)

@user_router.message(NewListing.media)
async def media_collect(m: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])

    if len(media) >= 10:
        return await m.answer("Максимум 10", reply_markup=kb_finish_media())

    if m.photo:
        media.append({"type": "photo", "file_id": m.photo[-1].file_id})
        await state.update_data(media=media)
        return await m.answer(f"✅ Добавлено ({len(media)}/10)", reply_markup=kb_finish_media())

    if m.video:
        media.append({"type": "video", "file_id": m.video.file_id})
        await state.update_data(media=media)
        return await m.answer(f"✅ Добавлено ({len(media)}/10)", reply_markup=kb_finish_media())

    await m.answer("Отправь фото/видео или нажми ✅ Завершить", reply_markup=kb_finish_media())

@user_router.callback_query(NewListing.media, F.data == "finish_media")
async def finish_media(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    media = data.get("media", [])
    if not media:
        return await cb.message.answer("Нужно хотя бы 1 фото/видео", reply_markup=kb_finish_media())

    district = data.get("district") or ""
    if not isinstance(district, str):
        district = str(district)

    public_caption = build_public_caption(
        title=data["title"],
        region=data["region"],
        city=data["city"],
        district=district,
        address=data["address"],
        freshness=data["freshness"],
        comment=data["comment"],
        price=fmt_sum(int(data["price"])),
        phone=data["contact"],
        user_username=cb.from_user.username,
    )
    await state.update_data(public_caption=public_caption, district=district)

    await cb.message.answer("Проверь объявление:\n\n" + public_caption, reply_markup=kb_confirm())
    await state.set_state(NewListing.confirm)

@user_router.callback_query(F.data == "send_to_review")
async def send_to_review(cb: CallbackQuery, state: FSMContext, db: DB, admin_ids: set[int]):
    await cb.answer()
    data = await state.get_data()

    # safety
    if data.get("district") is None:
        data["district"] = ""

    need = ["public_caption", "media", "price", "contact", "region", "city", "address", "freshness", "comment", "title"]
    if any(data.get(k) in (None, "") for k in ["public_caption", "price", "contact", "region", "city", "address", "freshness", "title"]):
        await cb.message.answer("Что-то сломалось. /start")
        await state.clear()
        return

    listing_id = await db.create_listing(
        user_id=cb.from_user.id,
        user_full_name=cb.from_user.full_name or "—",
        user_username=cb.from_user.username,
        data=data
    )
    await state.clear()

    # шлём админу медиа + инфо
    from .texts import build_admin_info
    admin_info = build_admin_info(
        user_full_name=cb.from_user.full_name or "—",
        user_username=cb.from_user.username,
        user_id=cb.from_user.id,
        phone=data["contact"]
    )

    for admin_id in admin_ids:
        try:
            group = build_media_group(data["media"])
            group[0].caption = f"Новая заявка ID {listing_id}\n\n{admin_info}\n\nПост в канал:\n{data['public_caption']}"
            group[0].parse_mode = "HTML"
            await cb.bot.send_media_group(chat_id=admin_id, media=group)
            # кнопки модерации отдельно
            from .keyboards import kb_admin_review
            await cb.bot.send_message(chat_id=admin_id, text=f"Модерация заявки ID {listing_id}:", reply_markup=kb_admin_review(listing_id))
        except:
            pass

    await cb.message.answer(f"✅ Заявка отправлена\nID: {listing_id}")