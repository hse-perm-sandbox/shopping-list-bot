from aiogram.fsm.state import State, StatesGroup

class shoppingListStates(StatesGroup):
    list_name = State()
    category_name = State()
    item_name = State()
    category_select = State()

class syncStates(StatesGroup):
    jwt_code = State()
    select_list = State()