# -*- coding: utf-8 -*-
import asyncio
import os
from datetime import datetime, time, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import openai
from aiogram import F
from aiogram.filters import Filter
from config import BOT_TOKEN, OPENAI_API_KEY
from prompt_processor import PromptProcessor
from user_memory import UserMemory
from user_memory_extended import UserMemoryExtended
from cbt_techniques import CBTTechniques
from progress_visualizer import ProgressVisualizer
from yookassa_payment import create_payment
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from yookassa_payment import create_payment, get_payment_info

from db_start import async_session
from db_models import users_table
from sqlalchemy import select

from db_utils import update_user_subscription, save_message, get_conversation_context
from sqlalchemy import text

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

import asyncio
from sqlalchemy.exc import OperationalError
from db_start import async_session

from sqlalchemy import text

# bot.py (вверху, рядом с другими импортами)
from create_db import create_db
from sqlalchemy import text


async def wait_for_db():
    print("⏳ Проверяю подключение к PostgreSQL...")
    for attempt in range(1, 16):
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
            print("✅ Подключение к PostgreSQL установлено")
            return
        except Exception as e:
            print(f"🔁 Попытка {attempt}/15: база ещё не готова ({e})")
            await asyncio.sleep(3)
    print("❌ Не удалось подключиться к PostgreSQL после 15 попыток")
    raise SystemExit(1)



bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

openai.api_key = OPENAI_API_KEY
prompt_processor = PromptProcessor(OPENAI_API_KEY)

if not prompt_processor.load_processed_data():
    print("Обработанные данные не найдены. Обрабатываю промпт...")
    if prompt_processor.process_prompt():
        prompt_processor.save_processed_data()
    else:
        print("Ошибка при обработке промпта")

user_memory = UserMemory()
user_memory_extended = UserMemoryExtended(user_memory)

cbt_techniques = CBTTechniques()
progress_visualizer = ProgressVisualizer()


async def wait_for_payment(payment_id: str, user_id: int, months: int = 1):
    """Проверяет оплату, обновляет данные и отправляет приветственное сообщение."""
    print(f"🕓 Старт ожидания платежа {payment_id} для пользователя {user_id}")

    for _ in range(30):  # 30 раз по 10 секунд = 5 минут ожидания
        info = await get_payment_info(payment_id)
        if not info:
            await asyncio.sleep(10)
            continue

        status = info.status
        print(f"🔎 Статус платежа {payment_id}: {status}")

        if status == "succeeded":
            from datetime import datetime, timedelta
            access_until = datetime.now() + timedelta(days=30 * months)
            amount = float(info.amount.value)
            currency = info.amount.currency

            # ✅ Запись в PostgreSQL
            period_label = "3 месяца" if months == 3 else "Ежемесячная"
            await update_user_subscription(user_id, int(amount), period_label)

            # ✅ Параллельно обновляем user_memory (если хочешь сохранять локально)
            try:
                user_memory.update_user_info(user_id, {
                    "is_paid": True,
                    "subscription_status": "Активна",
                    "subscription_period": f"{months} мес.",
                    "subscription_price": amount,
                    "currency": currency,
                    "next_payment_date": access_until.strftime("%Y-%m-%d"),
                    "access_until": access_until.strftime("%Y-%m-%d")
                })
            except Exception as e:
                print(f"⚠️ Ошибка обновления user_memory: {e}")

            # ✅ Отправляем приветственное сообщение
            await bot.send_message(
                chat_id=user_id,
                text=f"""<b>🤍 Добро пожаловать в «Я – Спокойно»</b>

Это пространство, где можно выгружать тревогу, видеть её со стороны и шаг за шагом возвращать себе спокойствие.

Что тебя ждёт:
 • Таблицы состояний — отмечаешь тревогу, замечаешь закономерности и учишься лучше понимать себя.
 • Диалог с ботом — он задаёт вопросы, помогает разложить всё по полочкам и предлагает техники.
 • Таблицы прогресса — видишь, как шаг за шагом меняется твоё состояние.
 • Методичка на 100 страниц — там собраны ключевые техники работы с тревогой, советы по образу жизни и готовый 10-дневный план практик. Можно пробовать разные упражнения и выбрать те, что действительно подходят именно тебе.

Важно: бот не завершает беседу сам, чтобы не оборвать тебя на полуслове. Когда почувствуешь, что достаточно, напиши «Завершить».

Совет: отвечай чуть подробнее. Тогда бот сможет давать не поверхностные слова, а реальные шаги и практики.

А если захочешь поддержки и живого общения — присоединяйся в закрытый клуб. Там мы вместе разбираем ситуации, делимся опытом и поддерживаем друг друга, чтобы путь был легче.

🔘 Кнопки бота

🌱 Старт — ты здесь. Приветственное сообщение и объяснение, как работает бот.
🕯 Заполнить день — возможность выгрузить всё, что накопилось за день, и заметить своё состояние.
🤲 Связаться с куратором — можно напрямую написать мне, если что-то непонятно или нужна поддержка.
📘 Получить методичку — большая методичка на 100 страниц: техники, образ жизни, и тот самый 10-дневный план для практики шаг за шагом.
📈 Мой прогресс — твои таблицы ситуативной и дневной тревожности, чтобы видеть изменения и движения вперёд.
🕊 Информация о подписке — напоминание, сколько дней осталось до конца подписки.

            <b>Доступ к материалам открыт до {access_until:%d.%m.%Y}</b>.
""",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )

            print(f"✅ Оплата подтверждена, пользователь {user_id} обновлён в PostgreSQL до {access_until:%d.%m.%Y}")
            return

        elif status == "canceled":
            await bot.send_message(user_id, "❌ Оплата отменена.")
            return

        await asyncio.sleep(10)

    await bot.send_message(user_id, "⏳ Время ожидания оплаты истекло. Попробуй ещё раз.")


async def check_subscriptions():
    while True:
        now = datetime.now().date()
        for user_id in user_memory.get_all_users():
            info = user_memory.get_user_memory(user_id).get("user_info", {})
            if not info.get("is_paid") or "access_until" not in info:
                continue

            access_until = datetime.strptime(info["access_until"], "%Y-%m-%d").date()
            days_left = (access_until - now).days
            days_after = (now - access_until).days

            if days_left > 3 or days_after > 3:
                continue

            try:
                if days_left == 3:
                    await bot.send_message(user_id, """🤍 Твоя подписка подходит к концу
Осталось всего три дня, чтобы бот продолжал сопровождать тебя: помогать разбирать тревогу, вести таблицы и отмечать прогресс.

Мы хотим, чтобы у тебя не обрывался этот путь — продли подписку заранее и продолжай спокойно двигаться вперёд.""")
                elif days_left == 1:
                    await bot.send_message(user_id, """🕊 Завтра доступ закончится
Все твои записи сохранятся, но новые техники и сопровождение бота станут недоступны.

Ты уже сделал(а) шаги, и мы не хотим, чтобы они потерялись. Продли подписку сегодня — и продолжи с того места, где остановился(ась).
""")
                elif days_after == 1:
                    await bot.send_message(user_id, """🌿 Подписка завершилась
У тебя остались все записи и таблицы, но бот больше не сможет отвечать и предлагать практики.

Если тебе важно продолжать чувствовать поддержку рядом — продли доступ и вернись к привычному ритму.
""")
                elif days_after == 3:
                    await bot.send_message(user_id, """🤍 Прошло три дня без бота
Если заметил(а), что тревога снова берёт верх или стало не хватать структуры — мы здесь, чтобы помочь тебе вернуться.

Подписку легко продлить, и ты продолжишь с того самого места, где остановился(ась).""")
            except Exception as e:
                print(f"Ошибка при отправке уведомления {user_id}: {e}")

        await asyncio.sleep(24 * 60 * 60)  # проверка раз в сутки


# Создание клавиатуры для первого уровня (только 1 кнопка)
def get_first_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Продолжить работу", callback_data="start_flow"))
    return builder.as_markup()

# Создание клавиатуры для второго уровня (только 1 кнопка)
def get_second_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Забрать набор спокойствия", callback_data="continue_flow"))
    return builder.as_markup()

# Создание клавиатуры для третьего уровня (3 кнопки - первая развилка)
def get_third_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Снять острую тревогу", callback_data="anxiety"))
    builder.add(InlineKeyboardButton(text="Навести порядок в жизни", callback_data="order"))
    builder.add(InlineKeyboardButton(text="Разобрать ситуацию", callback_data="analyze"))
    builder.adjust(1)
    return builder.as_markup()

# Создание клавиатуры для четвертого уровня (3 кнопки - вторая развилка)
def get_fourth_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="В голове", callback_data="urgent"))
    builder.add(InlineKeyboardButton(text="В эмоциях", callback_data="gradual"))
    builder.add(InlineKeyboardButton(text="В теле", callback_data="unknown"))
    builder.adjust(1)
    return builder.as_markup()

# Создание клавиатуры для пятого уровня (3 кнопки - третья развилка)
def get_fifth_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Силы", callback_data="mental"))
    builder.add(InlineKeyboardButton(text="Тепло/поддержку", callback_data="emotional"))
    builder.add(InlineKeyboardButton(text="Фокус", callback_data="physical"))
    builder.adjust(1)
    return builder.as_markup()

def get_subscription_info_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Подробнее о подписке", callback_data="subscription_info2"))
    builder.adjust(1)
    return builder.as_markup()


def get_subscription_payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="1 месяц – 1990₽", callback_data="pay_1"),
        InlineKeyboardButton(text="3 месяца – 4490₽", callback_data="pay_2"),
    )
    builder.adjust(1)
    return builder.as_markup()

def get_main_keyboard(collapsed: bool = True):
    """Главная клавиатура с возможностью показать больше/меньше кнопок"""
    builder = InlineKeyboardBuilder()

    # первые 6 кнопок
    builder.add(InlineKeyboardButton(text="🌱 Старт", callback_data="main_start"))
    builder.add(InlineKeyboardButton(text="🕯 Заполнить день", callback_data="main_daily_check"))
    builder.add(InlineKeyboardButton(text="🤲 Связаться с куратором", url="https://t.me/taisiya_psychology"))
    builder.add(InlineKeyboardButton(text="📘 Получить методичку", callback_data="main_pdf"))
    builder.add(InlineKeyboardButton(text="📈 Мой прогресс", callback_data="main_emotion_tracker"))
    builder.add(InlineKeyboardButton(text="🧘‍♀️ КПТ-техники", callback_data="cpt_techniques"))

    if collapsed:
        # кнопка показать ещё
        builder.add(InlineKeyboardButton(text="➕ Ещё", callback_data="expand_main"))
    else:
        # дополнительные кнопки
        builder.add(InlineKeyboardButton(text="🕊 Информация о подписке", callback_data="subscription_info"))
        builder.add(InlineKeyboardButton(text="👩 Указать пол", callback_data="set_gender"))
        builder.add(InlineKeyboardButton(text="⏳ Изменить время проверки", callback_data="set_time"))
        builder.add(InlineKeyboardButton(text="🧑 Изменить свое имя", callback_data="change_name"))
        # кнопка свернуть
        builder.add(InlineKeyboardButton(text="➖ Скрыть", callback_data="collapse_main"))

    builder.adjust(2)
    return builder.as_markup()



# Клавиатура для начала проверки
def get_daily_check_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да, давай", callback_data="daily_check_yes"))
    builder.add(InlineKeyboardButton(text="Напомнить позже (45 мин)", callback_data="daily_check_remind_45"))
    builder.add(InlineKeyboardButton(text="Напомнить позже (1,5 часа)", callback_data="daily_check_remind_90"))
    builder.add(InlineKeyboardButton(text="Пропустить сегодня", callback_data="daily_check_skip"))
    builder.adjust(1)
    return builder.as_markup()

# Клавиатура для выбора уровня тревоги (0-10)
def get_anxiety_level_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(11):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"anxiety_level_{i}"))
    builder.adjust(3)  # 3 кнопки в ряд
    return builder.as_markup()

