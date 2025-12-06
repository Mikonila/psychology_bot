# db_utils.py
from datetime import datetime, timedelta
from sqlalchemy import insert, select, text
from db_start import async_session
from db_models import users_table, messages_table

async def update_user_subscription(user_id: int, amount, period_label: str | None = None):
    try:
        amount = float(amount)
    except Exception:
            amount = 0.0

    if period_label is None:
        period_label = "3 месяца" if amount >= 4490 else "Ежемесячная"

    days = 90 if "3" in period_label else 30
    access_until = (datetime.utcnow() + timedelta(days=days)).date()

    async with async_session() as session:
        stmt = insert(users_table).values(
            user_id=user_id,
            is_paid=True,
            subscription_status="Активна",
            subscription_period=period_label,
            subscription_price=int(amount),
            currency="₽",
            next_payment_date=access_until,
            access_until=access_until,
        ).on_conflict_do_update(
            index_elements=[users_table.c.user_id],
            set_={
                "is_paid": True,
                "subscription_status": "Активна",
                "subscription_period": period_label,
                "subscription_price": int(amount),
                "currency": "₽",
                "next_payment_date": access_until,
                "access_until": access_until,
            }
        )
        await session.execute(stmt)
        await session.commit()

from datetime import datetime
from sqlalchemy import insert
from db_start import async_session
from db_models import messages_table

async def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение пользователя или ассистента в таблицу messages."""
    async with async_session() as session:
        await session.execute(
            insert(messages_table).values(
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.utcnow()  # ✅ теперь это TIMESTAMP, не строка
            )
        )
        await session.commit()


async def get_conversation_context(user_id: int, limit: int = 20) -> str:
    async with async_session() as session:
        res = await session.execute(
            text("""
                SELECT role, content
                FROM messages
                WHERE user_id = :uid
                ORDER BY id DESC
                LIMIT :lim
            """),
            {"uid": user_id, "lim": limit}
        )
        rows = res.fetchall()
    # Возвращаем в прямом порядке (от старых к новым)
    lines = []
    for r in reversed(rows):
        prefix = "Пользователь:" if r.role == "user" else "Ассистент:"
        lines.append(f"{prefix} {r.content}")
    return "\n".join(lines)
