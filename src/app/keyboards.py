from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def view_kb(user_data):
    view = InlineKeyboardBuilder()
    for list_name in user_data.get('lists', {}):
        view.button(text= list_name, callback_data= f"select_list:{list_name}")
    view.button(text='Назад', callback_data='manage')
    return view.adjust(1).as_markup()

async def view_category(user_data):
    cat = InlineKeyboardBuilder()
    for category_name in user_data.get('categories', {}):
        cat.button(text= category_name, callback_data=f"select_category:{category_name}")
    cat.button(text='Назад', callback_data='list_check')
    return cat.adjust(1).as_markup()

async def view_category_delete(user_data):
    cat = InlineKeyboardBuilder()
    for category_name in user_data.get('categories', {}):
        cat.button(text= category_name, callback_data=f"select_cat_delete:{category_name}")
    cat.button(text='Назад', callback_data='list_check')
    return cat.adjust(1).as_markup()

def view_items_delete(items, prefix="delete_item:"):
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=item, callback_data=f"{prefix}{item}")
    builder.button(text="Назад", callback_data="back_to_category")
    builder.adjust(1)
    return builder.as_markup()

back_category_choose = InlineKeyboardMarkup( inline_keyboard=[
  [InlineKeyboardButton(text='Назад', callback_data= 'back_to_categories')]
])

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Создать список', callback_data= 'create'),
     InlineKeyboardButton(text='Управление списками', callback_data= 'manage')
    ],
    [InlineKeyboardButton(text='Совместный доступ', callback_data='sync')]
])

sync_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Поделиться списком", callback_data="share_list")],
    [InlineKeyboardButton(text="Ввести код", callback_data="enter_code")],
    [InlineKeyboardButton(text="Полученные списки", callback_data="received_lists")],
    [InlineKeyboardButton(text="Назад", callback_data="back")]
])

manage = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text= 'Выбрать список', callback_data='list_check'),
     ],
    [InlineKeyboardButton(text='Назад', callback_data='back')]
])

lists = InlineKeyboardMarkup(inline_keyboard=[                              #Клавиатура для перечня списков
])

category = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить категорию', callback_data= 'category_add')],
    [InlineKeyboardButton(text='Добавить товар', callback_data= 'product_add')],
    [InlineKeyboardButton(text='Посмотреть список', callback_data= 'view_list')],
    [InlineKeyboardButton(text='Удаление', callback_data= 'delete')],
    [InlineKeyboardButton(text='Назад', callback_data= 'back_list_check')],

])

delete = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Удалить список', callback_data='delete_list')],
    [InlineKeyboardButton(text='Удалить категорию', callback_data='delete_category')],
    [InlineKeyboardButton(text='Удалить товар', callback_data='delete_item')],
    [InlineKeyboardButton(text='Назад', callback_data= 'back_to_category')]
])


backToLists = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_list_check')]
])

backFromProduct= InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_from_product')]
])