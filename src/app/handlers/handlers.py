from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import os
from dotenv import load_dotenv

import jwt
import datetime
import app.keyboards as kb
import app.states
from app import db
router = Router()
shopping_list = {}
shared_access = {}  #type: dict[int, list[int]]

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    await db.add_user(user_id, username)  # добавляем пользователя

    # загружаем структуру списков из БД
    shopping_list[user_id] = await db.load_user_data(user_id)

    await message.answer('Добро пожаловать!', reply_markup=kb.main)

@router.callback_query(F.data == 'create')
async def create(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.answer('Введите название списка')
    await state.set_state(app.states.shoppingListStates.list_name)

@router.message(app.states.shoppingListStates.list_name)
async def set_list_name(message: Message, state: FSMContext):
    list_name = message.text
    user_id = message.from_user.id
    if list_name not in shopping_list[user_id]['lists']:
        shopping_list[user_id]['lists'][list_name] = {'categories': {}}
        await db.add_list(user_id, list_name)
        await message.answer(f"Список '{list_name}' создан!")
        await message.answer("Что вы хотите сделать?", reply_markup=kb.main)
    else:
        await message.answer(f"Список '{list_name}' уже существует!")
        await message.answer("Что вы хотите сделать?", reply_markup=kb.main)
    await state.clear()

@router.callback_query(F.data == 'category_add')
async def category_add(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.answer('Введите название категории')
    await state.set_state(app.states.shoppingListStates.category_name)

@router.message(app.states.shoppingListStates.category_name)
async def set_list_name(message: Message, state: FSMContext):
    category_name = message.text
    user_id = message.from_user.id
    data = await state.get_data()
    list_name = data['selected_list']
    if category_name not in shopping_list[user_id]['lists'][list_name]['categories']:
        shopping_list[user_id]['lists'][list_name]['categories'][category_name] = []
        list_id = await db.get_list_id(user_id, list_name)
        await db.add_category(list_id, category_name)
        await message.answer(f"Категория '{category_name}' добавлена в список '{list_name}'")
        await message.answer(f'Выбранный список {list_name}!', reply_markup=kb.category)
    else:
        await message.answer(f"Категория '{category_name}' уже существует!")
        await message.answer("Что вы хотите сделать?", reply_markup=kb.main)

# Управление списками
@router.callback_query(F.data == 'manage')
async def manage(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите действие: ', reply_markup=kb.manage)

@router.callback_query(F.data == 'list_check')
async def check_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Получаем свои собственные списки
    own_data = shopping_list.get(user_id, {'lists': {}})
    own_lists = own_data['lists']
    # Готовим контейнер для расшаренных списков
    shared_lists = {}
    # Проходимся по всем пользователям
    for other_user_id, data in shopping_list.items():
        if other_user_id == user_id:
            continue  # пропускаем себя
        for list_name in data['lists']:
            list_id = await db.get_list_id(other_user_id, list_name)
            #4. Проверяем, есть ли доступ к этому списку
            if user_id in shared_access and list_id in shared_access[user_id]:
                shared_lists[f"{list_name} (от @{other_user_id})"] = data['lists'][list_name]
    # Объединяем собственные и расшаренные
    combined_lists = {**own_lists, **shared_lists}
    if not combined_lists:
        await callback.answer('У вас нет списков.')
        return
    #Передаём объединённый словарь в клавиатуру
    keyboard = kb.view_kb({'lists': combined_lists})
    await callback.message.edit_text('Выберите Список', reply_markup=await keyboard)

@router.callback_query(F.data == 'delete')
async def open_delete_menu(callback: CallbackQuery):
    await callback.message.edit_text("🗑 Выберите, что вы хотите удалить:", reply_markup=kb.delete)

@router.callback_query(F.data == "delete_list")
async def delete_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    list_name = data.get("selected_list")
    user_id = callback.from_user.id
    if list_name in shopping_list[user_id]["lists"]:
        del shopping_list[user_id]["lists"][list_name]
        await db.delete_list(user_id, list_name)
        await callback.message.edit_text(f"Список '{list_name}' удален.")
    else:
        await callback.answer("Список не найден.")
    await state.clear()
    await callback.message.answer('Что вы хотите сделать?', reply_markup=kb.main)

@router.callback_query(F.data == 'delete_category')
async def category_to_delete(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    user_data = shopping_list[user_id]['lists'][list_name]
    keyboard = kb.view_category_delete(user_data)
    await callback.message.edit_text('Выберите категорию:', reply_markup=await keyboard)

@router.callback_query(F.data.startswith('select_category_delete'))
async def delete_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get('selected_list')
    category_name = data.get('selected_category')
    if category_name in shopping_list[user_id]['lists'][list_name]['categories']:
        del shopping_list[user_id]['lists'][list_name]['categories'][category_name]
        list_id = await db.get_list_id(user_id, list_name)
        await db.delete_category(list_id, category_name)
        await callback.message.edit_text(f"Категория '{category_name}' удалена.")
    else:
        await callback.message.edit_text("Категория не найдена.")
    await select_list(callback, state)

@router.callback_query(F.data == 'back')
async def manage(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите действие: ', reply_markup=kb.main)

@router.callback_query(F.data == 'back_to_categories')
async def backToCategories(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите категорию:', reply_markup=kb.view_category())

@router.callback_query(F.data.startswith("select_list:"))
async def select_list(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    list_name = callback.data.split(':')[1]
    await state.update_data(selected_list=list_name)
    await callback.message.edit_text(f"Выбранный список: {list_name} !", reply_markup=kb.category)

@router.callback_query(F.data == 'back_list_check')
async def back_list_check(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = shopping_list.get(user_id, {'lists': {}})
    keyboard = kb.view_kb(user_data)
    await callback.message.edit_text('Выберите Список', reply_markup=await keyboard)
    await state.clear()

@router.callback_query(F.data == 'view_list')
async def view_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    list_name = data['selected_list']
    user_id = callback.from_user.id
    full_list = shopping_list[user_id]["lists"][list_name]["categories"]
    if not full_list:
        await callback.message.edit_text("Список пуст.")
        return
    response = f" Полный список '{list_name}':\n\n"
    for category, items in full_list.items():
        response += f" {category}:\n"
        if not items:
            response += "- (пусто)\n"
        else:
            for item in items:
                response += f"- {item}\n"
        response += "\n"
    await callback.message.edit_text(response, reply_markup=kb.backToLists)

@router.callback_query(F.data == 'product_add')
async def choose_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    user_data = shopping_list[user_id]['lists'][list_name]
    if not user_data['categories']:
        await callback.answer('В выбранном списке нет категорий')
        return
    keyboard = kb.view_category(user_data)
    await callback.message.edit_text('Выберите категорию: ', reply_markup=await keyboard)

@router.callback_query(F.data.startswith("select_category:"))
async def select_list(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    category_name = callback.data.split(':')[1]
    await state.update_data(selected_category=category_name)
    await state.update_data(selected_list=list_name)
    await callback.message.edit_text(
        f"Выбранная категория: {category_name}\n\nВведите название товара:",
        reply_markup=kb.backFromProduct
    )
    await state.set_state(app.states.shoppingListStates.item_name)

@router.message(app.states.shoppingListStates.item_name)
async def item_add(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    list_name = data['selected_list']
    category_name = data['selected_category']
    item_name = message.text
    shopping_list[user_id]['lists'][list_name]['categories'][category_name].append(item_name)
    list_id = await db.get_list_id(user_id, list_name)
    category_id = await db.get_category_id(list_id, category_name)
    await db.add_item(category_id, item_name)
    keyboard = kb.view_category(shopping_list[user_id]['lists'][list_name])
    await message.answer(f"Товар '{item_name}' добавлен в категорию '{category_name}'.")
    await message.answer('Выберите категорию: ', reply_markup=await keyboard)

@router.callback_query(F.data == 'back_from_product')
async def back_from_product(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    user_data = shopping_list[user_id]['lists'][list_name]
    keyboard = kb.view_category(user_data)
    await callback.message.edit_text('Выберите категорию', reply_markup=await keyboard)

@router.callback_query(F.data == 'back_to_category')
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    await state.update_data(selected_list=list_name)
    await callback.message.edit_text(f"Выбранный список: {list_name} !", reply_markup=kb.category)

@router.callback_query(F.data == "delete_item")
async def delete_item(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")
    user_data = shopping_list[user_id]['lists'][list_name]
    category_name = data.get("selected_category")
    if not list_name:
        await callback.answer("Сначала выберите список!")
        return
    # Если категория не выбрана — предложим выбрать её
    if not category_name:
        categories = shopping_list[user_id]['lists'][list_name]['categories']
        if not categories:
            await callback.message.answer("В этом списке нет категорий.")
            return
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        keyboard = kb.view_category_delete(user_data)
        await callback.message.answer("Выберите категорию для удаления товара:", reply_markup=await keyboard)
        return
    # Если категория уже выбрана — сразу показать товары
    items = shopping_list[user_id]['lists'][list_name]['categories'][category_name]
    if not items:
        await callback.answer("🛒 В этой категории нет товаров.")
        return
    keyboard = kb.view_items_delete(items)
    await callback.message.edit_text("🗑 Выберите товар для удаления:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("delete_item:"))
async def confirm_delete_item(callback: CallbackQuery, state: FSMContext):
    item_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    list_name = data["selected_list"]
    category_name = data["selected_category"]
    user_id = callback.from_user.id
    try:
        items = shopping_list[user_id]["lists"][list_name]["categories"][category_name]
        if item_name in items:
            items.remove(item_name)
            list_id = await db.get_list_id(user_id, list_name)
            category_id = await db.get_category_id(list_id, category_name)
            await db.delete_item(category_id, item_name)
            await callback.message.edit_text(f"Товар '{item_name}' удален.")
        else:
            await callback.message.edit_text("Товар не найден в категории.")
    except KeyError:
        await callback.message.edit_text("Ошибка: данные повреждены.")
    user_data = shopping_list[user_id]['lists'][list_name]
    await callback.message.answer("Что вы хотите сделать?", reply_markup=kb.category)

@router.callback_query(F.data.startswith("select_cat_delete"))
async def category_chosen_for_deletion(callback: CallbackQuery, state: FSMContext):
    category_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    data = await state.get_data()
    list_name = data.get("selected_list")

    await state.update_data(selected_category=category_name)

    items = shopping_list[user_id]['lists'][list_name]['categories'][category_name]
    if not items:
        await callback.message.answer("🛒 В этой категории нет товаров.")
        return

    keyboard = kb.view_items_delete(items)
    await callback.message.edit_text("🗑 Выберите товар для удаления:", reply_markup=keyboard)

@router.callback_query(F.data == "share_list")
async def share_list_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lists = shopping_list.get(user_id, {}).get("lists", {})

    if not user_lists:
        await callback.message.answer("У вас нет списков для передачи.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for list_name in user_lists:
        kb.button(text=list_name, callback_data=f"share_select:{list_name}")
    kb.button(text="Назад", callback_data="sync")

    await callback.message.edit_text("Выберите список для передачи:", reply_markup=kb.adjust(1).as_markup())
    await state.set_state(app.states.syncStates.select_list)

@router.callback_query(F.data == "enter_code")
async def enter_code(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код, который вам дали:")
    await state.set_state(app.states.syncStates.jwt_code)

@router.message(app.states.syncStates.jwt_code)
async def receive_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    token = message.text
    try:
        # Расшифровываем токен
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        sender_id = data["user_id"]
        list_name = data["list_name"]
        # Проверяем, есть ли у отправителя такой список
        sender_lists = shopping_list.get(sender_id, {}).get("lists", {})
        if list_name not in sender_lists:
            await message.answer("Список не найден у отправителя.")
            await state.clear()
            return
        # Загружаем данные отправителя, если их нет в памяти
        if sender_id not in shopping_list:
            shopping_list[sender_id] = await db.load_user_data(sender_id)
            sender_lists = shopping_list[sender_id]["lists"]
        # Добавляем ссылку на тот же самый объект
        shopping_list.setdefault(user_id, {"lists": {}})
        if list_name in shopping_list[user_id]["lists"]:
            await message.answer("Этот список уже подключён.")
        else:
            shopping_list[user_id]["lists"][list_name] = sender_lists[list_name]
            # Добавляем доступ в shared_access
            list_id = await db.get_list_id(sender_id, list_name)
            shared_access.setdefault(user_id, [])
            if list_id not in shared_access[user_id]:
                shared_access[user_id].append(list_id)

            await message.answer(f"Вы подключились к списку: '{list_name}'")

    except jwt.ExpiredSignatureError:
        await message.answer("Срок действия кода истёк.")
    except jwt.InvalidTokenError:
        await message.answer("Неверный код.")
    finally:
        await state.clear()

@router.callback_query(F.data == "received_lists")
async def view_received_lists(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lists = shopping_list.get(user_id, {}).get("lists", {})
    received = [name for name in user_lists if "(копия)" in name]

    if not received:
        await callback.message.answer("У вас пока нет полученных списков.")
    else:
        text = "Полученные списки:\n\n" + "\n".join(f"• {name}" for name in received)
        await callback.message.answer(text)

@router.callback_query(F.data == "sync")
async def sync_menu(callback: CallbackQuery):
    await callback.message.edit_text("🔄 Совместный доступ", reply_markup=kb.sync_menu)

@router.callback_query(F.data.startswith("share_select:"))
async def generate_share_token(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    list_name = callback.data.split(":", 1)[1]

    if list_name not in shopping_list.get(user_id, {}).get("lists", {}):
        await callback.message.answer("Такого списка нет.")
        return

    payload = {
        "user_id": user_id,
        "list_name": list_name,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    await callback.message.answer(
        f"Отправьте этот код другому пользователю:\n\n`{token}`", parse_mode="Markdown"
    )
    await state.clear()
