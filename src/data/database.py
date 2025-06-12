import asyncpg
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Подключение к базе данных и создание пула соединений"""
        try:
            self.pool = await asyncpg.create_pool(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT", 5432)
            )
            print("✅ Подключение к БД установлено")
            await self._initialize_tables()
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")

    async def _initialize_tables(self):
        """Создание всех таблиц при первом запуске"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Таблица списков
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lists (
                    list_id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    name TEXT NOT NULL,
                    UNIQUE (user_id, name)
                );
            """)

            # Таблица категорий
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id SERIAL PRIMARY KEY,
                    list_id INT REFERENCES lists(list_id),
                    name TEXT NOT NULL,
                    UNIQUE (list_id, name)
                );
            """)

            # Таблица товаров
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    item_id SERIAL PRIMARY KEY,
                    category_id INT REFERENCES categories(category_id),
                    name TEXT NOT NULL,
                    bought BOOLEAN DEFAULT FALSE,
                    UNIQUE (category_id, name)
                );
            """)

    # Работа с пользователями
    async def add_user(self, user_id, username):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username)
                VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING
            """, user_id, username)

    # Получить все списки пользователя
    async def get_lists(self, user_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT name FROM lists WHERE user_id = $1", user_id)
            return [row['name'] for row in rows]

    # Добавить список
    async def add_list(self, user_id, list_name):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO lists (user_id, name)
                VALUES ($1, $2) ON CONFLICT (user_id, name) DO NOTHING
            """, user_id, list_name)

    # Получить ID списка по имени
    async def get_list_id(self, user_id, list_name):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT list_id FROM lists WHERE user_id = $1 AND name = $2
            """, user_id, list_name)
            return result

    # Получить категории в списке
    async def get_categories(self, list_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT name FROM categories WHERE list_id = $1", list_id)
            return [row['name'] for row in rows]

    # Добавить категорию
    async def add_category(self, list_id, category_name):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO categories (list_id, name)
                VALUES ($1, $2) ON CONFLICT (list_id, name) DO NOTHING
            """, list_id, category_name)

    # Получить ID категории по имени
    async def get_category_id(self, list_id, category_name):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT category_id FROM categories WHERE list_id = $1 AND name = $2
            """, list_id, category_name)
            return result

    # Добавить товар в категорию
    async def add_item(self, category_id, item_name):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO items (category_id, name)
                VALUES ($1, $2) ON CONFLICT (category_id, name) DO NOTHING
            """, category_id, item_name)

    # Получить товары в категории
    async def get_items(self, category_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT name, bought FROM items WHERE category_id = $1", category_id)
            return {row['name']: row['bought'] for row in rows}

    # Удалить товар
    async def delete_item(self, category_id, item_name):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM items WHERE category_id = $1 AND name = $2", category_id, item_name)

    # Удалить категорию и все её товары
    async def delete_category(self, list_id, category_name):
        async with self.pool.acquire() as conn:
            category_id = await conn.fetchval("""
                SELECT category_id FROM categories WHERE list_id = $1 AND name = $2
            """, list_id, category_name)

            if category_id:
                await conn.execute("DELETE FROM items WHERE category_id = $1", category_id)
                await conn.execute("DELETE FROM categories WHERE category_id = $1", category_id)

    # Удалить список целиком
    async def delete_list(self, user_id, list_name):
        async with self.pool.acquire() as conn:
            list_id = await conn.fetchval("""
                SELECT list_id FROM lists WHERE user_id = $1 AND name = $2
            """, user_id, list_name)

            if list_id:
                await conn.execute("DELETE FROM items WHERE category_id IN (SELECT category_id FROM categories WHERE list_id = $1)", list_id)
                await conn.execute("DELETE FROM categories WHERE list_id = $1", list_id)
                await conn.execute("DELETE FROM lists WHERE list_id = $1", list_id)

    # Загрузить все данные пользователя из БД
    async def load_user_data(self, user_id):
        result = {"lists": {}}
        async with self.pool.acquire() as conn:
            # Получаем все списки пользователя
            lists = await conn.fetch("SELECT list_id, name FROM lists WHERE user_id = $1", user_id)
            for lst in lists:
                list_id = lst["list_id"]
                list_name = lst["name"]
                result["lists"][list_name] = {"categories": {}}

                # Получаем категории
                categories = await conn.fetch("SELECT category_id, name FROM categories WHERE list_id = $1", list_id)
                for cat in categories:
                    category_id = cat["category_id"]
                    category_name = cat["name"]
                    result["lists"][list_name]["categories"][category_name] = []

                    # Получаем товары
                    items = await conn.fetch("SELECT name FROM items WHERE category_id = $1", category_id)
                    for item in items:
                        result["lists"][list_name]["categories"][category_name].append(item["name"])

        return result

    # Сохранить новый товар
    async def save_item(self, category_id, item_name):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO items (category_id, name)
                VALUES ($1, $2) ON CONFLICT (category_id, name) DO NOTHING
            """, category_id, item_name)