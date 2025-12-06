from bot import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from db_utils import update_user_subscription
from db_start import async_session
from db_models import users_table
from sqlalchemy import select


def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌱 Старт", callback_data="main_start"),
        InlineKeyboardButton(text="🕯 Заполнить день", callback_data="main_daily_check"),
    )
    builder.row(
        InlineKeyboardButton(text="🤲 Связаться с куратором", callback_data="main_support"),
        InlineKeyboardButton(text="📘 Получить методичку", callback_data="main_pdf"),
    )
    builder.row(
        InlineKeyboardButton(text="📈 Мой прогресс", callback_data="main_emotion_tracker"),
        InlineKeyboardButton(text="🕊 Информация о подписке", callback_data="subscription_info"),
    )
    return builder.as_markup()


async def check_payment_status(payment_id, user_id):
    """
    Проверяет статус платежа по ID.
    Если успешен — обновляет данные в БД и отправляет приветственное сообщение.
    """
    from yookassa import Payment
    try:
        payment = Payment.find_one(payment_id)
        status = payment.status
        amount = float(payment.amount.value)

        print(f"🔎 Проверяю статус платежа {payment_id}: {status}")

        if status == "succeeded":
            print(f"✅ Платёж {payment_id} успешен! Обновляем пользователя {user_id} в PostgreSQL.")
            if int(amount) == 4490:
                await update_user_subscription(user_id, 4490, "3 месяца")
            else:
                await update_user_subscription(user_id, 1990, "Ежемесячная")

            access_until = datetime.now() + timedelta(days=90 if amount == 4490 else 30)
            date_str = access_until.strftime('%d.%m.%Y')

            # 🕊 Отправляем вступительное сообщение
            text = f"""<b>🤍 Добро пожаловать в «Я – Спокойно»</b>

Это пространство, где можно выгружать тревогу, видеть её со стороны и шаг за шагом возвращать себе спокойствие.

Что тебя ждёт:
 • Таблицы состояний — отмечаешь тревогу, замечаешь закономерности и учишься лучше понимать себя.
 • Диалог с ботом — он задаёт вопросы, помогает разложить всё по полочкам и предлагает техники.
 • Таблицы прогресса — видишь, как шаг за шагом меняется твоё состояние.
 • Методичка на 100 страниц — там собраны ключевые техники работы с тревогой, советы по образу жизни и готовый 10-дневный план практик. Можно пробовать разные упражнения и выбрать те, что действительно подходят именно тебе.

<b>Доступ к материалам открыт до {date_str}</b>.
"""

            await bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )

            return True
        else:
            print(f"⚠️ Платёж {payment_id} ещё не завершён (status={status})")
            return False

    except Exception as ex:
        print(f"❌ Ошибка при проверке платежа {payment_id}: {ex}")
        return False



async def check_subscriptions():
    """Проверяет подписки и отправляет напоминания пользователям."""
    while True:
        now = datetime.now().date()
        async with async_session() as session:
            result = await session.execute(select(users_table))
            users = result.fetchall()

        for row in users:
            user_id = row.user_id
            if not row.is_paid or not row.access_until:
                continue

            access_until = row.access_until
            days_left = (access_until - now).days
            days_after = (now - access_until).days

            try:
                if days_left == 3:
                    await bot.send_message(
                        user_id,
                        "🤍 <b>Твоя подписка подходит к концу</b>\n"
                        "Осталось всего <i>три дня</i>, чтобы бот продолжал сопровождать тебя: "
                        "помогать разбирать тревогу, вести таблицы и отмечать прогресс.\n\n"
                        "Продли подписку заранее и продолжай спокойно двигаться вперёд.",
                        parse_mode="HTML"
                    )
                elif days_left == 1:
                    await bot.send_message(
                        user_id,
                        "🕊 <b>Завтра доступ закончится</b>\n"
                        "<i>Все твои записи сохранятся</i>, но новые техники и сопровождение бота станут недоступны.\n\n"
                        "Продли подписку сегодня — и продолжи путь без перерыва.",
                        parse_mode="HTML"
                    )
                elif days_after == 1:
                    await bot.send_message(
                        user_id,
                        "🌱 <b>Подписка завершилась</b>\n"
                        "У тебя остались все записи и таблицы, но бот больше не сможет отвечать.\n\n"
                        "Продли доступ, чтобы вернуться к поддержке и спокойствию.",
                        parse_mode="HTML"
                    )
                elif days_after == 3:
                    await bot.send_message(
                        user_id,
                        "🤍 <b>Прошло три дня без бота</b>\n"
                        "Если тревога возвращается — мы рядом.\n\n"
                        "Продли подписку и продолжай путь к спокойствию.",
                        parse_mode="HTML"
                    )
            except Exception as e:
                print(f"⚠️ Ошибка при уведомлении {user_id}: {e}")

        await asyncio.sleep(24 * 60 * 60)  # проверяем раз в сутки


if __name__ == "__main__":
    print("🕊 Планировщик подписок запущен...")
    asyncio.run(check_subscriptions())