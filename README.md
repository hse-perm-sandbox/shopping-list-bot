# shopping-list-bot
Telegram-бот для удобного создания и управления списками покупок.

## Описание

Этот Telegram-бот предназначен для управления списками покупок.  
Он позволяет создавать списки, добавлять категории и товары, делиться списками с другими пользователями с помощью одноразового токена.

## Функционал

- Создание и удаление списков покупок  
- Добавление и удаление категорий и товаров  
- Просмотр списков в виде дерева 
- Совместный доступ к спискам через одноразовый токен  

## Установка и запуск приложения

### Предварительные требования

- Python 3.12  
- Python venv  


### 1. Шаги установки

```bash
# Клонируйте репозиторий
git clone https://github.com/hse-perm-sandbox/shopping-list-bot.git
cd shopping-list-bot

# Создайте виртуальное окружение
python3 -m venv .venv

# Активация окружения
.\.venv\Scripts\activate

# Установите Poetry
pip install poetry

# Установите зависимости
poetry install
```
### 2. Создание .env файла
Создайте .env в корне проекта и добавьте туда следующие переменные окружения:
```bash
TG_TOKEN=your_telegram_bot_token
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shoppinglist
SECRET_KEY=your_secret_key
```
### 3. Запуск приложения
```bash
poetry run python src/main.py
```
## Конфигурация

Приложение использует файл `.env` для хранения конфигурационных переменных.  

```env
# Telegram Bot Token
TG_TOKEN=your_telegram_bot_token

# Параметры подключения к базе данных PostgreSQL
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shoppinglist

# Секретный ключ для токенов доступа (JWT)
SECRET_KEY=your_secret_key
