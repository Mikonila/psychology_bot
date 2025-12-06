# create_db.py
import asyncio
from sqlalchemy import text
from db_start import engine

DDL = """
CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT PRIMARY KEY,
  is_paid BOOLEAN NOT NULL DEFAULT FALSE,
  subscription_status VARCHAR(50),
  subscription_period VARCHAR(50),
  subscription_price INTEGER,
  currency VARCHAR(8),
  next_payment_date DATE,
  access_until DATE
);

CREATE TABLE IF NOT EXISTS messages (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  role VARCHAR(16) NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
"""

async def create_db():
    async with engine.begin() as conn:
        for stmt in DDL.strip().split(";\n\n"):
            s = stmt.strip()
            if s:
                await conn.execute(text(s))

if __name__ == "__main__":
    asyncio.run(create_db())
