import os
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import asyncio

# Загружаем переменные окружения
load_dotenv()

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Нет BOT_TOKEN в переменных окружения!")

REFERRAL_CODE = os.getenv("REFERRAL_CODE", "ref_7973988177")
TARGET_BOT_USERNAME = "AntiCasino_Robot"
REFERRAL_LINK = f"https://t.me/{TARGET_BOT_USERNAME}?start={REFERRAL_CODE}"
REFERRAL_BONUS = "0.1$"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def create_main_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками-ссылками"""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🎲 ИГРАТЬ СЕЙЧАС", 
        url=REFERRAL_LINK
    ))
    
    builder.row(
        InlineKeyboardButton(
            text="👤 ПРОФИЛЬ", 
            url=REFERRAL_LINK
        ),
        InlineKeyboardButton(
            text="👥 РЕФЕРАЛЫ", 
            url=REFERRAL_LINK
        )
    )
    
    return builder.as_markup()

def get_welcome_text(user_name: str) -> str:
    """Формирует красивое приветствие"""
    
    welcome_text = f"""
🎰 <b>ANTI CASINO</b> 🎰

Привет, <b>{user_name}</b>! ✨

🎲 Лучшие игры
💎 Моментальные выплаты
🎁 Бонусы каждый день

💰 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>
👉 За каждого друга: <b>{REFERRAL_BONUS}</b>
🚀 Выплаты мгновенные

👇 Нажми на кнопку чтобы начать:
"""
    return welcome_text

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    
    logger.info(f"Новый пользователь: {user_name} (ID: {user_id})")
    
    # Отправляем красивое приветствие с HTML разметкой
    await message.answer(
        get_welcome_text(user_name),
        reply_markup=create_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Случайное пожелание удачи
    greetings = [
        "🎰 Удачи в игре!",
        "💫 Пусть фортуна улыбнется!",
        "⭐ Джекпот ждет тебя!",
        "🍀 Ни пуха ни пера!",
        "🔥 Сорви куш!",
        "💎 Богатство близко!"
    ]
    await message.answer(random.choice(greetings))

@dp.message(Command("ref"))
async def cmd_ref(message: types.Message):
    """Обработчик команды /ref - подробнее о рефералах"""
    
    ref_text = f"""
👥 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>

💰 Зарабатывай приглашая друзей в казино!

🎁 За каждого друга: <b>{REFERRAL_BONUS}</b>
🔄 Неограниченно приглашений
💸 Выплаты сразу на карту

🔗 <b>Твоя реферальная ссылка:</b>
<code>{REFERRAL_LINK}</code>

📤 Отправь друзьям и получай бонусы за каждого!
"""
    
    # Кнопка для быстрого шаринга ссылки
    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="📢 ПОДЕЛИТЬСЯ ССЫЛКОЙ",
                url=f"https://t.me/share/url?url={REFERRAL_LINK}&text=🎰 Заходи в ANTI CASINO! Получай бонусы и выигрывай! За каждого друга платят {REFERRAL_BONUS}! 🚀"
            )
        ]]
    )
    
    await message.answer(
        ref_text,
        reply_markup=share_keyboard,
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам"""
    help_text = """
ℹ️ <b>Доступные команды:</b>

/start - Главное меню
/ref - Реферальная система
/help - Эта справка

👇 Используй кнопки ниже для навигации
"""
    await message.answer(
        help_text,
        reply_markup=create_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message()
async def handle_unknown(message: types.Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "❓ Не понял команду...\n"
        "Используй /help для списка команд.",
        reply_markup=create_main_keyboard()
    )

async def on_startup():
    """Действия при запуске бота"""
    print("\n" + "="*50)
    print("🎰 ANTI CASINO BOT")
    print("="*50)
    print(f"✅ Бот успешно запущен!")
    print(f"💰 Бонус за реферала: {REFERRAL_BONUS}")
    print(f"🔗 Реферальная ссылка: {REFERRAL_LINK}")
    print("="*50 + "\n")

async def main():
    """Запуск бота"""
    await on_startup()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