# Клавиатура для выбора факторов влияния
def get_factors_keyboard():
    builder = InlineKeyboardBuilder()
    factors = ["Сон", "Работа/Учёба", "Деньги", "Отношения", "Здоровье", 
               "Неопределённость", "Конфликт", "Новости", "Кофеин", 
               "Шум/толпа", "Иное"]
    
    for factor in factors:
        builder.add(InlineKeyboardButton(text=factor, callback_data=f"factor_{factor}"))
    
    builder.add(InlineKeyboardButton(text="Готово", callback_data="factors_done"))
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()


@dp.callback_query(lambda c: c.data == "expand_main")
async def expand_main_keyboard(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(collapsed=False))

@dp.callback_query(lambda c: c.data == "collapse_main")
async def collapse_main_keyboard(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(collapsed=True))



class PaidOnly(BaseFilter):
    async def __call__(self, obj: types.CallbackQuery | types.Message) -> bool:
        user_id = obj.from_user.id
        if not is_paid(user_id):
            if isinstance(obj, types.CallbackQuery):
                await obj.message.answer(
                    "<b>Эта функция доступна только по подписке 💳</b>\n\n"
                    "Оформи подписку и получи доступ ко всем функциям бота.",
                    parse_mode="HTML",
                    reply_markup=get_subscription_payment_keyboard()
                )
            else:
                await obj.answer(
                    "<b>Эта функция доступна только по подписке 💳</b>\n\n"
                    "Оформи подписку и получи доступ ко всем функциям бота.",
                    parse_mode="HTML",
                    reply_markup=get_subscription_payment_keyboard()
                )
            return False
        return True
    
def is_paid(user_id: int) -> bool:
    """Проверяет, является ли подписка пользователя активной."""
    user_data = user_memory.get_user_memory(user_id).get("user_info", {})
    
    # 1. Проверяем флаг 'is_paid'
    if not user_data.get("is_paid", False):
        return False
        
    # 2. Проверяем дату окончания подписки
    access_until_str = user_data.get("access_until")
    if not access_until_str:
        # Если is_paid=True, но даты нет - ошибка данных, но дадим доступ
        return True 

    try:
        access_until_date = datetime.strptime(access_until_str, "%Y-%m-%d").date()
        return access_until_date >= datetime.now().date()
    except ValueError:
        # Ошибка в формате даты, считаем подписку неактивной
        return False

@dp.callback_query(lambda c: c.data == "pay_1")
async def handle_pay_1m(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    email = "taisia.psychology@yandex.ru" 
    bot_username = "@IAmCalm_Bot"

    payment = await create_payment(
        amount=1990,
        description="Подписка на 1 месяц",
        email="taisia.psychology@yandex.ru",
        bot_username="@IAmCalm_Bot",
        user_id=user_id
    )
    if payment:
        await callback.message.answer(
            f"Ссылка на оплату за 1 месяц: <a href=\"{payment.confirmation.confirmation_url}\">{payment.confirmation.confirmation_url}</a>",
            parse_mode="HTML"
        )
        asyncio.create_task(wait_for_payment(payment.id, user_id, months=1))

    else:
        await callback.message.answer("Ошибка при создании платежа.")

@dp.callback_query(lambda c: c.data == "pay_2")
async def handle_pay_3m(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    email = "taisia.psychology@yandex.ru"
    bot_username = "@IAmCalm_Bot"
    user_id=user_id


    payment = await create_payment(
        amount=4490,
        description="Подписка на 3 месяца",
        email=email,
        bot_username=bot_username,
        user_id=user_id
    )
    if payment:
        await callback.message.answer(
            f"Ссылка на оплату за 3 месяца: <a href=\"{payment.confirmation.confirmation_url}\">{payment.confirmation.confirmation_url}</a>",
            parse_mode="HTML"
        )
        asyncio.create_task(wait_for_payment(payment.id, user_id, months=3))

    else:
        await callback.message.answer("Ошибка при создании платежа.")


async def load_user_info(user_id: int) -> dict:
    """Загружает данные подписки для конкретного пользователя из PostgreSQL."""
    async with async_session() as session:
        result = await session.execute(
            select(users_table).where(users_table.c.user_id == user_id)
        )
        user = result.mappings().first()  # получаем строку в виде dict
        if not user:
            return {}
        return dict(user)


async def schedule_daily_reminder(user_id: int, time_str: str = "18:30"):
    """Запускает ежедневное напоминание для пользователя в заданное время"""
    try:
        while True:
            now = datetime.now()
            target_time = datetime.strptime(time_str, "%H:%M").time()
            target = datetime.combine(now.date(), target_time)

            # если время уже прошло сегодня → переносим на завтра
            if target <= now:
                target += timedelta(days=1)

            wait_time = (target - now).total_seconds()
            await asyncio.sleep(wait_time)

            # --- ИСПРАВЛЕНИЕ: Используем корректную проверку is_paid ---
            if is_paid(user_id):
                await send_daily_reminder(user_id)
            else:
                print(f"⏭ Пропущено напоминание для {user_id} — нет активной подписки или она истекла")
            # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    except Exception as e:
        print(f"❌ Ошибка в schedule_daily_reminder для {user_id}: {e}")


async def send_daily_reminder(user_id: int):
    """Отправляет напоминание о ежедневной проверке пользователю (только если подписка активна)"""
    try:
        user_memory_data = user_memory.get_user_memory(user_id)
        user_info = user_memory_data.get("user_info", {})

        # Проверяем, есть ли подписка
        if not user_info.get("is_paid"):
            print(f"⏭ Напоминание не отправлено — у пользователя {user_id} нет активной подписки")
            return

        name = user_info.get("name", "друг")

        text = f"<b>Привет, {name}! Сделаем проверку твоего состояния сегодня? 💛</b>"

        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=get_daily_check_start_keyboard(),
            parse_mode="HTML"
        )

        # Добавляем в историю
        user_memory.add_message_to_history(
            user_id,
            "assistant",
            "Напоминание о ежедневной проверке"
        )

    except Exception as e:
        print(f"❌ Ошибка при отправке напоминания пользователю {user_id}: {e}")


async def send_sequence_messages(user_id: int, name: str):
    """Отправляет последовательность сообщений после /start с задержками, если не оплачено"""
    try:
                # Сообщение 1 — через 10 минут
        await asyncio.sleep(10*60)
        if is_paid(user_id):
            return
        message1 = (
            "<b>Сделала один вечерний чек-ин — и уснула без гонки мыслей</b>\n\n"
            "Это не магия: бот даёт ровно ту технику, которая подходит тебе сейчас.\n\n"
            "В боте ты отмечаешь «тревога сейчас» и «за день», а он подбирает шаги — дыхание/заземление/мини‑КПТ — <i>и учит делать правильно</i>.\n\n"
            "<b>А в клубе</b> разбираем твои ситуации и поддерживаем, чтобы эффект закреплялся.\n\n"
            "Участники уже:\n— легче засыпают;\n— меньше избеганий;\n— на графиках тревога падает, а контроль растёт.\n\n"
            "<i>Мы не делаем формальность — работаем с твоим реальным состоянием.</i>\n\n"
            "<b>Представь:</b> 7–10 минут вечером → замечаешь триггеры, делаешь технику «здесь и сейчас», шаг за шагом возвращаешь контроль.\n\n"
            "<b>Это возможно.</b>\n\n"
            "Чтобы узнать подробности и подключиться по цене запуска, жми на кнопку ниже 👇\n"
            "Сегодня действует цена запуска."
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее о подписке", callback_data="subscription_info2")]
            ]
        )
        with open("images/1 отложенное (10 минут).png", "rb") as f:
            photo = BufferedInputFile(f.read(), filename="delayed_1.png")
            await bot.send_photo(chat_id=user_id, photo=photo, caption=message1, parse_mode="HTML", reply_markup=keyboard)

        # Сообщение 2 — через 2 часа
        await asyncio.sleep(2*60*60)
        if is_paid(user_id):
            return
        message2 = (
            "<b>Моя тревожность снизилась с 54 до 20 баллов.</b>\n\n"
            "<b>И впервые за долгое время я стала спать спокойно.</b>\n\n"
            "Это не шутка, это моя реальность.\n\n"
            "Я сама проверила на себе: тревога, которая раньше держала меня на уровне 54 баллов, постепенно ушла до 20.\n\n"
            "Теперь я сплю глубже, реагирую спокойнее и чувствую, что могу управлять своим состоянием.\n\n"
            "В бот я собрала всё, что помогло мне самой:\n— техники для быстрого снятия тревоги,\n— разборы мыслей и эмоций,\n— а главное — искусственный интеллект внутри бота мягко ведёт тебя через разбор волнующих ситуаций.\n\n"
            "Это не сухой шаблон и не «терапия», а бережная консультация: ты описываешь, что случилось, а бот помогает увидеть мысль, задать вопросы, найти более спокойный взгляд.\n\n"
            "Жми на кнопку ниже и подключайся по цене запуска 👇🏻"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее о подписке", callback_data="subscription_info2")]
            ]
        )


        with open("images/2 отложенное (2 часа).jpg", "rb") as f:
            photo = BufferedInputFile(f.read(), filename="delayed_2.jpg")
            await bot.send_photo(chat_id=user_id, photo=photo, caption=message2, parse_mode="HTML", reply_markup=keyboard)

        # Сообщение 3 — через 5 часов
        await asyncio.sleep(5*60*60)
        if is_paid(user_id):
            return
        message3 = (
            "<b>Как выглядит мой архив вечерних чек-инов — и скрин графика тревожности</b> 😀\n\n"
            "У подопечных — та же история:\n«Ничего особенного не делала, а стало легче» — даже когда ресурса мало и дней «без сил» больше, чем хотелось бы.\n\n"
            "Почему так работает?\n\n"
            "Потому что бот крутится каждый вечер: чек-ин «тревога сейчас / за день», автоподбор техники или мягкий разбор ситуации, а в клубе — обратная связь и поддержка.\n\n"
            "Алгоритм выстроен, напоминания стоят, техники объяснены, графики показывают живую динамику.\n\n"
            "Да, можно не «пахать» часами, а всё равно получать входящие результаты:\nлучше спать, реже срываться, спокойнее реагировать и ощущать контроль.\n\n"
            "Что для этого нужно на самом деле?\n\n"
            "Реально проанализировать свои потребности и триггеры:\nговорить с ботом на языке своих состояний,\nделать короткие техники «здесь и сейчас»\nи закрывать внутренние возражения через мини-КПТ (мысль → факты → трезвая версия).\n\n"
            "Если ты умело этим воспользуешься:\nвечерний ритуал = чек-ин → техника/разбор → микро-шаг на завтра,\nа главные когнитивные ловушки (катастрофизация, «всё или ничего») закрыты,\n<b>— у тревоги нет шансов не отступить.</b>\n\n"
            "Присоединяйся к подписке — сделай себе так же.\n\n"
            "Подключай бот и клуб, начни с первого чек-ина сегодня."
        )
        with open("images/3 отложенное (5 часов).jpg", "rb") as f:
            photo = BufferedInputFile(f.read(), filename="delayed_3.jpg")
            await bot.send_photo(chat_id=user_id, photo=photo)  # Без caption!
        await bot.send_message(chat_id=user_id, text=message3, parse_mode="HTML")
        
        # Сообщение 4 — через 20 часов
        await asyncio.sleep(20*60*60)
        if is_paid(user_id):
            return
        message4 = (
            "<b>Я извиняюсь, но они не просто «что-то делают» — они реально включаются и идут вперёд!</b>\n\n"
            "Раньше мне казалось, что перемены приходят только после дорогих обучений или долгих терапий.\n\n"
            "Но нет. Люди начинают действовать, когда попадают в понятную систему:\n— есть поддержка,\n— есть окружение,\n— есть живой пример, который спрашивает «как прошёл день?» и подталкивает к следующему шагу.\n\n"
            "<b>Грех не делать, когда ты видишь, что каждое твоё действие ведёт к реальному результату: тревога снижается, сон улучшается, реакции становятся спокойнее.</b>\n\n"
            "Нажимай «Подробнее о подписке» и присоединяйся 👇🏻"
        )
        await bot.send_message(chat_id=user_id, text=message4, parse_mode="HTML")

        # Сообщение 5 — через 24 часа от предыдущего
        await asyncio.sleep(24*60*60)
        if is_paid(user_id):
            return
        message5 = (
            "<b>В 2023</b> я сама искала хоть что-то, чтобы справиться с тревогой.\n\n"
            "Слушала вебинары, конспектировала советы «умных людей» — и всё равно возвращалась к тем же мыслям.\n\n"
            "А в <b>2025</b> люди уже пишут:\n<b>«Спасибо, ты помогла».</b>\n\n"
            "<b>Что изменилось?</b>\n\n"
            "Я перестала крутиться в тревоге и пустых ожиданиях — и собрала систему, которая держит меня в спокойствии.\n\n"
            "<b>Что реально работает:</b>\n— вечерний чек-ин: отмечаю уровень тревоги,\n— бот помогает разобрать ситуацию и даёт конкретный шаг,\n— техники, которые действительно снижают тревожность,\n— поддержка и обратная связь в клубе.\n\n"
            "Это не про «вдохновение».\n\n"
            "<b>Это про рабочие шаги, которые меняют жизнь:</b>\nсон глубже, реакции спокойнее, тревога уходит из-под контроля.\n\n"
            "Сейчас доступ в систему — <b>1990₽</b>: пошаговые  практики, бот и поддержка в клубе.\n\n"
            "Попробуй — хотя бы возьми своё.\n\n"
            "<b>Жми на кнопку 👇🏻</b>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее о подписке", callback_data="subscription_info2")]
            ]
        )
        with open("images/5 отложенное (24 часа).png", "rb") as f:
            photo = BufferedInputFile(f.read(), filename="delayed_5.png")
            await bot.send_photo(chat_id=user_id, photo=photo)
        await bot.send_message(chat_id=user_id, text=message5, parse_mode="HTML", reply_markup=keyboard)

        # Сообщение 6 — через 48 часов
        await asyncio.sleep(48*60*60)
        if is_paid(user_id):
            return
        message6 = (
            "<b>Как довести тревогу до капитуляции</b>\n\n"
            "или «Оценил — сделал — уснул».\n\n"
            "Это не мечта — это реальность участников.\n\n"
            "Потому что вечером они честно раскрываются в чек-ине, а бот с ИИ помогает разобрать волнующую ситуацию и дать точный следующий шаг. Так возникает сильная эмоциональная связь с собой — и спокойствие перестаёт быть случайностью.\n\n"
            "<b>В подписке ты узнаешь, как:</b>\n— называть свои эмоции и потребности, чтобы тревога не рулила тобой;\n— транслировать ценности и границы без чувства вины;\n— показывать себе путь;\n— чтобы к тебе возвращались твоё спокойствие и энергия (полный мэтч с собственной жизнью).\n\n"
            "<b>Результат:</b> глубже спишь, мягче реагируешь, меньше срывов — и вокруг появляется поддерживающее окружение.\n\n"
            "<b>1990₽</b> — за пошаговую систему вечерних чек-инов с ежедневными заданиями.\n"
            "Внутри: комьюнити, опора, готовые техники и сценарии вечерних диалогов, методички и свежие знания.\n\n"
            "<b>Хватит откладывать — начни с сегодняшнего вечера.</b>\n\n"
            "Нажимай «Подробнее о подписке» и присоединяйся 👇🏻"
        )
       
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее о подписке", callback_data="subscription_info2")]
            ]
        )
        await bot.send_message(chat_id=user_id, text=message6, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Ошибка в send_sequence_messages: {e}")



# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Запоминаем информацию о пользователе
    user_info = {
        "name": message.from_user.first_name or "Пользователь",
        "username": message.from_user.username or "",
        "start_date": message.date.isoformat(),
        "language_code": message.from_user.language_code or "ru"
    }
    user_memory.update_user_info(user_id, user_info)
    
    # Добавляем сообщение в историю
    user_memory.add_message_to_history(user_id, "user", "/start")
    
    # Запускаем ежедневное напоминание для этого пользователя
    # Берём сохранённое время или устанавливаем дефолт 18:30
    user_data = user_memory.get_user_memory(user_id)
    saved_time = user_data.get("user_info", {}).get("daily_check_time")
    if not saved_time:
        saved_time = "18:30"
        user_memory.update_user_info(user_id, {"daily_check_time": saved_time})
    asyncio.create_task(schedule_daily_reminder(user_id, saved_time))
    
    # Персонализированное приветствие
    name = user_info["name"]
    welcome_text = (
        "Привет 🤍 Я <b>Таисия Довыденко</b> — здесь о психологии по-человечески.\n"
        "Помогаю снижать тревожность с опорой на <b>науку</b> — бережно, системно.\n\n"
        "А если подробнее, я:\n"
        "— 5-й курс клинической психологии в медуниверситете, повышение квалификации — детская нейропсихология;\n"
        "— веду индивидуальные и групповые форматы;\n"
        "— собрала рабочие КПТ-протоколы и нейро-инструменты и адаптировала их под формат «карманного» психолога.\n\n"
        "Моя цель — сделать качественную, доказательную психопомощь доступной каждому человеку.\n\n"
        "Я проанализировала лучшие КПТ-техники, дневники тревоги, поведенческие эксперименты и практики самопомощи, научила искусственный интеллект быть искусным собеседником — и положила всё это в этот бот.\n\n"
        "Этот проект — для людей, которые хотят управлять тревогой, выстраивать границы и стабильно ощущать спокойствие и ясность.\n\n"
        "<b>Тут лежат мои мозги, душа, опора на доказательность и самые работающие практики.</b>\n\n"
        "Приступим к нашей работе?)\n\n"
        "<a href=\"https://drive.google.com/file/d/1DDaFn_S7a5nTpKWKBMyzUlrdPRZoXARE/view?usp=drivesdk\"><i>Нажимая на кнопку ниже, ты соглашаешься на получение информационной и рекламной рассылки</i></a>"
    )
    
    # Отправляем приветственное сообщение с изображением
    with open("images/Для приветственного сообщения.png", "rb") as f:
        photo = BufferedInputFile(f.read(), filename="welcome.png")
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=get_first_keyboard(),
            parse_mode="HTML"
        )
    
    # Запоминаем ответ бота
    user_memory.add_message_to_history(user_id, "assistant", "Приветствие и представление")
    
    # Запускаем последовательность сообщений в фоне
    asyncio.create_task(send_sequence_messages(user_id, name))



