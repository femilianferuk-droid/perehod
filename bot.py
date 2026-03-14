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
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# --- НАСТРОЙКИ ГЛАВНОГО БОТА-КОНСТРУКТОРА ---
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
if not MAIN_BOT_TOKEN:
    raise ValueError("Нет MAIN_BOT_TOKEN в переменных окружения!")

# ФИКСИРОВАННЫЙ РЕФЕРАЛЬНЫЙ КОД - ЕГО НЕЛЬЗЯ ИЗМЕНИТЬ
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
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Нет BOT_TOKEN в переменных окружения!")

# ФИКСИРОВАННЫЙ РЕФЕРАЛЬНЫЙ КОД (нельзя изменить)
REFERRAL_CODE = "{FIXED_REFERRAL_CODE}"
BOT_NAME = os.getenv("BOT_NAME", "Casino Bot")
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
    
    # Создаем .env файл (только токен и имя, реферальный код фиксирован в шаблоне)
    env_content = f"""BOT_TOKEN={token}
BOT_NAME={name}
"""
    with open(os.path.join(bot_folder, ".env"), "w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Копируем шаблон бота (в нем уже фиксированный реферальный код)
    shutil.copy(TEMPLATE_FILE, os.path.join(bot_folder, "bot.py"))
    
    # Создаем requirements.txt
    requirements = """aiogram==3.4.1
python-dotenv==1.0.0
"""
    with open(os.path.join(bot_folder, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(requirements)
    
    # Создаем информацию о боте
    bot_info = {
        "id": bot_id,
        "token": token[-10:],  # Сохраняем только последние 10 символов токена для безопасности
        "name": name,
        "referral_code": FIXED_REFERRAL_CODE,  # Всегда фиксированный код
        "owner_id": owner_id,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "folder": bot_folder
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
            
            # Запускаем бота
            bat_content = f'''@echo off
cd /d "{bot_folder}"
call venv\\Scripts\\activate
python bot.py
'''
            bat_path = os.path.join(bot_folder, "start.bat")
            with open(bat_path, "w") as f:
                f.write(bat_content)
            
            # Запускаем в скрытом окне
            subprocess.Popen(['start', 'cmd', '/c', bat_path], shell=True)
        else:
            # Linux/Mac
            subprocess.run(f'cd "{bot_folder}" && python3 -m venv venv', shell=True, check=True)
            subprocess.run(f'cd "{bot_folder}" && venv/bin/pip install -r requirements.txt', shell=True, check=True)
            
            # Запускаем в screen
            subprocess.Popen(['screen', '-dmS', f'bot_{os.path.basename(bot_folder)}', 'bash', '-c', f'cd "{bot_folder}" && venv/bin/python bot.py'])
        
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

Я помогу тебе создать своего Telegram бота для казино.
Каждый бот будет направлять игроков в @AntiCasino_Robot с реферальным кодом:
<code>{FIXED_REFERRAL_CODE}</code>

<b>📊 Статистика:</b>
• Создано ботов: {bot_manager.get_bot_count()}/{MAX_BOTS}
• Доступно мест: {MAX_BOTS - bot_manager.get_bot_count()}

<b>💰 Твой доход:</b>
• За каждого реферала: 0.1$
• Все рефералы приходят на твой код

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

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    user_name = callback.from_user.first_name
    
    welcome_text = f"""
🎰 <b>КОНСТРУКТОР БОТОВ-КАЗИНО</b> 🎰

Привет, <b>{user_name}</b>! ✨

<b>📊 Статистика:</b>
• Создано ботов: {bot_manager.get_bot_count()}/{MAX_BOTS}
• Доступно мест: {MAX_BOTS - bot_manager.get_bot_count()}

<b>💰 Твой доход:</b>
• За каждого реферала: 0.1$
• Реферальный код: <code>{FIXED_REFERRAL_CODE}</code>
"""
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "create_bot")
async def create_bot_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания бота"""
    
    # Проверяем лимит
    if not bot_manager.can_create_bot():
        await callback.message.edit_text(
            "❌ <b>Достигнут лимит ботов!</b>\n\n"
            f"Максимальное количество ботов: {MAX_BOTS}\n"
            "Удали одного из существующих ботов, чтобы создать нового.\n\n"
            f"📊 Текущее количество: {bot_manager.get_bot_count()}/{MAX_BOTS}",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🔑 <b>Создание нового бота</b>\n\n"
        "Отправь мне <b>токен</b> твоего нового бота.\n\n"
        "📌 <b>Важно:</b>\n"
        f"• Реферальный код будет ФИКСИРОВАННЫМ: <code>{FIXED_REFERRAL_CODE}</code>\n"
        "• Все рефералы пойдут на этот код\n\n"
        "Где взять токен?\n"
        "1. Напиши @BotFather в Telegram\n"
        "2. Создай нового бота командой /newbot\n"
        "3. Скопируй полученный токен\n\n"
        "Пример токена:\n"
        "<code>7685321845:AAHdqTcvCH1vGWJxfSeofSAs0K5PALbSAu</code>",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(CreateBotStates.waiting_for_token)
    await callback.answer()

@dp.message(CreateBotStates.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    """Обработка введенного токена"""
    
    token = message.text.strip()
    
    # Простая проверка токена
    if len(token) < 40 or ':' not in token:
        await message.answer(
            "❌ <b>Неверный формат токена!</b>\n\n"
            "Токен должен выглядеть так:\n"
            "<code>7685321845:AAHdqTcvCH1vGWJxfSeofSAs0K5PALbSAu</code>\n\n"
            "Попробуй еще раз:",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(token=token)
    
    await message.answer(
        "📝 <b>Название бота</b>\n\n"
        "Отправь <b>название</b> для твоего бота.\n\n"
        "Примеры:\n"
        "• Casino King\n"
        "• Golden Casino\n"
        "• Lucky Bot\n\n"
        "Это имя будет отображаться в приветствии.\n\n"
        f"⚡ Реферальный код: <code>{FIXED_REFERRAL_CODE}</code> (фиксированный)",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(CreateBotStates.waiting_for_name)

@dp.message(CreateBotStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка введенного названия"""
    
    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "❌ Название должно быть от 2 до 50 символов.\n"
            "Попробуй еще раз:",
            reply_markup=get_back_keyboard()
        )
        return
    
    data = await state.get_data()
    token = data['token']
    owner_id = message.from_user.id
    
    # Отправляем сообщение о начале создания
    progress_msg = await message.answer(
        "⏳ <b>Создаю бота...</b>\n\n"
        "🔄 Устанавливаю зависимости...",
        parse_mode="HTML"
    )
    
    try:
        # Создаем файлы бота с ФИКСИРОВАННЫМ реферальным кодом
        bot_info = create_bot_files(token, name, owner_id)
        
        # Устанавливаем и запускаем
        await progress_msg.edit_text(
            "⏳ <b>Создаю бота...</b>\n\n"
            "✅ Файлы созданы\n"
            "🔄 Запускаю бота...",
            parse_mode="HTML"
        )
        
        success = install_and_start_bot(bot_info['folder'])
        
        if success:
            bot_info['status'] = 'running'
            bot_manager.add_bot(bot_info)
            
            await progress_msg.edit_text(
                f"✅ <b>Бот успешно создан и запущен!</b>\n\n"
                f"🤖 <b>Название:</b> {name}\n"
                f"🔗 <b>Реферальный код:</b> <code>{FIXED_REFERRAL_CODE}</code>\n"
                f"💰 <b>Бонус:</b> 0.1$ за реферала\n"
                f"📊 <b>Всего ботов:</b> {bot_manager.get_bot_count()}/{MAX_BOTS}\n\n"
                f"Теперь твой бот работает и направляет игроков на твой реферальный код!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            bot_info['status'] = 'error'
            bot_manager.add_bot(bot_info)
            
            await progress_msg.edit_text(
                f"❌ <b>Ошибка при запуске бота</b>\n\n"
                f"Файлы созданы, но не удалось запустить бота.\n"
                f"Попробуй запустить его вручную из папки:\n"
                f"<code>{bot_info['folder']}</code>\n\n"
                f"Или удали бота и создай заново.",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        await progress_msg.edit_text(
            f"❌ <b>Ошибка:</b>\n<code>{str(e)}</code>\n\n"
            f"Попробуй еще раз или обратись к администратору.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()

@dp.callback_query(lambda c: c.data == "my_bots")
async def show_my_bots(callback: types.CallbackQuery):
    """Показывает список ботов пользователя"""
    
    user_id = callback.from_user.id
    user_bots = [b for b in bot_manager.bots if b['owner_id'] == user_id]
    
    if not user_bots:
        await callback.message.edit_text(
            "📋 <b>У тебя пока нет созданных ботов</b>\n\n"
            "Нажми «✨ Создать бота», чтобы создать своего первого бота!\n\n"
            f"📊 Всего создано: {bot_manager.get_bot_count()}/{MAX_BOTS}",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Создаем клавиатуру со списком ботов
    keyboard = []
    for bot in user_bots:
        status_emoji = "🟢" if bot['status'] == 'running' else "🔴" if bot['status'] == 'stopped' else "🟡"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {bot['name']}",
                callback_data=f"bot_info_{bot['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back_to_main")])
    
    await callback.message.edit_text(
        f"📋 <b>Твои боты ({len(user_bots)})</b>\n\n"
        f"📊 Всего создано: {bot_manager.get_bot_count()}/{MAX_BOTS}\n"
        f"💰 Реферальный код: <code>{FIXED_REFERRAL_CODE}</code>\n\n"
        f"Статусы:\n"
        f"🟢 - Работает\n"
        f"🟡 - Создан\n"
        f"🔴 - Остановлен",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("bot_info_"))
async def show_bot_info(callback: types.CallbackQuery):
    """Показывает информацию о конкретном боте"""
    
    bot_id = callback.data.replace("bot_info_", "")
    bot_info = bot_manager.get_bot(bot_id)
    
    if not bot_info:
        await callback.message.edit_text(
            "❌ Бот не найден!",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    status_text = {
        'running': '🟢 Работает',
        'stopped': '🔴 Остановлен',
        'created': '🟡 Создан',
        'error': '❌ Ошибка'
    }.get(bot_info['status'], '❓ Неизвестно')
    
    info_text = f"""
🤖 <b>{bot_info['name']}</b>

📊 <b>Статус:</b> {status_text}
🔗 <b>Реферальный код:</b> <code>{FIXED_REFERRAL_CODE}</code>
💰 <b>Бонус:</b> 0.1$ за реферала
📅 <b>Создан:</b> {bot_info['created_at'][:19].replace('T', ' ')}
"""
    
    keyboard = []
    
    if bot_info['status'] == 'running':
        keyboard.append([InlineKeyboardButton(text="⏹️ Остановить", callback_data=f"stop_bot_{bot_id}")])
    elif bot_info['status'] in ['stopped', 'created', 'error']:
        keyboard.append([InlineKeyboardButton(text="▶️ Запустить", callback_data=f"start_bot_{bot_id}")])
    
    keyboard.append([InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_bot_{bot_id}")])
    keyboard.append([InlineKeyboardButton(text="◀️ К списку", callback_data="my_bots")])
    
    await callback.message.edit_text(
        info_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("start_bot_"))
async def start_bot_command(callback: types.CallbackQuery):
    """Запускает бота"""
    
    bot_id = callback.data.replace("start_bot_", "")
    bot_info = bot_manager.get_bot(bot_id)
    
    if not bot_info:
        await callback.answer("❌ Бот не найден!")
        return
    
    await callback.message.edit_text(
        f"⏳ Запускаю бота {bot_info['name']}...",
        reply_markup=None
    )
    
    success = install_and_start_bot(bot_info['folder'])
    
    if success:
        bot_manager.update_bot_status(bot_id, 'running')
        await callback.message.edit_text(
            f"✅ Бот {bot_info['name']} успешно запущен!\n\n"
            f"🔗 Реферальный код: <code>{FIXED_REFERRAL_CODE}</code>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="◀️ НАЗАД", callback_data="my_bots")
                ]]
            ),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ Не удалось запустить бота {bot_info['name']}\n"
            f"Попробуй запустить вручную из папки:\n"
            f"<code>{bot_info['folder']}</code>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="◀️ НАЗАД", callback_data="my_bots")
                ]]
            ),
            parse_mode="HTML"
        )
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("stop_bot_"))
async def stop_bot_command(callback: types.CallbackQuery):
    """Останавливает бота"""
    
    bot_id = callback.data.replace("stop_bot_", "")
    bot_info = bot_manager.get_bot(bot_id)
    
    if not bot_info:
        await callback.answer("❌ Бот не найден!")
        return
    
    # Просто обновляем статус
    bot_manager.update_bot_status(bot_id, 'stopped')
    
    await callback.message.edit_text(
        f"⏹️ Бот {bot_info['name']} остановлен\n\n"
        f"Статус обновлен. Чтобы снова запустить, нажми «▶️ Запустить»",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="◀️ НАЗАД", callback_data="my_bots")
            ]]
        )
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("delete_bot_"))
async def delete_bot_command(callback: types.CallbackQuery):
    """Удаляет бота"""
    
    bot_id = callback.data.replace("delete_bot_", "")
    bot_info = bot_manager.get_bot(bot_id)
    
    if not bot_info:
        await callback.answer("❌ Бот не найден!")
        return
    
    # Удаляем папку с ботом
    try:
        shutil.rmtree(bot_info['folder'])
    except:
        pass
    
    # Удаляем из реестра
    bot_manager.remove_bot(bot_id)
    
    await callback.message.edit_text(
        f"🗑️ Бот {bot_info['name']} удален",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="◀️ НАЗАД", callback_data="my_bots")
            ]]
        )
    )
    await callback.answer()

@dp.message()
async def handle_unknown(message: types.Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "❓ Не понял команду...\n"
        "Используй /start для главного меню.",
        reply_markup=get_main_keyboard()
    )

async def main():
    """Запуск главного бота-конструктора"""
    print("\n" + "="*60)
    print("🎰 КОНСТРУКТОР БОТОВ-КАЗИНО (Telegram Bot)")
    print("="*60)
    print(f"✅ Главный бот запущен!")
    print(f"🔗 Реферальный код: {FIXED_REFERRAL_CODE} (ФИКСИРОВАННЫЙ)")
    print(f"📊 Максимум ботов: {MAX_BOTS}")
    print(f"📁 Боты сохраняются в: {BOTS_FOLDER}")
    print("="*60 + "\n")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
