import json
import aiosqlite
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Listing:
    id: int
    user_id: int
    user_full_name: str
    user_username: Optional[str]
    status: str

    title: str
    region: str
    city: str
    district: str
    address: str

    freshness: str
    comment: str
    price: str
    contact: str

    media_json: str
    public_caption: str
    channel_first_message_id: Optional[int]

class DB:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS listings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              user_full_name TEXT NOT NULL,
              user_username TEXT,
              status TEXT NOT NULL,

              title TEXT NOT NULL,
              region TEXT NOT NULL,
              city TEXT NOT NULL,
              district TEXT NOT NULL,
              address TEXT NOT NULL,

              freshness TEXT NOT NULL,
              comment TEXT NOT NULL,
              price TEXT NOT NULL,
              contact TEXT NOT NULL,

              media_json TEXT NOT NULL,
              public_caption TEXT NOT NULL,

              channel_first_message_id INTEGER
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            """)
            await db.commit()

    async def set_setting(self, key: str, value: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
              INSERT INTO settings (key, value)
              VALUES (?, ?)
              ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, value))
            await db.commit()

    async def get_setting(self, key: str) -> Optional[str]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def set_examples(self, photo_file_ids: list[str]) -> None:
        await self.set_setting("examples_photo_ids", json.dumps(photo_file_ids, ensure_ascii=False))

    async def get_examples(self) -> list[str]:
        raw = await self.get_setting("examples_photo_ids")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data]
        except:
            pass
        return []

    async def create_listing(self, user_id: int, user_full_name: str, user_username: Optional[str], data: dict[str, Any]) -> int:
        district = data.get("district") or ""
        if not isinstance(district, str):
            district = str(district)
        district = district.strip()

        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("""
              INSERT INTO listings (
                user_id, user_full_name, user_username, status,
                title, region, city, district, address,
                freshness, comment, price, contact,
                media_json, public_caption, channel_first_message_id
              )
              VALUES (?, ?, ?, 'pending',
                      ?, ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, NULL)
            """, (
                user_id, user_full_name, user_username,
                data["title"],
                data["region"], data["city"], district, data["address"],
                data["freshness"], data["comment"], str(data["price"]), data["contact"],
                json.dumps(data["media"], ensure_ascii=False),
                data["public_caption"],
            ))
            await db.commit()
            return cur.lastrowid

    async def get_listing(self, listing_id: int) -> Optional[Listing]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM listings WHERE id=?", (listing_id,))
            row = await cur.fetchone()
            return Listing(**dict(row)) if row else None

    async def set_published(self, listing_id: int, first_msg_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
              UPDATE listings
              SET status='published', channel_first_message_id=?
              WHERE id=?
            """, (first_msg_id, listing_id))
            await db.commit()

    async def set_rejected(self, listing_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE listings SET status='rejected' WHERE id=?", (listing_id,))
            await db.commit()

    async def set_sold(self, listing_id: int, new_public_caption: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
              UPDATE listings
              SET status='sold', public_caption=?
              WHERE id=?
            """, (new_public_caption, listing_id))
            await db.commit()