@dp.callback_query(lambda c: c.data == "main_start")
async def handle_main_start(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    user_memory.add_message_to_history(user_id, "user", "main_start")
    
    text = f"""<b>Добро пожаловать, {name}! 👋</b>

<b>🎯 Как использовать бота:</b>
Нажми на одну из кнопок ниже или напиши мне сообщение!

<b>💬 Как завершить диалог:</b>
Просто напиши "завершить".

<b>🔗 Закрытый клуб:</b>
<a href="https://t.me/+iJNSvffQUhxjMWYy
">Присоединяйся к нашему сообществу для поддержки и обмена опытом!</a>

<b>💡 Совет:</b> Регулярное использование бота поможет вам лучше понимать свои эмоции и развивать навыки управления тревожностью.
Чем более развернуто ты будешь отвечать на вопросы бота, тем лучше он сможет подобрать рекомендации и техники для твоего состояния!
"""
    
    await callback.message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")
    user_memory.add_message_to_history(user_id, "assistant", "Главное меню")

@dp.message(Command("pro"))
async def handle_pro_command(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "друг"

    user_memory.add_message_to_history(user_id, "user", "/pro")

    text = f"""<b>Добро пожаловать, {name}! 👋</b>

<b>🎯 Как использовать бота:</b>
Нажми на одну из кнопок ниже или напиши мне сообщение!

<b>💬 Как завершить диалог:</b>
Просто напиши "завершить".

<b>🔗 Закрытый клуб:</b>
<a href="https://t.me/+iJNSvffQUhxjMWYy">Присоединяйся к нашему сообществу для поддержки и обмена опытом!</a>

<b>💡 Совет:</b> Регулярное использование бота поможет вам лучше понимать свои эмоции и развивать навыки управления тревожностью.
Чем более развернуто ты будешь отвечать на вопросы бота, тем лучше он сможет подобрать рекомендации и техники для твоего состояния!
"""

    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")
    user_memory.add_message_to_history(user_id, "assistant", "Главное меню")

@dp.callback_query(lambda c: c.data == "change_name")
async def handle_change_name(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    text = "✍️ Напиши новое имя, и я буду обращаться к тебе именно так!"
    await callback.message.answer(text, parse_mode="HTML")

    # фиксируем, что пользователь теперь в процессе изменения имени
    user_memory.add_message_to_history(user_id, "user", "change_name")


@dp.callback_query(lambda c: c.data == "set_gender")
async def cmd_set_gender_callback(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    user_memory.add_message_to_history(user_id, "user", "/set_gender")
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"))
    keyboard.add(InlineKeyboardButton(text="👩 Женский", callback_data="gender_female"))
    keyboard.adjust(2)
    
    text = """<b>⚙️ Укажите ваш пол</b>

Это поможет боту обращаться к вам в правильном склонении в финальных сообщениях."""
    
    user_memory.add_message_to_history(user_id, "assistant", text)
    await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith("gender_"))
async def handle_gender_selection(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    gender_data = callback.data.replace("gender_", "")
    
    if gender_data == "cancel":
        await callback.message.edit_text("❌ Отменено. Пол не изменен.")
        return
    
    # Сохраняем пол пользователя
    user_memory.update_user_info(user_id, {"gender": gender_data})
    
    gender_text = "мужской" if gender_data == "male" else "женский"
    await callback.message.edit_text(f"✅ Пол установлен: <b>{gender_text}</b>\n\nТеперь бот будет обращаться к вам в правильном склонении!", parse_mode="HTML")



@dp.callback_query(lambda c: c.data == "set_time")
async def cmd_set_time_callback(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    user_memory.add_message_to_history(user_id, "user", "/set_time")
    
    text = """<b>⏰ Изменить время ежедневной проверки</b>

Напиши время в формате <code>ЧЧ:ММ</code> (например: 09:30, 18:00, 21:15)"""
    
    user_memory.add_message_to_history(user_id, "assistant", text)
    await callback.message.answer(text, parse_mode="HTML")


# Обработчик для установки времени
@dp.message(lambda message: message.text and ":" in message.text and len(message.text) == 5 and message.text[2] == ":")
async def handle_time_setting(message: types.Message):
    user_id = message.from_user.id
    time_text = message.text.strip()
    
    # Проверяем формат времени
    try:
        hour, minute = time_text.split(":")
        hour = int(hour)
        minute = int(minute)
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            # Сохраняем время
            user_memory.update_user_info(user_id, {"daily_check_time": time_text})
            
            # Запускаем планировщик напоминаний
            asyncio.create_task(schedule_daily_reminder(user_id, time_text))
            
            await message.answer(f"✅ Время ежедневной проверки установлено: <b>{time_text}</b>\n\nТеперь бот будет напоминать тебе о ежедневной проверке в это время!", parse_mode="HTML")
            user_memory.add_message_to_history(user_id, "assistant", f"Время установлено: {time_text}")
        else:
            await message.answer("❌ Неверный формат времени. Используйте формат ЧЧ:ММ (например: 09:30)")
    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте формат ЧЧ:ММ (например: 09:30)")


class IsChangingName(Filter):
    async def __call__(self, message: types.Message) -> bool:
        user_id = message.from_user.id
        last_history = user_memory.get_user_memory(user_id).get("conversation_history", [])
        return last_history and last_history[-1].get("content") == "change_name"

@dp.message(IsChangingName())
async def handle_name_change_message(message: types.Message):
    user_id = message.from_user.id
    new_name = message.text.strip()
    if new_name:
        user_memory.update_user_info(user_id, {"name": new_name})
        await message.answer(
            f"✅ Имя обновлено! Теперь я буду обращаться к тебе как <b>{new_name}</b>.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        user_memory.add_message_to_history(user_id, "assistant", f"Имя пользователя изменено на: {new_name}")
    else:
        await message.answer("Пожалуйста, напиши имя, чтобы я могла обращаться к тебе правильно 💛")

    

@dp.callback_query(lambda c: c.data == "cpt_techniques", PaidOnly())
async def cmd_cpt_techniques(callback: types.CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    user_memory.add_message_to_history(user_id, "user", "/cpt_techniques")
    
    text = f"""<b>КПТ техники, {name}! 🧘‍♀️</b>

Выбери категорию техник:"""
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🫁 Дыхательные", callback_data="cbt_breathing"))
    keyboard.add(InlineKeyboardButton(text="🌍 Заземление", callback_data="cbt_grounding"))
    keyboard.add(InlineKeyboardButton(text="😌 Релаксация", callback_data="cbt_relaxation"))
    keyboard.add(InlineKeyboardButton(text="🧠 Осознанность", callback_data="cbt_mindfulness"))
    keyboard.add(InlineKeyboardButton(text="💭 Когнитивные", callback_data="cbt_cognitive"))
    keyboard.adjust(2)
    
    await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")



@dp.callback_query(lambda c: c.data == "subscription_info")
async def handle_subscription_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = await load_user_info(user_id)

    status = user_data.get("subscription_status", "Неактивна")
    period = user_data.get("subscription_period", "—")
    price = user_data.get("subscription_price", "—")
    next_payment_date = user_data.get("next_payment_date", "—")

    if status == "Активна" and next_payment_date != "—":
        try:
            dt = datetime.strptime(next_payment_date, "%Y-%m-%d")
            days_left = (dt.date() - datetime.now().date()).days
            if days_left >= 0:
                next_info = f"Через {days_left} дней ({dt:%d.%m.%Y})"
            else:
                next_info = "Подписка завершилась"
        except Exception:
            next_info = next_payment_date
    else:
        next_info = "—"

    text = (
        f"<b>Информация о подписке 💳</b>\n\n"
        f"📅 <b>Статус:</b> {status}\n"
        f"⏰ <b>Период:</b> {period}\n"
        f"💰 <b>Стоимость:</b> {price} ₽\n"
        f"🔄 <b>Следующее списание:</b> {next_info}\n"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="main_start"))
    if status != "Активна":
        keyboard.add(types.InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="pay_1"))
    keyboard.adjust(1)

    await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


# Обработчик нажатия на первую кнопку
@dp.callback_query(lambda c: c.data == "start_flow")
async def process_first_button(callback: types.CallbackQuery):
    await callback.answer()
    # Отправляем сообщение с одной кнопкой
    await callback.message.answer(
        """<b>Здесь ты можешь:</b>

• <b>Ежедневно отмечать</b> уровень тревоги/ресурса в таблицах и смотреть динамику
• <b>Фиксировать эмоции, мысли и ситуации</b>, замечать автоматические мысли и когнитивные искажения
• <b>Производить переоценку</b> своей жизни
• <b>Отмечать триггеры</b> и поддерживающие действия (сон, питание, движение, общение)
• <b>Заполнять по пошаговому алгоритму</b> из видео: что писать, что делать при высоких значениях и как не перегореть

<b>При доступе к полной версии</b> у тебя будет <b>ИИ-бот и PDF-гайд</b> (техники на сейчас и базовый режим жизни), а также канал со мной, где можно получить обратную связь на свои запросы 🤍

<b>Ответь на пару вопросов</b> — пришлю бесплатный старт-набор (таблицы + дневник + видео).""",
        reply_markup=get_second_keyboard(),
        parse_mode="HTML"
    )

# Обработчик нажатия на вторую кнопку
@dp.callback_query(lambda c: c.data == "continue_flow")
async def process_second_button(callback: types.CallbackQuery):
    await callback.answer()
    
    # Отправляем клавиатуру с тремя кнопками (первая развилка)
    await callback.message.answer(
        "<b>Что хочется прямо сейчас?</b> 🤔",
        reply_markup=get_third_keyboard(),
        parse_mode="HTML"
    )

# Обработчик нажатий на кнопки третьего уровня (первая развилка)
@dp.callback_query(lambda c: c.data in ["anxiety", "order", "analyze"])
async def process_third_level(callback: types.CallbackQuery):
    await callback.answer()
    
    # Отправляем сообщение с тремя кнопками (вторая развилка)
    await callback.message.answer(
        "<b>Если коротко, то ты сейчас больше...</b> 💭",
        reply_markup=get_fourth_keyboard(),
        parse_mode="HTML"
    )

# Обработчик нажатий на кнопки четвертого уровня (вторая развилка)
@dp.callback_query(lambda c: c.data in ["urgent", "gradual", "unknown"])
async def process_fourth_level(callback: types.CallbackQuery):
    await callback.answer()
    
    # Отправляем сообщение с тремя кнопками (третья развилка)
    await callback.message.answer(
        "<b>Что сейчас больше всего хочется дать себе?</b> 💝",
        reply_markup=get_fifth_keyboard(),
        parse_mode="HTML"
    )

# Обработчик нажатий на кнопки пятого уровня (третья развилка)
@dp.callback_query(lambda c: c.data in ["mental", "emotional", "physical"])
async def process_fifth_level(callback: types.CallbackQuery):
    await callback.answer()
    
    # Отправляем первое сообщение
    await callback.message.answer(
        """<b>▫️ Заметь:</b> сейчас твоя тревога может казаться небольшой или, наоборот, очень ощутимой.

Поэтому прежде чем переходить к глубоким разборам, важно сначала <b>заметить и отследить базовые состояния</b> — уровень тревоги, ресурса, реакции тела.

А уже после этого мы двинемся к <b>проработке мыслей и стратегий</b> 💪""",
        parse_mode="HTML"
    )
    
    # Ждем 5 секунд перед отправкой второго сообщения
    await asyncio.sleep(5)
    
    # Отправляем второе сообщение
    await callback.message.answer(
        """<b>✨ Урок о том, как справляться с тревогой</b> и шаг за шагом возвращать себе себя.

Он помогает мягко разложить всё по полочкам — <b>без надрыва и без лишнего давления</b>. Те, кто годами чувствовали, что застряли в круге тревог, после него впервые сказали: <em>«Теперь я понимаю, как выбраться и что делать дальше»</em>.

<b>Внутри:</b>
• <b>Простая стратегия</b>, которая работает надолго и даёт ощущение опоры
• Как <b>заметить свои триггеры</b> и подобрать практики так, чтобы они действительно помогали
• <b>Маленькая система шагов</b>, которая снижает тревогу и возвращает энергию в повседневность

📎 <b>Таблица тревоги</b> <a href="https://docs.google.com/spreadsheets/d/1ipy8B6CgxhajmPGnG2hWFTqBN0vXanq29AINpmZV3_w/edit?gid=685037108#gid=685037108">тут</a>
📎 <b>Чек-лист заботы о себе в тревоге</b> <a href="https://drive.google.com/file/d/1CJ-OEkmui37hWtMQ6HyypeZh5e_cjh4L/view?usp=sharing">тут</a>
📎 <b>❗️ Важно посмотреть</b> <a href="https://rutube.ru/video/private/1627bde4c3adf337fd8648b079f2c565/?p=wvaHHvLe9rGNqUxN1I3-SQ">урок</a> — только так материалы сработают на 100%.

А если хочешь не просто знать стратегию, а реально внедрить её, подключай <b>бота и клуб</b>.

🤖 <b>Бот будет каждый день рядом:</b> задавать вопросы, отслеживать твои состояния и предлагать техники, которые сработают именно для тебя, составлять графики твоего ментального прогресса.

🤍 <b>В клубе</b> мы вместе разбираем ситуации, даём обратную связь и поддерживаем, чтобы путь был легче и результат стабильнее.""",
        parse_mode="HTML",
        reply_markup=get_subscription_info_keyboard()
    )

@dp.callback_query(lambda c: c.data == "subscription_info2")
async def handle_subscription_info_new(callback: types.CallbackQuery):
    await callback.answer()

    text = """🤍 Спасибо, что ты здесь.

В подписке <b>(бот + клуб)</b> ты получаешь систему поддержки, которая помогает снижать тревожность каждый день.

<b>Как строится работа</b>

Каждый день у тебя есть пространство, чтобы остановиться и заметить своё состояние.  
— Бот напоминает тебе заполнить день и после задаёт короткие вопросы, запоминая твою статистику.  
— При повышенном уровне тревоги он помогает разобрать конкретную ситуацию по шагам и разложить по полочкам всё в твоей голове.  
— На основе твоих ответов бот предлагает техники для успокоения здесь и сейчас.  
— Всё это сохраняется, и со временем формируется твоя личная стратегия — не на один день, а в долгую.  

Параллельно ты получаешь <b>поддержку в клубе</b>:  
— там каждый день публикуются материалы, заметки и практики,  
— каждую неделю мы разбираем ситуации и я даю обратную связь,  
— так формируется ощущение, что ты не одна и рядом есть люди, которые понимают.  

<b>После оформления подписки тебе откроется:</b>  

— <b>«Путеводитель по тревоге»</b> — большой PDF с иллюстрациями и понятными объяснениями: почему тревожность возникает, какие техники работают, как выстраивать режим и заботу о себе. Это твоя база знаний, к которой можно возвращаться в любое время.  
— <b>ИИ-бот</b> — который запоминает именно твои ответы и помогает выстроить стратегию на протяжении всего времени.  
— <b>Клуб</b> — с регулярными материалами, поддержкой и живой обратной связью.  

<b>Стоимость участия</b>  

💳  <b>1990₽</b> <s>2990₽</s> — месяц (достаточно, чтобы попробовать и почувствовать первые результаты).  
💳  <b>4490₽</b> <s>8970₽</s> — три месяца (для тех, кто хочет стабильного результата и поддержки с запасом).  

Эта стоимость актуальна сейчас.  
Если откликается — присоединяйся.  

<a href="https://docs.google.com/document/d/1234567890/edit?usp=sharing"><i>При оформлении подписки ты подтверждаешь согласие с договором-офертой</i></a>

Пусть бот, клуб и «Путеводитель по тревоге» будут твоей опорой на пути к спокойствию 🤍
"""

    # Кнопки оплаты
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="1 месяц – 1990₽", callback_data="pay_1"),
        InlineKeyboardButton(text="3 месяца – 4490₽", callback_data="pay_2"),
    )
    keyboard.adjust(1)

    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard.as_markup())


@dp.callback_query(lambda c: c.data == "main_daily_check", PaidOnly())
async def handle_main_daily_check(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    # if not is_paid(user_id):
    #     text = "<b>Извините, но вам нужно оформить подписку, чтобы продолжить.</b>"
    #     await callback.message.answer(text, parse_mode="HTML")
    #     return

    user_memory.add_message_to_history(user_id, "user", "main_daily_check")
    
    text = f"<b>Привет, {name}! Сделаем проверку твоего состояния сегодня? 💛</b>"
    await callback.message.answer(text, reply_markup=get_daily_check_start_keyboard(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "main_pdf", PaidOnly())
async def handle_main_pdf(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    user_memory.add_message_to_history(user_id, "user", "main_pdf")
    
    # Отправляем PDF файл
    from aiogram.types import FSInputFile
    pdf_file = FSInputFile("Там,_где_становится_тише_Довыденко_Таисия.pdf")
    await callback.message.answer_document(
        document=pdf_file,
        caption=f"<b>📘 Методичка \"Там, где становится тише\"</b>\n\n{name}, вот твоя методичка! Изучай и применяй техники на практике 💛",
        parse_mode="HTML"
    )
    
    user_memory.add_message_to_history(user_id, "assistant", "Отправлена методичка")

@dp.callback_query(lambda c: c.data == "main_emotion_tracker", PaidOnly())
async def handle_main_emotion_tracker(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    user_memory.add_message_to_history(user_id, "user", "main_emotion_tracker")
    
    text = f"""<b>Твои графики тревожности, {name}! 📊</b>

Выбери тип графика:"""
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="😰 Ситуативная тревожность", callback_data="chart_situational_anxiety"))
    keyboard.add(InlineKeyboardButton(text="📊 Общая тревожность", callback_data="chart_general_anxiety"))
    keyboard.add(InlineKeyboardButton(text="📚 Справка", callback_data="help"))
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="main_start"))
    keyboard.adjust(2)
    
    await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
    user_memory.add_message_to_history(user_id, "assistant", "Графики тревожности")


# Обработчик начала ежедневной проверки
@dp.callback_query(lambda c: c.data == "daily_check_yes", PaidOnly())
async def start_daily_check(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    # Запоминаем согласие на проверку
    user_memory.add_message_to_history(user_id, "assistant", "Начало ежедневной проверки")
    
    await callback.message.answer(
        "<b>На сколько баллов тревога прямо сейчас? (0–10)</b>",
        reply_markup=get_anxiety_level_keyboard(),
        parse_mode="HTML"
    )

# Обработчик пропуска проверки
@dp.callback_query(lambda c: c.data == "daily_check_skip")
async def skip_daily_check(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    user_memory.add_message_to_history(user_id, "assistant", "Пользователь пропустил проверку")
    
    text = f"Понятно, {name}! Если захочешь проверить состояние — просто напиши /daily_check 💛\n\nИли используй кнопки ниже для быстрого доступа к функциям бота:"
    
    await callback.message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")

# Обработчик напоминания позже
@dp.callback_query(lambda c: c.data.startswith("daily_check_remind_") and PaidOnly())
async def remind_later(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    minutes = int(callback.data.split("_")[-1])
    user_memory.add_message_to_history(user_id, "assistant", f"Напоминание через {minutes} минут")
    
    await callback.message.answer(
        f"Хорошо! Напомню тебе через {minutes} минут 💛"
    )
    
    # Планируем напоминание в фоне
    asyncio.create_task(schedule_reminder(user_id, minutes))


async def schedule_reminder(user_id: int, minutes: int):
    """Планирует напоминание о ежедневной проверке"""
    try:
        # Ждем указанное количество минут
        await asyncio.sleep(minutes * 60)
        
        # Отправляем напоминание
        name = await get_user_name(user_id)
        await bot.send_message(
            chat_id=user_id,
            text=f"<b>{name}, время для ежедневной проверки! 💛</b>\n\n"
                 f"Как дела? Готов(а) ответить на несколько вопросов?",
            reply_markup=get_daily_check_start_keyboard(),
            parse_mode="HTML"
        )
        
        
    except Exception as e:
        print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")


# Глобальная переменная для отслеживания состояния проверки
daily_check_state = {}

# Функция для получения актуального имени пользователя
async def get_user_name(user_id: int, fallback_name: str = "друг") -> str:
    """Получает актуальное имя пользователя из памяти или возвращает fallback"""
    user_info = user_memory.get_user_memory(user_id)
    name = user_info.get("user_info", {}).get("name", fallback_name)
    return name if name != "друг" else fallback_name

# Обработчик выбора уровня тревоги
@dp.callback_query(lambda c: c.data.startswith("anxiety_level_"))
async def handle_anxiety_level(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    level = int(callback.data.split("_")[-1])
    
    # Инициализируем состояние пользователя, если его нет
    if user_id not in daily_check_state:
        daily_check_state[user_id] = {"step": "current_anxiety"}
    
    current_step = daily_check_state[user_id]["step"]
    
    if current_step == "current_anxiety":
        # Сохраняем текущий уровень тревоги
        user_memory.record_anxiety_level(user_id, level, "Текущий момент")
        user_memory.add_message_to_history(user_id, "user", f"Текущая тревога: {level}/10")
        
        # Переходим к следующему шагу
        daily_check_state[user_id]["current_anxiety"] = level
        daily_check_state[user_id]["step"] = "daily_anxiety"
        
        await callback.message.answer(
            "<b>Если смотреть на весь день, какая была средняя тревога? (0–10)</b>",
            reply_markup=get_anxiety_level_keyboard(),
            parse_mode="HTML"
        )
    
    elif current_step == "daily_anxiety":
        # Сохраняем средний уровень тревоги за день
        user_memory.record_anxiety_level(user_id, level, "Средний за день")
        user_memory.add_message_to_history(user_id, "user", f"Средняя тревога за день: {level}/10")
        
        # Переходим к следующему шагу - вопросы по очереди
        daily_check_state[user_id]["daily_anxiety"] = level
        daily_check_state[user_id]["step"] = "question_1"
        
        # Задаем первый вопрос
        await callback.message.answer(
            "<b>Что сильнее всего повлияло сегодня?</b>\n\n"
            "<i>Подсказки: Сон • Работа/Учёба • Деньги • Отношения • Здоровье • Неопределённость • Конфликт • Новости • Кофеин • Шум/толпа • Иное</i>",
            parse_mode="HTML"
        )

# Обработчик текстовых ответов на вопросы ежедневной проверки
@dp.message()
async def handle_daily_check_text(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, находится ли пользователь в процессе ежедневной проверки
    if user_id not in daily_check_state:
        # Если не в проверке, обрабатываем как обычное сообщение
        await handle_regular_message(message)
        return
    
    current_step = daily_check_state[user_id]["step"]
    
    if current_step == "question_1":
        # Ответ на первый вопрос
        await save_message(user_id, "user", message.text)

        user_memory.add_message_to_history(user_id, "user", f"Что повлияло: {message.text}")
        daily_check_state[user_id]["step"] = "question_2"
        daily_check_state[user_id]["answer_1"] = message.text
        
        await message.answer(
            "<b>Была ли мысль/ситуация, из-за которой тревога росла?</b>",
            parse_mode="HTML"
        )
    
    elif current_step == "question_2":
        # Ответ на второй вопрос
        await save_message(user_id, "user", message.text)

        user_memory.add_message_to_history(user_id, "user", f"Что усиливало тревогу: {message.text}")
        daily_check_state[user_id]["step"] = "question_3"
        daily_check_state[user_id]["answer_2"] = message.text
        
        await message.answer(
            "<b>Что помогало хотя бы немного?</b>",
            parse_mode="HTML"
        )
    
    elif current_step == "question_3":
        # Ответ на третий вопрос - завершаем сбор ответов
        await save_message(user_id, "user", message.text)

        user_memory.add_message_to_history(user_id, "user", f"Что помогало: {message.text}")
        daily_check_state[user_id]["answer_3"] = message.text
        
        # Собираем все ответы
        all_answers = f"Что повлияло: {daily_check_state[user_id]['answer_1']}\nЧто усиливало тревогу: {daily_check_state[user_id]['answer_2']}\nЧто помогало: {message.text}"
        daily_check_state[user_id]["user_answers"] = all_answers
        
        # Получаем текущий уровень тревоги из состояния
        if "current_anxiety" in daily_check_state[user_id]:
            current_anxiety = daily_check_state[user_id]["current_anxiety"]
            
            # Начинаем терапевтический диалог
            daily_check_state[user_id]["step"] = "therapy_dialog"
            daily_check_state[user_id]["message_count"] = 0
            
            # Для высокой тревоги добавляем этап выполнения техники
            if current_anxiety >= 7:
                daily_check_state[user_id]["anxiety_technique_completed"] = False
            
            # Принимаем решение на основе уровня тревоги
            if current_anxiety >= 7:
                # Высокая тревога - краткосрочные техники
                response = await get_high_anxiety_response(user_id, current_anxiety)
            elif current_anxiety >= 4:
                # Средняя тревога - стандартная терапевтическая беседа
                response = await get_medium_anxiety_response(user_id, current_anxiety)
            else:
                # Низкая тревога - превентивные меры
                response = await get_low_anxiety_response(user_id, current_anxiety)
            
            await message.answer(response, parse_mode="HTML")
            
            
        else:
            await message.answer("Спасибо за ответы! 💛")
            del daily_check_state[user_id]
    
    elif current_step == "therapy_dialog":
        # Продолжаем терапевтический диалог
        await save_message(user_id, "user", message.text)

        daily_check_state[user_id]["message_count"] += 1
        
        # Получаем контекст для терапевтического диалога
        context = prompt_processor.get_context_for_query(message.text)
        conversation_context = await get_conversation_context(user_id)
        user_summary = user_memory.get_user_summary(user_id)
        current_anxiety = daily_check_state[user_id]["current_anxiety"]
        user_answers = daily_check_state[user_id].get("user_answers", "")
        
        # Формируем системное сообщение для терапевтического диалога
        system_message = f"""Ты - заботливый психолог, ведущий терапевтический диалог после ежедневной проверки.

ВАЖНО: Ты говоришь от лица психолога Таисии Довиденко, ты ЖЕНСКОГО пола. 

Общие принципы
 1. Всегда начинай с валидации и признания эмоций: «Понимаю, это тяжело», «Нормально чувствовать себя так».
 2. Держи стиль спокойный, уважительный, без директив и приписок «правильно/неправильно».
 3. Формулируй ответы коротко: 1–3 предложения и один вопрос.
 4. Используй открытые вопросы, которые помогают исследовать, а не давать советы.
 5. Сохраняй малые шаги — предлагай простые эксперименты или маленькие вопросы, не перегружая.
 6. В кризисных или опасных ситуациях напоминай: «Я не заменяю терапевта. Если есть риск причинить себе вред, пожалуйста, обратись к специалистам или экстренной помощи».
 7. Очень важно не повторяться и не повторять свои вопросы! То есть нельзя писать подряд фразы типа "Понимаю, (имя)", "Понимаю, это тяжело", "Рада слышать, (имя)", "Как ты себя чувствуешь?" и так далее. Нужно стараться каждый раз формулировать по-новому, чтобы не создавать ощущение шаблонности и неискренности.

 Инструменты (подходы, которые нужно чередовать)

1. Сократовский диалог
 • Задавай уточняющие вопросы.
Помогай человеку конкретизировать свои мысли, чтобы он сам услышал их точнее.
Примеры:
– «Что именно ты имеешь в виду под этой мыслью?»
– «Какая часть ситуации кажется тебе самой трудной?»
 • Выявляй допущения.
Подталкивай к тому, чтобы заметить скрытые убеждения и предпосылки.
Примеры:
– «На чём основана эта мысль?»
– «Ты предполагаешь, что всё закончится плохо. Что даёт тебе такую уверенность?»
 • Показывай последствия.
Помогай исследовать, к чему ведёт та или иная мысль.
Примеры:
– «Если эта мысль верна, что это значит для тебя?»
– «Что изменится в твоей жизни, если поверить в эту версию?»
 • Предлагай альтернативы.
Давай возможность рассмотреть другую перспективу.
Примеры:
– «Какая другая версия могла бы быть?»
– «Что бы сказал кто-то, кто смотрит со стороны?»

2. КПТ (когнитивно-поведенческая терапия)
 • Разделяй факты и интерпретации.
Напоминай, что чувства и мысли не всегда отражают объективную реальность.
Примеры:
– «Что здесь факт, а что твоя интерпретация?»
– «Какие события реально произошли?»
 • Отслеживай автоматические мысли.
Помогай их замечать и формулировать вслух.
Примеры:
– «Какая мысль мелькнула, когда ты это почувствовал?»
– «Какая первая реакция появилась у тебя в голове?»
 • Выявляй когнитивные искажения.
Указывай мягко, когда человек обобщает, драматизирует, идеализирует.
Примеры:
– «Ты говоришь “всегда” или “никогда”. Были ли исключения?»
– «Ты уверен(а), что знаешь, что думают другие?»
 • Предлагай мини-эксперименты.
Помогай проверять мысли в реальности.
Примеры:
– «Хочешь завтра попробовать маленький шаг, чтобы проверить эту мысль?»
– «Что можно сделать, чтобы убедиться, что это правда/неправда?»

3. Психоаналитический взгляд (лёгкая форма)
 • Замечай повторяющиеся сценарии.
Подсвечивай, если человек снова и снова сталкивается с похожей ситуацией.
Примеры:
– «Ты описываешь похожие чувства в разных обстоятельствах. Не похоже ли это на повторяющийся сценарий?»
– «Есть ли в твоей жизни что-то, где ты снова оказываешься в той же роли?»
 • Обращай внимание на перенос.
Связывай нынешние реакции с прошлым опытом.
Примеры:
– «Тебе тяжело, когда он уходит. Напоминает ли это кого-то из прошлого?»
– «Ты переживаешь критику особенно остро. Кто ещё в твоей жизни критиковал так же?»
 • Выявляй защитные реакции.
Замечай и мягко озвучивай, когда человек отшучивается или обесценивает.
Примеры:
– «Ты смеёшься, рассказывая о боли. Может, это способ защититься?»
– «Ты говоришь, что это пустяк. А если допустить, что это важно — что тогда?»
 • Ищи внутренние голоса.
Исследуй, как чужие фигуры звучат внутри.
Примеры:
– «Когда ты критикуешь себя, чей это голос?»
– «Кого тебе напоминает этот тон?»

4. Гештальт и эмбодимент
 • Фокусируй внимание на теле.
Переводи разговор из мыслей в телесные ощущения.
Примеры:
– «Где в теле ты это чувствуешь?»
– «Какое это ощущение — тяжесть, сжатие, тепло?»
 • Используй образы и метафоры.
Дай возможность выразить эмоции через форму, цвет, звук.
Примеры:
– «Если бы это чувство было цветом или формой, каким оно было бы?»
– «Какой звук или движение лучше всего описывает это состояние?»
 • Дай телу высказаться.
Спроси, чего хочется телу сделать, чтобы завершить переживание.
Примеры:
– «Что твоё тело хочет сделать прямо сейчас?»
– «Какое движение или поза помогли бы тебе почувствовать завершённость?»
 • Заземляй в «здесь и сейчас».
Возвращай внимание к текущему моменту.
Примеры:
– «Что ты видишь, слышишь, ощущаешь прямо сейчас вокруг себя?»
– «Если на минуту забыть о ситуации — что есть реального рядом?»

Структура диалога
 1. Приветствие + валидация
Зачем: создать ощущение безопасности, показать, что эмоции допустимы.
 2. Фокусировка (выбор темы)
Зачем: сузить внимание до одной мысли или чувства, чтобы не расплываться.
 3. Разбор (Сократовский / КПТ)
Зачем: помочь увидеть мысль яснее, проверить её логику и факты.
 4. Углубление (психоанализ / эмбодимент)
Зачем: показать скрытые связи, паттерны или выразить то, что не помещается в слова.
Можно заменить: на более лёгкий вариант КПТ, если глубина небезопасна для пользователя.
 5. Заземление (малый шаг)
Зачем: вернуть чувство контроля и снизить напряжение.
Форматы: дыхание, движение, маленький эксперимент, запись мысли.
Можно ли пропустить: нет, иначе пользователь может остаться с «разобранным», но не собранным состоянием.
 6. Выход (итог)
Зачем: закрепить пользу разговора, осознать, что именно человек забирает с собой.
Можно заменить: на открытый вопрос «Что сейчас изменилось для тебя?»
 7. Завершение
Зачем: закрыть контакт, напомнить про границы и возможность вернуться.


ВАЖНО! Не задерживайся долго на одном из этапов. Если пользователь отвечает односложно, переходи в следующму этапу.
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:
{user_summary}

ТЕКУЩИЙ УРОВЕНЬ ТРЕВОГИ: {current_anxiety}/10

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ НА ВОПРОСЫ ЕЖЕДНЕВНОЙ ПРОВЕРКИ:
{user_answers}

КОНТЕКСТ ДИАЛОГА:
{conversation_context}

РЕЛЕВАНТНЫЙ КОНТЕКСТ ИЗ ПРОМПТА:
{context}

ВАЖНО: Ты ведешь терапевтический диалог после ежедневной проверки. 
- Отвечай как живой психолог, а не как бот
- Задавай уточняющие вопросы
- Проявляй эмпатию и понимание
- Предлагай конкретные техники и упражнения
- Продолжай диалог до тех пор, пока пользователь не подтвердит, что ему стало лучше
- Только когда пользователь скажет что-то вроде "мне стало лучше", "спасибо, помогло", "не хочу", "не знаю", "нет" - тогда давай закрывающее сообщение
- НЕ завершай диалог после "хорошо", "нормально", "ок", "понятно" - вместо этого уточни, что именно пользователь хочет обсудить
- НЕ задавай вопрос в каждом сообщении - это неестественно
- Можешь просто комментировать или поддерживать без вопроса
- Отвечай кратко, по-дружески и по-русски
- Используй имя пользователя
- Пиши полные сообщения, не обрезай текст
- КРИТИЧЕСКИ ВАЖНО: Используй ТОЛЬКО поддерживаемые Telegram HTML теги: <b>, <i>, <u>, <s>, <code>, <pre>. НЕ используй <p>, <br>, <div> или Markdown (*, **, _)
- ОБЯЗАТЕЛЬНО ссылайся на ответы пользователя на первые вопросы ежедневной проверки
- НЕ начинай сообщения с шаблонных фраз типа "Понимаю", "Я понимаю" - будь более естественным
- Если не знаешь, как к пользователю обращаться, спроси: "Как тебя лучше называть?"
- КРИТИЧЕСКИ ВАЖНО: НЕ повторяй одинаковые фразы, предложения или вопросы в диалоге
- НЕ используй повторяющиеся фразы типа "замечательно", "это замечательно", "давай разберемся вместе"
- Варьируй свои ответы: вместо "замечательно" используй "отлично", "здорово", "прекрасно", "хорошо"
- Вместо "давай разберемся" используй "расскажи подробнее", "интересно узнать", "что думаешь об этом"
- Каждое сообщение должно быть уникальным и развивать разговор дальше
- НЕ используй одинаковые конструкции типа "я всегда рядом", "я здесь для тебя", "заботься о себе"
 """

        # Проверяем, что сообщение не пустое
        if not message.text or message.text.strip() == "":
            await message.answer("Пожалуйста, напиши что-нибудь, чтобы я могла тебе помочь 💛")
            return
        
        # Получаем ответ от GPT-4o-mini
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message.text}
            ],
            max_tokens=400,
            temperature=0.8
        )
        
        bot_response = response.choices[0].message.content
        await save_message(user_id, "assistant", bot_response)
    
        # Сохраняем предпочтения пользователя, если он их упомянул
        await save_user_preferences(user_id, message.text)
        
        # Проверяем команду завершения диалога
        if message.text.lower().strip() in ["завершить", "завершить диалог"]:
            # Пользователь просит завершить диалог
            await message.answer(bot_response, parse_mode="HTML")
            
            
            # Добавляем завершающее сообщение через 2 секунды
            await asyncio.sleep(2)
            closing_message = await get_closing_message(user_id, current_anxiety)
            await message.answer(closing_message, reply_markup=get_main_keyboard(), parse_mode="HTML")
            
            # Очищаем состояние пользователя
            del daily_check_state[user_id]
            return
        
        # Отправляем ответ пользователю
        await message.answer(bot_response, parse_mode="HTML")
        await save_message(user_id, "assistant", bot_response)

        user_name = await get_user_name(user_id)

# ===== ОБРАБОТЧИКИ ДЛЯ НОВЫХ ФУНКЦИЙ =====

# Обработчики для КПТ техник

# Обработчики для КПТ техник
@dp.callback_query(lambda c: c.data == "cbt_breathing", PaidOnly())
async def handle_cbt_breathing(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    techniques = cbt_techniques.get_breathing_techniques()
    
    # Если только одна техника, показываем её сразу
    if len(techniques) == 1:
        technique_id = techniques[0]['id']
        instructions = cbt_techniques.get_technique_instructions(technique_id)
        # Сохраняем последнюю открытую технику
        user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
        await callback.message.answer(instructions, parse_mode="HTML")
    else:
        # Если несколько техник, показываем выбор
        text = f"""<b>Дыхательные техники, {name}! 🫁</b>

Выбери технику:"""
        
        keyboard = InlineKeyboardBuilder()
        for technique in techniques:
            keyboard.add(InlineKeyboardButton(
                text=technique['name'], 
                callback_data=f"technique_{technique['id']}"
            ))
        keyboard.adjust(1)
        
        await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "cbt_grounding", PaidOnly())
async def handle_cbt_grounding(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    techniques = cbt_techniques.get_grounding_techniques()
    
    # Если только одна техника, показываем её сразу
    if len(techniques) == 1:
        technique_id = techniques[0]['id']
        instructions = cbt_techniques.get_technique_instructions(technique_id)
        # Сохраняем последнюю открытую технику
        user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
        await callback.message.answer(instructions, parse_mode="HTML")
    else:
        # Если несколько техник, показываем выбор
        text = f"""<b>Техники заземления, {name}! 🌍</b>

Выбери технику:"""
        
        keyboard = InlineKeyboardBuilder()
        for technique in techniques:
            keyboard.add(InlineKeyboardButton(
                text=technique['name'], 
                callback_data=f"technique_{technique['id']}"
            ))
        keyboard.adjust(1)
        
        await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "cbt_relaxation", PaidOnly())
async def handle_cbt_relaxation(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    techniques = cbt_techniques.get_relaxation_techniques()
    
    # Если только одна техника, показываем её сразу
    if len(techniques) == 1:
        technique_id = techniques[0]['id']
        instructions = cbt_techniques.get_technique_instructions(technique_id)
        # Сохраняем последнюю открытую технику
        user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
        await callback.message.answer(instructions, parse_mode="HTML")
    else:
        # Если несколько техник, показываем выбор
        text = f"""<b>Техники релаксации, {name}! 😌</b>

Выбери технику:"""
        
        keyboard = InlineKeyboardBuilder()
        for technique in techniques:
            keyboard.add(InlineKeyboardButton(
                text=technique['name'], 
                callback_data=f"technique_{technique['id']}"
            ))
        keyboard.adjust(1)
        
        await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "cbt_mindfulness", PaidOnly())
async def handle_cbt_mindfulness(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    techniques = cbt_techniques.get_mindfulness_techniques()
    
    # Если только одна техника, показываем её сразу
    if len(techniques) == 1:
        technique_id = techniques[0]['id']
        instructions = cbt_techniques.get_technique_instructions(technique_id)
        # Сохраняем последнюю открытую технику
        user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
        await callback.message.answer(instructions, parse_mode="HTML")
    else:
        # Если несколько техник, показываем выбор
        text = f"""<b>Техники осознанности, {name}! 🧠</b>

Выбери технику:"""
        
        keyboard = InlineKeyboardBuilder()
        for technique in techniques:
            keyboard.add(InlineKeyboardButton(
                text=technique['name'], 
                callback_data=f"technique_{technique['id']}"
            ))
        keyboard.adjust(1)
        
        await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "cbt_cognitive", PaidOnly())
async def handle_cbt_cognitive(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    techniques = cbt_techniques.get_cognitive_techniques()
    
    # Если только одна техника, показываем её сразу
    if len(techniques) == 1:
        technique_id = techniques[0]['id']
        instructions = cbt_techniques.get_technique_instructions(technique_id)
        # Сохраняем последнюю открытую технику
        user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
        await callback.message.answer(instructions, parse_mode="HTML")
    else:
        # Если несколько техник, показываем выбор
        text = f"""<b>Когнитивные техники, {name}! 💭</b>

Выбери технику:"""
        
        keyboard = InlineKeyboardBuilder()
        for technique in techniques:
            keyboard.add(InlineKeyboardButton(
                text=technique['name'], 
                callback_data=f"technique_{technique['id']}"
            ))
        keyboard.adjust(1)
        
        await callback.message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

# Обработчик для конкретной техники
@dp.callback_query(lambda c: c.data.startswith("technique_"), PaidOnly())
async def handle_technique_selection(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    technique_id = callback.data.replace("technique_", "")
    
    technique = cbt_techniques.get_technique(technique_id)
    if not technique:
        await callback.message.answer("Техника не найдена")
        return
        
    # Получаем инструкции
    instructions = cbt_techniques.get_technique_instructions(technique_id)
    
    # Сохраняем последнюю открытую технику
    user_memory.update_user_info(user_id, {"last_technique_id": technique_id})
    
    # Отправляем инструкции сразу без дополнительных кнопок
    await callback.message.answer(instructions, parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith("pdf_"), PaidOnly())
async def handle_pdf_technique(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    technique_type = callback.data.replace("pdf_", "")
    technique_map = {
        "breathing": "breathing_478",
        "grounding": "grounding_54321", 
        "relaxation": "progressive_relaxation"
    }
    
    technique_id = technique_map.get(technique_type)
    if not technique_id:
        await callback.message.answer("Техника не найдена")
        return
    
    technique = cbt_techniques.get_technique(technique_id)
    if not technique:
        await callback.message.answer("Техника не найдена")
        return
    

# Обработчики для графиков прогресса
@dp.callback_query(lambda c: c.data == "chart_situational_anxiety", PaidOnly())
async def handle_chart_situational_anxiety(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    try:
        await callback.answer()
        # Получаем данные о ситуативной тревожности (текущий момент)
        user_memory_data = user_memory.get_user_memory(user_id)
        anxiety_levels = user_memory_data.get("anxiety_levels", [])
        
        # Фильтруем только записи "Текущий момент"
        situational_anxiety = [a for a in anxiety_levels if a.get("notes") == "Текущий момент"]
        
        if not situational_anxiety:
            await callback.message.answer("Недостаточно данных о ситуативной тревожности. Используй команду /daily_check для записи текущего уровня тревожности!")
            return
        
        # Создаем график
        chart_data = [{"level": a["level"], "timestamp": a["timestamp"]} for a in situational_anxiety]
        chart_base64 = progress_visualizer.create_situational_anxiety_chart(chart_data)
        
        # Отправляем график
        from io import BytesIO
        import base64
        from aiogram.types import BufferedInputFile
        
        image_data = base64.b64decode(chart_base64)
        photo = BufferedInputFile(image_data, filename="chart.png")
        
        await callback.message.answer_photo(
            photo=photo,
            caption=f"<b>Ситуативная тревожность 😰</b>\n\n"
                    "Этот график показывает твою тревожность в конкретные моменты времени. "
                    "Цветные зоны помогают оценить уровень: серая - зона комфорта, жёлтая - умеренная тревога, красная - высокая.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Ошибка при создании графика ситуативной тревожности: {e}")
        await callback.message.answer("Ошибка при создании графика. Попробуй позже.")

@dp.callback_query(lambda c: c.data == "chart_general_anxiety", PaidOnly())
async def handle_chart_general_anxiety(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    name = callback.from_user.first_name or "друг"
    
    try:
        await callback.answer()
        # Получаем данные об общей тревожности (средний за день)
        user_memory_data = user_memory.get_user_memory(user_id)
        anxiety_levels = user_memory_data.get("anxiety_levels", [])
        
        # Фильтруем только записи "Средний за день"
        general_anxiety = [a for a in anxiety_levels if a.get("notes") == "Средний за день"]
        
        if not general_anxiety:
            await callback.message.answer("Недостаточно данных об общей тревожности. Используй команду /daily_check для записи среднего уровня тревожности за день!")
            return
        
        # Создаем график
        chart_data = [{"level": a["level"], "timestamp": a["timestamp"]} for a in general_anxiety]
        chart_base64 = progress_visualizer.create_general_anxiety_chart(chart_data)
        
        # Отправляем график
        from io import BytesIO
        import base64
        from aiogram.types import BufferedInputFile
        
        image_data = base64.b64decode(chart_base64)
        photo = BufferedInputFile(image_data, filename="chart.png")
        
        await callback.message.answer_photo(
            photo=photo,
            caption=f"<b>Общая тревожность 📊</b>\n\n"
                    "Этот график показывает твой средний уровень тревожности за день. "
                    "Цветные зоны помогают оценить уровень: серая - зона комфорта, жёлтая - умеренная тревога, красная - высокая.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Ошибка при создании графика общей тревожности: {e}")
        await callback.message.answer("Ошибка при создании графика. Попробуй позже.")

async def handle_regular_message(message: types.Message):
    try:
        user_id = message.from_user.id
        await save_message(user_id, "user", message.text)
        # Проверяем, не является ли это записью эмоции или мысли
        if await handle_emotion_or_thought_tracking(message):
            return

        context = prompt_processor.get_context_for_query(message.text)
        conversation_context = await get_conversation_context(user_id)

        user_summary = user_memory.get_user_summary(user_id)

        system_message = f"""Ты - заботливый психолог, ведущий терапевтический диалог после ежедневной проверки.

ВАЖНО: Ты говоришь от лица психолога Таисии Довиденко, ты ЖЕНСКОГО пола. 

Общие принципы
 1. Всегда начинай с валидации и признания эмоций: «Понимаю, это тяжело», «Нормально чувствовать себя так».
 2. Держи стиль спокойный, уважительный, без директив и приписок «правильно/неправильно».
 3. Формулируй ответы коротко: 1–3 предложения и один вопрос.
 4. Используй открытые вопросы, которые помогают исследовать, а не давать советы.
 5. Сохраняй малые шаги — предлагай простые эксперименты или маленькие вопросы, не перегружая.
 6. В кризисных или опасных ситуациях напоминай: «Я не заменяю терапевта. Если есть риск причинить себе вред, пожалуйста, обратись к специалистам или экстренной помощи».
 7. Очень важно не повторяться и не повторять свои вопросы! То есть нельзя писать подряд фразы типа "Понимаю, (имя)", "Понимаю, это тяжело", "Рада слышать, (имя)", "Как ты себя чувствуешь?" и так далее. Нужно стараться каждый раз формулировать по-новому, чтобы не создавать ощущение шаблонности и неискренности.

Инструменты (подходы, которые нужно чередовать)

1. Сократовский диалог
 • Задавай уточняющие вопросы.
Помогай человеку конкретизировать свои мысли, чтобы он сам услышал их точнее.
Примеры:
– «Что именно ты имеешь в виду под этой мыслью?»
– «Какая часть ситуации кажется тебе самой трудной?»
 • Выявляй допущения.
Подталкивай к тому, чтобы заметить скрытые убеждения и предпосылки.
Примеры:
– «На чём основана эта мысль?»
– «Ты предполагаешь, что всё закончится плохо. Что даёт тебе такую уверенность?»
 • Показывай последствия.
Помогай исследовать, к чему ведёт та или иная мысль.
Примеры:
– «Если эта мысль верна, что это значит для тебя?»
– «Что изменится в твоей жизни, если поверить в эту версию?»
 • Предлагай альтернативы.
Давай возможность рассмотреть другую перспективу.
Примеры:
– «Какая другая версия могла бы быть?»
– «Что бы сказал кто-то, кто смотрит со стороны?»

2. КПТ (когнитивно-поведенческая терапия)
 • Разделяй факты и интерпретации.
Напоминай, что чувства и мысли не всегда отражают объективную реальность.
Примеры:
– «Что здесь факт, а что твоя интерпретация?»
– «Какие события реально произошли?»
 • Отслеживай автоматические мысли.
Помогай их замечать и формулировать вслух.
Примеры:
– «Какая мысль мелькнула, когда ты это почувствовал?»
– «Какая первая реакция появилась у тебя в голове?»
 • Выявляй когнитивные искажения.
Указывай мягко, когда человек обобщает, драматизирует, идеализирует.
Примеры:
– «Ты говоришь “всегда” или “никогда”. Были ли исключения?»
– «Ты уверен(а), что знаешь, что думают другие?»
 • Предлагай мини-эксперименты.
Помогай проверять мысли в реальности.
Примеры:
– «Хочешь завтра попробовать маленький шаг, чтобы проверить эту мысль?»
– «Что можно сделать, чтобы убедиться, что это правда/неправда?»

3. Психоаналитический взгляд (лёгкая форма)
 • Замечай повторяющиеся сценарии.
Подсвечивай, если человек снова и снова сталкивается с похожей ситуацией.
Примеры:
– «Ты описываешь похожие чувства в разных обстоятельствах. Не похоже ли это на повторяющийся сценарий?»
– «Есть ли в твоей жизни что-то, где ты снова оказываешься в той же роли?»
 • Обращай внимание на перенос.
Связывай нынешние реакции с прошлым опытом.
Примеры:
– «Тебе тяжело, когда он уходит. Напоминает ли это кого-то из прошлого?»
– «Ты переживаешь критику особенно остро. Кто ещё в твоей жизни критиковал так же?»
 • Выявляй защитные реакции.
Замечай и мягко озвучивай, когда человек отшучивается или обесценивает.
Примеры:
– «Ты смеёшься, рассказывая о боли. Может, это способ защититься?»
– «Ты говоришь, что это пустяк. А если допустить, что это важно — что тогда?»
 • Ищи внутренние голоса.
Исследуй, как чужие фигуры звучат внутри.
Примеры:
– «Когда ты критикуешь себя, чей это голос?»
– «Кого тебе напоминает этот тон?»

4. Гештальт и эмбодимент
 • Фокусируй внимание на теле.
Переводи разговор из мыслей в телесные ощущения.
Примеры:
– «Где в теле ты это чувствуешь?»
– «Какое это ощущение — тяжесть, сжатие, тепло?»
 • Используй образы и метафоры.
Дай возможность выразить эмоции через форму, цвет, звук.
Примеры:
– «Если бы это чувство было цветом или формой, каким оно было бы?»
– «Какой звук или движение лучше всего описывает это состояние?»
 • Дай телу высказаться.
Спроси, чего хочется телу сделать, чтобы завершить переживание.
Примеры:
– «Что твоё тело хочет сделать прямо сейчас?»
– «Какое движение или поза помогли бы тебе почувствовать завершённость?»
 • Заземляй в «здесь и сейчас».
Возвращай внимание к текущему моменту.
Примеры:
– «Что ты видишь, слышишь, ощущаешь прямо сейчас вокруг себя?»
– «Если на минуту забыть о ситуации — что есть реального рядом?»

Структура диалога
 1. Приветствие + валидация
Зачем: создать ощущение безопасности, показать, что эмоции допустимы.
 2. Фокусировка (выбор темы)
Зачем: сузить внимание до одной мысли или чувства, чтобы не расплываться.
 3. Разбор (Сократовский / КПТ)
Зачем: помочь увидеть мысль яснее, проверить её логику и факты.
 4. Углубление (психоанализ / эмбодимент)
Зачем: показать скрытые связи, паттерны или выразить то, что не помещается в слова.
Можно заменить: на более лёгкий вариант КПТ, если глубина небезопасна для пользователя.
 5. Заземление (малый шаг)
Зачем: вернуть чувство контроля и снизить напряжение.
Форматы: дыхание, движение, маленький эксперимент, запись мысли.
Можно ли пропустить: нет, иначе пользователь может остаться с «разобранным», но не собранным состоянием.
 6. Выход (итог)
Зачем: закрепить пользу разговора, осознать, что именно человек забирает с собой.
Можно заменить: на открытый вопрос «Что сейчас изменилось для тебя?»
 7. Завершение
Зачем: закрыть контакт, напомнить про границы и возможность вернуться.


ВАЖНО! Не задерживайся долго на одном из этапов. Если пользователь отвечает односложно, переходи в следующму этапу.
ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:
{user_summary}

КОНТЕКСТ ДИАЛОГА:
{conversation_context}

РЕЛЕВАНТНЫЙ КОНТЕКСТ ИЗ ПРОМПТА:
{context}

ВАЖНО: Ты ведешь терапевтический диалог после ежедневной проверки. 
- Отвечай как живой психолог, а не как бот
- Задавай уточняющие вопросы
- Проявляй эмпатию и понимание
- Предлагай конкретные техники и упражнения
- Продолжай диалог до тех пор, пока пользователь не подтвердит, что ему стало лучше
- Только когда пользователь скажет что-то вроде "мне стало лучше", "спасибо, помогло", "не хочу", "не знаю", "нет" - тогда давай закрывающее сообщение
- НЕ завершай диалог после "хорошо", "нормально", "ок", "понятно" - вместо этого уточни, что именно пользователь хочет обсудить
- НЕ задавай вопрос в каждом сообщении - это неестественно
- Можешь просто комментировать или поддерживать без вопроса
- Отвечай кратко, по-дружески и по-русски
- Используй имя пользователя
- Пиши полные сообщения, не обрезай текст
- КРИТИЧЕСКИ ВАЖНО: Используй ТОЛЬКО поддерживаемые Telegram HTML теги: <b>, <i>, <u>, <s>, <code>, <pre>. НЕ используй <p>, <br>, <div> или Markdown (*, **, _)
- ОБЯЗАТЕЛЬНО ссылайся на ответы пользователя на первые вопросы ежедневной проверки
- НЕ начинай сообщения с шаблонных фраз типа "Понимаю", "Я понимаю" - будь более естественным
- Если не знаешь, как к пользователю обращаться, спроси: "Как тебя лучше называть?"
- КРИТИЧЕСКИ ВАЖНО: НЕ повторяй одинаковые фразы, предложения или вопросы в диалоге
- НЕ используй повторяющиеся фразы типа "замечательно", "это замечательно", "давай разберемся вместе"
- Варьируй свои ответы: вместо "замечательно" используй "отлично", "здорово", "прекрасно", "хорошо"
- Вместо "давай разберемся" используй "расскажи подробнее", "интересно узнать", "что думаешь об этом"
- Каждое сообщение должно быть уникальным и развивать разговор дальше
- НЕ используй одинаковые конструкции типа "я всегда рядом", "я здесь для тебя", "заботься о себе"
"""

        # Проверяем, что сообщение не пустое
        if not message.text or message.text.strip() == "":
            await message.answer("Пожалуйста, напиши что-нибудь, чтобы я могла тебе помочь 💛")
            return

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message.text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        bot_response = response.choices[0].message.content

        # Команда завершения диалога
        if message.text.lower().strip() in ["завершить", "завершить диалог"]:
            await message.answer(bot_response, parse_mode="HTML")

            # если нет последних данных о тревоге, используем безопасное значение 3
            anxiety_level = 3
            closing_message = await get_closing_message(user_id, anxiety_level)
            await message.answer(closing_message, reply_markup=get_main_keyboard(), parse_mode="HTML")
            return

        await message.answer(bot_response, parse_mode="HTML")
        await save_message(user_id, "assistant", bot_response)

    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")
        await message.answer("Извини, произошла ошибка при обработке твоего сообщения. Попробуй еще раз.")

# Функция для обработки записи эмоций и мыслей
async def handle_emotion_or_thought_tracking(message: types.Message) -> bool:
    """Обрабатывает сообщения, связанные с трекингом эмоций и мыслей"""
    user_id = message.from_user.id
    text = message.text.lower()
    
    
    
    return False



async def get_high_anxiety_response(user_id: int, anxiety_level: int) -> str:
    """Ответ для высокой тревоги (7-10 баллов)"""
    name = await get_user_name(user_id)
    
    return f"""<b>{name}, вижу, что тревога сейчас высокая ({anxiety_level}/10).</b>

Сейчас самое важное - снизить уровень тревоги, а позже мы обсудим, как можно решить твою проблему

Давай попробуем технику <b>"4-7-8"</b> - она поможет быстро успокоиться:
- <b>Вдох</b> на 4 счёта
- <b>Задержка</b> на 7 счётов  
- <b>Выдох</b> на 8 счётов
- Повтори 3-4 раза

Попробуй прямо сейчас и скажи, как себя чувствуешь после этого упражнения? Стало ли легче дышать?"""

async def get_medium_anxiety_response(user_id: int, anxiety_level: int) -> str:
    """Ответ для средней тревоги (4-6 баллов)"""
    name = await get_user_name(user_id)
    
    return f"""<b>{name}, тревога на среднем уровне ({anxiety_level}/10).</b>

Это управляемый уровень, но всё равно неприятно. Давай разберёмся вместе \U0001F49B

Расскажи мне подробнее - что именно тебя беспокоит? Какие мысли крутятся в голове? Это поможет мне лучше понять ситуацию."""

async def get_low_anxiety_response(user_id: int, anxiety_level: int) -> str:
    """Ответ для низкой тревоги (0-3 балла)"""
    name = await get_user_name(user_id)
    
    return f"""<b>Отлично, {name}! Тревога на низком уровне ({anxiety_level}/10).</b>

Ты молодец, что держишься спокойно! 

Расскажи мне - что помогает тебе оставаться в таком хорошем состоянии? Это поможет мне лучше понять твои стратегии и поддержать тебя."""

# Функция для сохранения предпочтений пользователя
async def save_user_preferences(user_id: int, message_text: str):
    """Сохраняет предпочтения пользователя на основе его сообщений"""
    try:
        text_lower = message_text.lower()
        preferences = {}
        
        # Определяем предпочтительную активность
        if any(word in text_lower for word in ["прогулка", "гулять", "воздух", "улица"]):
            preferences["preferred_activity"] = "прогулка"
        elif any(word in text_lower for word in ["медитация", "медитировать", "дыхание", "дыхательные"]):
            preferences["preferred_activity"] = "медитация"
        elif any(word in text_lower for word in ["заземление", "заземляться", "5-4-3-2-1"]):
            preferences["preferred_activity"] = "заземление"
        
        # Определяем предпочтительное время
        if any(word in text_lower for word in ["утром", "утро", "рано", "9", "10"]):
            preferences["preferred_time"] = "09:00"
        elif any(word in text_lower for word in ["днем", "день", "12", "13", "14"]):
            preferences["preferred_time"] = "12:00"
        elif any(word in text_lower for word in ["вечером", "вечер", "18", "19", "20"]):
            preferences["preferred_time"] = "18:00"
        
        # Сохраняем предпочтения, если они найдены
        if preferences:
            user_memory.update_preferences(user_id, preferences)
            
    except Exception as e:
        print(f"Ошибка при сохранении предпочтений: {e}")

# Функция для закрытия диалога с персонализированными рекомендациями
async def get_closing_message(user_id: int, anxiety_level: int) -> str:
    """Генерация закрывающего сообщения с рекомендациями"""
    name = await get_user_name(user_id)
    
    # Получаем историю пользователя для персонализации
    user_memory_data = user_memory.get_user_memory(user_id)
    conversation_history = user_memory_data.get("conversation_history", [])
    
    # Определяем пол пользователя (сохраняем навсегда)
    user_gender = user_memory_data.get("user_info", {}).get("gender", "neutral")  # Получаем сохраненный пол
    
    # Если пол еще не определен, определяем его с помощью нейросети
    if user_gender == "neutral":
        # Собираем все сообщения пользователя для анализа
        user_messages = []
        for msg in conversation_history[-30:]:  # Последние 30 сообщений
            if msg.get("role") == "user":
                user_messages.append(msg.get("content", ""))
        
        if user_messages:
            # Объединяем сообщения для анализа
            combined_text = " ".join(user_messages)
            
            # Используем GPT для определения пола по склонениям
            gender_prompt = f"""Проанализируй текст и определи пол автора по склонениям глаголов и прилагательных. 
            Обрати внимание на окончания: -а, -я (женский), -л, -л (мужской), -ла, -ла (женский).
            
            Текст: "{combined_text[:1000]}"
            
            Ответь только одним словом: male, female или neutral"""
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": gender_prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
                
                gender_result = response.choices[0].message.content.strip().lower()
                if gender_result in ["male", "female"]:
                    user_gender = gender_result
                    # Сохраняем пол навсегда
                    user_memory.update_user_info(user_id, {"gender": user_gender})
                    print(f"DEBUG: Нейросеть определила и сохранила пол: {user_gender}")
                else:
                    print(f"DEBUG: Нейросеть вернула неопределенный результат: {gender_result}")
                    
            except Exception as e:
                print(f"DEBUG: Ошибка при определении пола: {e}")
                user_gender = "neutral"
    else:
        print(f"DEBUG: Используем сохраненный пол: {user_gender}")
    
    # Определяем склонения в зависимости от пола
    if user_gender == "male":
        achievement = "отлично справился"
        action = "поделился"
        alone = "ты не один"
    elif user_gender == "female":
        achievement = "отлично справилась"
        action = "поделилась"
        alone = "ты не одна"
    else:
        achievement = "отлично справился(ась)"
        action = "поделился(ась)"
        alone = "ты не один(а)"
    
    # Определяем последнюю открытую технику
    last_technique_id = user_memory_data.get("user_info", {}).get("last_technique_id")
    
    if last_technique_id:
        # Получаем информацию о последней технике
        last_technique = cbt_techniques.get_technique(last_technique_id)
        if last_technique:
            favorite_technique = last_technique['name']
        else:
            favorite_technique = "дыхание 4-7-8"  # По умолчанию
    else:
        favorite_technique = "дыхание 4-7-8"  # По умолчанию
    
    # Определяем микро-действие на завтра на основе уровня тревоги
    if anxiety_level >= 7:
        micro_actions = [
            "5 минут дыхательных упражнений",
            "техника заземления",
            "короткая медитация"
        ]
    elif anxiety_level >= 4:
        micro_actions = [
            "короткая прогулка на свежем воздухе",
            "техника заземления",
            "медитация 3 минуты"
        ]
    else:
        micro_actions = [
            "короткая прогулка на свежем воздухе",
            "медитация 3 минуты",
            "техника благодарности"
        ]
    
    # Выбираем действие случайно из трех вариантов
    import random
    micro_action = random.choice(micro_actions)
    
    # Получаем сохраненное время или используем по умолчанию
    saved_time = user_memory_data.get("user_info", {}).get("daily_check_time", "18:30")
    suggested_time = saved_time
    
    return f"""<b>Ты сегодня {achievement} - особенно с тем, что {action} своими чувствами.</b>

Если накроет - у тебя под рукой <b>{favorite_technique}</b>.

Мы договорились: <b>{micro_action}</b> завтра в <b>{suggested_time}</b>. Я спрошу, как прошло 💛

До встречи, {name}! Помни: {alone}, и тревога временна """



# Запуск бота
async def load_existing_reminders():
    """Загружает существующие напоминания при запуске бота"""
    try:
        memories = user_memory.memories
        for user_id_str, user_data in memories.items():
            user_id = int(user_id_str)
            daily_check_time = user_data.get("user_info", {}).get("daily_check_time")
            if daily_check_time:
                asyncio.create_task(schedule_daily_reminder(user_id, daily_check_time))
    except Exception as e:
        print(f"❌ Ошибка при загрузке существующих напоминаний: {e}")

async def main():
    await create_db()
    asyncio.create_task(check_subscriptions())
    await load_existing_reminders()
    await dp.start_polling(bot)
    await wait_for_db()

from aiogram.types import ErrorEvent

@dp.errors()
async def errors_handler(event: ErrorEvent):
    logging.exception(f"⚠️ Ошибка при обработке апдейта: {event.exception}")
    return True

if __name__ == "__main__":
    asyncio.run(main())
