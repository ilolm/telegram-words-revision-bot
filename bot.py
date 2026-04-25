import asyncio
from datetime import datetime, date, time, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import aiosqlite
import os

API_TOKEN = os.environ.get("TG_BOT_TOKEN")

INTERVALS = [1, 4, 11, 23, 53]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "words.db")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- KEYBOARD ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить кучку")],
        [KeyboardButton(text="📚 Сегодня повторить")],
        [KeyboardButton(text="📦 Все кучки")],
        [KeyboardButton(text="🗑 Удалить кучку")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)


# --- FSM ---
class AddDeck(StatesGroup):
    waiting_name = State()


# --- DB ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            created_at TEXT
        )
        """)
        await db.commit()


# --- START ---
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Привет! Выбери действие:", reply_markup=main_kb)


# --- ADD ---
@dp.message(F.text == "➕ Добавить кучку")
async def add_start(message: Message, state: FSMContext):
    await state.set_state(AddDeck.waiting_name)
    await message.answer("Напиши название кучки:")


@dp.message(AddDeck.waiting_name)
async def add_finish(message: Message, state: FSMContext):
    name = message.text

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO decks (user_id, name, created_at) VALUES (?, ?, ?)",
            (message.from_user.id, name, date.today().isoformat())
        )
        await db.commit()

    await state.clear()
    await message.answer(f"✅ Добавлено: {name}", reply_markup=main_kb)


# --- TODAY ---
@dp.message(F.text == "📚 Сегодня повторить")
async def today_reviews(message: Message):
    user_id = message.from_user.id
    today = date.today()

    result = []

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name, created_at FROM decks WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            async for name, created_at in cursor:
                created_date = datetime.fromisoformat(created_at).date()
                days_passed = (today - created_date).days

                if days_passed in INTERVALS:
                    result.append(f"📌 {name} — {created_at}   (день {days_passed})")

    if not result:
        await message.answer("🎉 Сегодня ничего повторять не нужно", reply_markup=main_kb)
    else:
        await message.answer(
            "📚 Сегодня повторить:\n\n" + "\n".join(result),
            reply_markup=main_kb
        )


# --- LIST ---
@dp.message(F.text == "📦 Все кучки")
async def list_decks(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name, created_at FROM decks WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("Пока пусто", reply_markup=main_kb)
        return

    text = "\n".join([f"📌 {name} — {created}" for name, created in rows])
    await message.answer("📦 Кучки:\n\n" + text, reply_markup=main_kb)


# --- DELETE MENU ---
@dp.message(F.text == "🗑 Удалить кучку")
async def delete_menu(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name FROM decks WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("❌ Нет кучек для удаления", reply_markup=main_kb)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"📌 {name}",
                callback_data=f"delete:{deck_id}"
            )]
            for deck_id, name in rows
        ]
    )

    await message.answer("Выбери кучку для удаления:", reply_markup=keyboard)


# --- DELETE ACTION ---
@dp.callback_query(F.data.startswith("delete:"))
async def delete_deck(callback: CallbackQuery):
    deck_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM decks WHERE id = ? AND user_id = ?",
            (deck_id, user_id)
        )
        await db.commit()

    await callback.message.edit_text("🗑 Кучка удалена")
    await callback.answer()


# --- HELP ---
@dp.message(F.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer(
        "Как пользоваться:\n\n"
        "1. Добавляешь кучку слов\n"
        "2. Каждый день жмёшь 'Сегодня повторить'\n\n"
        "Интервалы:\n1, 3, 7, 12, 30 дней",
        reply_markup=main_kb
    )


# --- REMINDER ---
async def send_daily_reminders():
    while True:
        now = datetime.now()
        target = datetime.combine(date.today(), time(10, 0))

        if now >= target:
            target = target + timedelta(days=1)

        await asyncio.sleep((target - now).total_seconds())

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT DISTINCT user_id FROM decks"
            ) as cursor:
                users = await cursor.fetchall()

        for (user_id,) in users:
            today = date.today()
            result = []

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    "SELECT name, created_at FROM decks WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    async for name, created_at in cursor:
                        created_date = datetime.fromisoformat(created_at).date()
                        days_passed = (today - created_date).days

                        if days_passed in INTERVALS:
                            result.append(f"📌 {name} (день {days_passed})")

            if result:
                try:
                    await bot.send_message(
                        user_id,
                        "⏰ Напоминание!\n\n📚 Сегодня повторить:\n\n" + "\n".join(result)
                    )
                except:
                    pass


# --- MAIN ---
async def main():
    await init_db()

    asyncio.create_task(send_daily_reminders())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
