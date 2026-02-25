import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from .db import DB
from .utils import build_media_group
from .keyboards import kb_user_sold
from .texts import mark_sold_caption

admin_router = Router()

def is_admin(user_id: int, admin_ids: set[int]) -> bool:
    return user_id in admin_ids

@admin_router.message(Command("set_examples"))
async def cmd_set_examples(m: Message, db: DB, admin_ids: set[int]):
    if not is_admin(m.from_user.id, admin_ids):
        return
    await m.answer("Скинь 3 фото примера (по одному сообщению). Я сохраню последние 3.")

@admin_router.message(F.photo)
async def catch_examples(m: Message, db: DB, admin_ids: set[int]):
    if not is_admin(m.from_user.id, admin_ids):
        return
    # сохраняем последние 3 file_id
    raw = await db.get_setting("examples_buffer") or "[]"
    try:
        buf = json.loads(raw)
        if not isinstance(buf, list):
            buf = []
    except:
        buf = []
    buf.append(m.photo[-1].file_id)
    buf = buf[-3:]
    await db.set_setting("examples_buffer", json.dumps(buf, ensure_ascii=False))

    if len(buf) < 3:
        await m.answer(f"Ок, принято ({len(buf)}/3)")
        return

    await db.set_examples(buf)
    await db.set_setting("examples_buffer", "[]")
    await m.answer("✅ Примеры сохранены. Теперь /start будет показывать 3 фото.")

@admin_router.callback_query(F.data.startswith("admin_publish:"))
async def admin_publish(cb: CallbackQuery, db: DB, admin_ids: set[int], channel_id: int):
    if not is_admin(cb.from_user.id, admin_ids):
        return await cb.answer("Нет доступа", show_alert=True)

    await cb.answer()
    listing_id = int(cb.data.split(":", 1)[1])
    listing = await db.get_listing(listing_id)
    if not listing:
        return await cb.message.answer("Не найдено")

    media_items = json.loads(listing.media_json)
    group = build_media_group(media_items)
    group[0].caption = listing.public_caption
    group[0].parse_mode = "HTML"

    msgs = await cb.bot.send_media_group(chat_id=channel_id, media=group)
    first_id = msgs[0].message_id if msgs else None

    if first_id:
        await db.set_published(listing_id, first_id)

    # продавцу в ЛС кнопка "Продано"
    try:
        await cb.bot.send_message(
            chat_id=listing.user_id,
            text=f"✅ Твоё объявление опубликовано (ID {listing_id}).\nКогда продашь — жми кнопку:",
            reply_markup=kb_user_sold(listing_id)
        )
    except:
        pass

    await cb.message.answer("✅ Опубликовано")

@admin_router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(cb: CallbackQuery, db: DB, admin_ids: set[int]):
    if not is_admin(cb.from_user.id, admin_ids):
        return await cb.answer("Нет доступа", show_alert=True)

    await cb.answer()
    listing_id = int(cb.data.split(":", 1)[1])
    listing = await db.get_listing(listing_id)
    if not listing:
        return await cb.message.answer("Не найдено")

    await db.set_rejected(listing_id)

    try:
        await cb.bot.send_message(chat_id=listing.user_id, text=f"❌ Заявка отклонена (ID {listing_id}).")
    except:
        pass

    await cb.message.answer("Отклонено")

@admin_router.callback_query(F.data.startswith("user_sold:"))
async def user_sold(cb: CallbackQuery, db: DB, admin_ids: set[int], channel_id: int):
    await cb.answer()
    listing_id = int(cb.data.split(":", 1)[1])
    listing = await db.get_listing(listing_id)
    if not listing:
        return await cb.message.answer("Не найдено")

    # только владелец или админ
    if cb.from_user.id != listing.user_id and cb.from_user.id not in admin_ids:
        return await cb.message.answer("Это не твоё объявление 🙂")

    new_caption = mark_sold_caption(listing.public_caption)
    await db.set_sold(listing_id, new_caption)

    # редактируем подпись в канале (первое сообщение медиагруппы)
    if listing.channel_first_message_id:
        try:
            await cb.bot.edit_message_caption(
                chat_id=channel_id,
                message_id=listing.channel_first_message_id,
                caption=new_caption,
                parse_mode="HTML"
            )
        except:
            pass

    await cb.message.answer("✅ Отмечено как ПРОДАНО!")