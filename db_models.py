# db_models.py
from sqlalchemy import (
    Table, Column, BigInteger, Integer, String, Boolean, Date, Text,
    MetaData
)

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("user_id", BigInteger, primary_key=True),
    Column("is_paid", Boolean, nullable=False, default=False),
    Column("subscription_status", String(50), nullable=True),
    Column("subscription_period", String(50), nullable=True),
    Column("subscription_price", Integer, nullable=True),
    Column("currency", String(8), nullable=True),
    Column("next_payment_date", Date, nullable=True),
    Column("access_until", Date, nullable=True),
)

messages_table = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, nullable=False, index=True),
    Column("role", String(16), nullable=False),      # 'user' | 'assistant'
    Column("content", Text, nullable=False),
    Column("timestamp", String(32), nullable=False), # ISO строка, проще хранить так
)
