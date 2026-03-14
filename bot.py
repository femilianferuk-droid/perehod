import os
import json
import logging
import asyncio
import subprocess
import sys
import shutil
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# НЕТ ИМПОРТА dotenv - токен только из окружений!

# --- НАСТРОЙКИ ГЛАВНОГО БОТА-КОНСТРУКТОРА ---
# Берем токен ТОЛЬКО из переменных окружения
MAIN_BOT_TOKEN = os.environ.get("MAIN_BOT_TOKEN")
if not MAIN_BOT_TOKEN:
    raise ValueError(
        "❌ ОШИБКА: Не найден MAIN_BOT_TOKEN в переменных окружения!\n"
        "Добавь переменную окружения MAIN_BOT_TOKEN в панели управления хостингом."
    )

# ФИКСИРОВАННЫЙ РЕФЕРАЛЬНЫЙ КОД
FIXED_REFERRAL_CODE = "ref_7973988177"
MAX_BOTS = 50  # Максимальное количество ботов
BOTS_FOLDER = "created_bots"
TEMPLATE_FILE = "bot_template.py"

# Создаем папки
os.makedirs(BOTS_FOLDER, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация главного бота
bot = Bot(token=MAIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для FSM
class CreateBotStates(StatesGroup):
    waiting_for_token = State()
    waiting_for_name = State()

# Класс для управления созданными ботами
class BotManager:
    def __init__(self):
        self.bots_file = os.path.join(BOTS_FOLDER, "bots_registry.json")
        self.load_bots()
    
    def load_bots(self):
        """Загружает реестр ботов"""
        if os.path.exists(self.bots_file):
            with open(self.bots_file, "r", encoding="utf-8") as f:
                self.bots = json.load(f)
        else:
            self.bots = []
    
    def save_bots(self):
        """Сохраняет реестр ботов"""
        with open(self.bots_file, "w", encoding="utf-8") as f:
            json.dump(self.bots, f, indent=2, ensure_ascii=False)
    
    def can_create_bot(self) -> bool:
        """Проверяет, можно ли создать нового бота"""
        return len(self.bots) < MAX_BOTS
    
    def get_bot_count(self) -> int:
        """Возвращает количество созданных ботов"""
        return len(self.bots)
    
    def add_bot(self, bot_data: dict):
        """Добавляет бота в реестр"""
        self.bots.append(bot_data)
        self.save_bots()
    
    def remove_bot(self, bot_id: str):
        """Удаляет бота из реестра"""
        self.bots = [b for b in self.bots if b["id"] != bot_id]
        self.save_bots()
    
    def get_bot(self, bot_id: str) -> dict:
        """Возвращает данные бота по ID"""
        for bot in self.bots:
            if bot["id"] == bot_id:
                return bot
        return None
    
    def update_bot_status(self, bot_id: str, status: str):
        """Обновляет статус бота"""
        for bot in self.bots:
            if bot["id"] == bot_id:
                bot["status"] = status
                bot["updated_at"] = datetime.now().isoformat()
                break
        self.save_bots()

# Создаем шаблон бота
def create_bot_template():
    """Создает шаблонный файл бота"""
    
    template = f'''import os
import logging
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# НЕТ ИМПОРТА dotenv - токен только из окружений!

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Нет BOT_TOKEN в переменных окружения!")

# ФИКСИРОВАННЫЙ РЕФЕРАЛЬНЫЙ КОД (нельзя изменить)
REFERRAL_CODE = "{FIXED_REFERRAL_CODE}"
BOT_NAME = os.environ.get("BOT_NAME", "Casino Bot")
TARGET_BOT_USERNAME = "AntiCasino_Robot"
REFERRAL_LINK = f"https://t.me/{{TARGET_BOT_USERNAME}}?start={{REFERRAL_CODE}}"
REFERRAL_BONUS = "0.1$"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s'
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
🎰 <b>{{BOT_NAME}}</b> 🎰

Привет, <b>{{user_name}}</b>! ✨

🎲 Лучшие игры
💎 Моментальные выплаты
🎁 Бонусы каждый день

💰 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>
👉 За каждого друга: <b>{{REFERRAL_BONUS}}</b>
🚀 Выплаты мгновенные

👇 Нажми на кнопку чтобы начать:
"""
    return welcome_text

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    
    logger.info(f"Новый пользователь: {{user_name}} (ID: {{user_id}})")
    
    await message.answer(
        get_welcome_text(user_name).replace("{{user_name}}", user_name).replace("{{BOT_NAME}}", BOT_NAME).replace("{{REFERRAL_BONUS}}", REFERRAL_BONUS),
        reply_markup=create_main_keyboard(),
        parse_mode="HTML"
    )
    
    greetings = [
        "🎰 Удачи в игре!",
        "💫 Пусть фортуна улыбнется!",
        "⭐ Джекпот ждет тебя!",
        "🍀 Ни пуха ни пера!"
    ]
    await message.answer(random.choice(greetings))

@dp.message(Command("ref"))
async def cmd_ref(message: types.Message):
    """Обработчик команды /ref"""
    
    ref_text = f"""
👥 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>

💰 За каждого друга: <b>{{REFERRAL_BONUS}}</b>
🔄 Неограниченно приглашений

🔗 <b>Твоя ссылка:</b>
<code>{{REFERRAL_LINK}}</code>
"""
    
    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="📢 ПОДЕЛИТЬСЯ",
                url=f"https://t.me/share/url?url={{REFERRAL_LINK}}&text=🎰 Заходи в {{BOT_NAME}}! За каждого друга платят {{REFERRAL_BONUS}}! 🚀"
            )
        ]]
    )
    
    await message.answer(
        ref_text.replace("{{REFERRAL_BONUS}}", REFERRAL_BONUS).replace("{{REFERRAL_LINK}}", REFERRAL_LINK).replace("{{BOT_NAME}}", BOT_NAME),
        reply_markup=share_keyboard,
        parse_mode="HTML"
    )

@dp.message()
async def handle_unknown(message: types.Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "❓ Не понял команду...\\n"
        "Используй /start для меню.",
        reply_markup=create_main_keyboard()
    )

async def main():
    """Запуск бота"""
    print(f"\\n🎰 {{BOT_NAME}}")
    print("="*50)
    print(f"✅ Бот запущен!")
    print(f"💰 Бонус за реферала: {{REFERRAL_BONUS}}")
    print(f"🔗 Реферальная ссылка: {{REFERRAL_LINK}}")
    print("="*50 + "\\n")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        f.write(template)

# Создаем шаблон
create_bot_template()

# Инициализируем менеджер ботов
bot_manager = BotManager()

def create_bot_files(token: str, name: str, owner_id: int) -> dict:
    """Создает файлы нового бота с ФИКСИРОВАННЫМ реферальным кодом"""
    
    # Генерируем уникальный ID для бота
    bot_id = f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{owner_id}"
    bot_folder = os.path.join(BOTS_FOLDER, bot_id)
    os.makedirs(bot_folder, exist_ok=True)
    
    # НЕ создаем .env файл! Вместо этого создаем скрипт запуска с экспортом переменных
    
    # Копируем шаблон бота (в нем уже фиксированный реферальный код)
    shutil.copy(TEMPLATE_FILE, os.path.join(bot_folder, "bot.py"))
    
    # Создаем requirements.txt
    requirements = """aiogram==3.4.1
# python-dotenv НЕ НУЖЕН!
"""
    with open(os.path.join(bot_folder, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(requirements)
    
    # Создаем скрипт для запуска с переменными окружения
    if sys.platform == "win32":
        # Windows
        run_script = f'''@echo off
set BOT_TOKEN={token}
set BOT_NAME={name}
python bot.py
'''
        script_name = "run.bat"
    else:
        # Linux/Mac
        run_script = f'''#!/bin/bash
export BOT_TOKEN="{token}"
export BOT_NAME="{name}"
python3 bot.py
'''
        script_name = "run.sh"
    
    with open(os.path.join(bot_folder, script_name), "w", encoding="utf-8") as f:
        f.write(run_script)
    
    if sys.platform != "win32":
        os.chmod(os.path.join(bot_folder, script_name), 0o755)
    
    # Создаем информацию о боте
    bot_info = {
        "id": bot_id,
        "token": token[-10:],  # Сохраняем только последние 10 символов токена для безопасности
        "name": name,
        "referral_code": FIXED_REFERRAL_CODE,  # Всегда фиксированный код
        "owner_id": owner_id,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "folder": bot_folder,
        "script": script_name
    }
    
    # Сохраняем информацию
    with open(os.path.join(bot_folder, "info.json"), "w", encoding="utf-8") as f:
        json.dump(bot_info, f, indent=2, ensure_ascii=False)
    
    return bot_info

def install_and_start_bot(bot_folder: str) -> bool:
    """Устанавливает зависимости и запускает бота"""
    try:
        # Создаем виртуальное окружение и устанавливаем зависимости
        if sys.platform == "win32":
            # Windows
            subprocess.run(f'cd /d "{bot_folder}" && python -m venv venv', shell=True, check=True)
            subprocess.run(f'cd /d "{bot_folder}" && venv\\Scripts\\python -m pip install -r requirements.txt', shell=True, check=True)
            
            # Запускаем бота через run.bat
            bat_path = os.path.join(bot_folder, "run.bat")
            subprocess.Popen(['start', 'cmd', '/c', bat_path], shell=True)
        else:
            # Linux/Mac
            subprocess.run(f'cd "{bot_folder}" && python3 -m venv venv', shell=True, check=True)
            subprocess.run(f'cd "{bot_folder}" && venv/bin/pip install -r requirements.txt', shell=True, check=True)
            
            # Запускаем в screen с использованием run.sh
            script_path = os.path.join(bot_folder, "run.sh")
            subprocess.Popen(['screen', '-dmS', f'bot_{os.path.basename(bot_folder)}', 'bash', '-c', f'cd "{bot_folder}" && ./run.sh'])
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return False

# Клавиатуры
def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ СОЗДАТЬ БОТА", callback_data="create_bot")],
            [InlineKeyboardButton(text="📋 МОИ БОТЫ", callback_data="my_bots")],
            [InlineKeyboardButton(text="ℹ️ ПОМОЩЬ", callback_data="help")]
        ]
    )
    return keyboard

def get_back_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back_to_main")]
        ]
    )
    return keyboard

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name
    
    welcome_text = f"""
🎰 <b>КОНСТРУКТОР БОТОВ-КАЗИНО</b> 🎰

Привет, <b>{user_name}</b>! ✨

Я помогаю создавать ботов для @AntiCasino_Robot.
Все боты используют ТВОЙ реферальный код:
<code>{FIXED_REFERRAL_CODE}</code>

<b>📊 Статистика:</b>
• Создано ботов: {bot_manager.get_bot_count()}/{MAX_BOTS}
• Доступно мест: {MAX_BOTS - bot_manager.get_bot_count()}

<b>💰 Твой доход:</b>
• За каждого реферала: 0.1$
• Все рефералы идут на твой код

👇 Выбери действие:
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data == "help")
async def show_help(callback: types.CallbackQuery):
    """Показывает справку"""
    
    help_text = f"""
ℹ️ <b>Как пользоваться конструктором:</b>

1️⃣ <b>Создать бота</b>
   • Нажми «✨ Создать бота»
   • Отправь токен от @BotFather
   • Укажи название бота
   • Бот создастся автоматически

2️⃣ <b>Реферальный код</b>
   • Код ФИКСИРОВАННЫЙ: <code>{FIXED_REFERRAL_CODE}</code>
   • Все созданные боты используют его
   • Все рефералы идут на этот код

3️⃣ <b>Управление ботами</b>
   • Просмотр списка ботов
   • Запуск/остановка
   • Удаление

<b>💰 Заработок:</b>
• За каждого реферала: 0.1$
• Чем больше ботов, тем больше доход
"""
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# [Все остальные обработчики без изменений]
# ... (create_bot_start, process_token, process_name, show_my_bots, show_bot_info, 
#      start_bot_command, stop_bot_command, delete_bot_command, handle_unknown)

# Для экономии места я не копирую все обработчики, 
# но они остаются точно такими же как в предыдущем ответе

async def main():
    """Запуск главного бота-конструктора"""
    print("\n" + "="*60)
    print("🎰 КОНСТРУКТОР БОТОВ-КАЗИНО")
    print("="*60)
    print(f"✅ Главный бот запущен!")
    print(f"🔗 Реферальный код: {FIXED_REFERRAL_CODE}")
    print(f"📊 Максимум ботов: {MAX_BOTS}")
    print("="*60 + "\n")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
