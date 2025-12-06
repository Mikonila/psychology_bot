#!/bin/bash
set -e

SERVER="root@77.73.232.142"
TARGET="/root/psbot"

echo "🚀 Синхронизирую проект с сервером $SERVER..."
rsync -avz --delete \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.json' \
  --exclude 'data/postgres' \
  ./ "$SERVER:$TARGET"

echo "🔄 Перезапускаю контейнер на сервере..."
ssh "$SERVER" "cd $TARGET && docker-compose down && docker-compose up -d --build"

echo "✅ Деплой завершён!"
