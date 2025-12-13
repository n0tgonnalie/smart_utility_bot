TOKEN='8504544886:AAF6sLIQNakDcrWmKj2yu2UXI4e72nLyjCA'

import aiogram
import sqlite3
import asyncio
import logging
import re
import math

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.types import CallbackQuery



from aiogram import types
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

dp = Dispatcher() #создаём диспетчера, он отвечает за обработку команд
bot = Bot(TOKEN) #создаем самого бота

async def main():
    def test_kb():
        kb_list = [
            [KeyboardButton(text="/info"), KeyboardButton(text="Заполнить анкету")],
            [KeyboardButton(text="зачем?"), KeyboardButton(text="ссылки")],
            [KeyboardButton(text="Выбрать теорию"), KeyboardButton(text="добавление теории")],
            [KeyboardButton(text="/calc")]
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
        return keyboard

    @dp.message(Command('start'))
    async def command_start(message):
        await message.answer('Hello, выбери функцию с помощью которой я смогу помочь тебе, а инече... ничего не сделаю',
                             reply_markup=test_kb())

    @dp.message(Command('info'))
    async def command_info(message):
        await message.answer(
            'Я являюсь ботом для помощи в расчётах, учёбе, работе и повседневной жизни. В скорем времени мой функционал будет пополнятся!')

    @dp.message(F.text == 'зачем?')
    async def get_inline_btn_link(message: Message):
        await message.answer('ну затем, сам поймёшь')
        await message.answer('или загугли, не маленький')

    class Register(StatesGroup):
        name = State()  # имя
        age = State()  # возрас
        number = State()  # номер телефона
        regon = State()  # регион

    @dp.message(F.text == 'Заполнить анкету')
    async def register(message: Message, state: FSMContext):
        await state.set_state(Register.name)
        await message.answer('Введите ваше имя')

    @dp.message(Register.name)
    async def register_name(message: Message, state: FSMContext):
        await state.update_data(name=message.text)
        await state.set_state(Register.age)
        await message.answer('Введите ваш возраст')

    @dp.message(Register.age)
    async def register_age(message: Message, state: FSMContext):
        await state.update_data(age=message.text)
        await state.set_state(Register.number)
        await message.answer('Отправьте ваш номер телефона')

    @dp.message(Register.number)
    async def register_age(message: Message, state: FSMContext):
        await state.update_data(number=message.text)
        await state.set_state(Register.regon)
        await message.answer('Введите ваш регион')

    @dp.message(Register.regon)
    async def register_number(message: Message, state: FSMContext):
        await state.update_data(regon=message.text)
        data = await state.get_data()
        await message.answer(
            f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}\nРегион: {data["regon"]}')
        await message.answer('Данные приняты, можете воспользоваться другими функциями', reply_markup=test_kb())
        await state.clear()

    def link_kb():
        inline_kb_list = [
            [InlineKeyboardButton(text="график функции", url='https://www.desmos.com/calculator/s60mqvyp85?lang=ru'),
             InlineKeyboardButton(text="Калькулятор", url='https://www.desmos.com/scientific?lang=ru')]]

        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    @dp.message(F.text == 'ссылки')
    async def get_inline_btn_link(message: Message):
        await message.answer('Это важные ссылки', reply_markup=link_kb())

    def city():
        inline_kb_list = [
            [InlineKeyboardButton(text="Физика", callback_data='fiz')],
            [InlineKeyboardButton(text="Математика", callback_data='mat')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    @dp.message(F.text == 'Выбрать теорию')
    async def trip(message: Message):
        await message.answer('Выберите теорию:', reply_markup=city())

    def fiz_kb():
        inline_kb_list = [
            [InlineKeyboardButton(text="Механика", callback_data='fiz_food')],
            [InlineKeyboardButton(text="Законы Ньютона", callback_data='fiz_entertainment')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    @dp.callback_query(F.data == 'fiz')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('вы выбрали Физику')
        # await callback.answer('вы выбрали Москву', show_alert=True)
        await callback.message.edit_text('Выберите тему', reply_markup=fiz_kb())

    @dp.callback_query(F.data == 'fiz_food')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('Вот вся загруженная теория по теме')
        # await callback.answer('вы выбрали Москву', show_alert=True)
        await callback.message.edit_text('''Eкин=(mv^2)/2
        Eпот=mgh
        ''')

    @dp.callback_query(F.data == 'fiz_entertainment')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('Вот вся загруженная теория по теме')
        # await callback.answer('вы выбрали Москву', show_alert=True)
        await callback.message.edit_text('''скоро
        появится
        ''')

    @dp.callback_query(F.data == 'mat')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('вы выбрали математику')
        await callback.message.edit_text('Выберите тему', reply_markup=mat_kb())

    def mat_kb():
        inline_kb_list = [
            [InlineKeyboardButton(text="Функции", callback_data='mat_food')],
            [InlineKeyboardButton(text="Теоремы", callback_data='mat_entertainment')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

    @dp.callback_query(F.data == 'mat_food')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('Вот вся загруженная теория по теме')
        await callback.message.edit_text('''x=y прямая
        y=x^2 парабола
        ''')

    @dp.callback_query(F.data == 'mat_entertainment')
    async def callback_msk(callback: CallbackQuery):
        await callback.answer('Вот вся загруженная теория по теме')
        await callback.message.edit_text('''Пифагоровы штаны
        во все стороны равны
        ''')

    logging.basicConfig(level=logging.INFO)

    def safe_eval_restricted(expression: str):
        expression = expression.replace('pi', str(math.pi))
        allowed_functions = {
            'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'pow': math.pow, 'pi': math.pi
        }
        # Разрешённые символы: цифры, знаки, точки, пробелы, скобки
        allowed_chars_pattern = re.compile(r"^[0-9+\-*/().\s]+$")
        # Проверим наличие запрещённых символов
        cleaned_expr = expression
        # Уберём известные функции из проверки символов (т.к. в expression могут быть имена функций)
        for func in allowed_functions:
            cleaned_expr = cleaned_expr.replace(func, '')
        if not allowed_chars_pattern.match(cleaned_expr):
            return "Ошибка: Недопустимые символы"
        # Проверка на наличие неразрешённых имён
        if re.search(r"[a-zA-Z_]\w*", expression):
            for part in re.findall(r"[a-zA-Z_]\w*", expression):
                if part not in allowed_functions:
                    return "Ошибка: Недопустимое имя функции или переменной"
        try:
            result = eval(
                expression,
                {"__builtins__": None},
                allowed_functions
            )
            return str(result)
        except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
            return f"Ошибка: {e}"
        except Exception as e:
            return f"Неизвестная ошибка: {e}"

    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)

    def get_calculator_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        buttons = [
            ('(', '('), (')', ')'), ('sqrt', 'sqrt('), ('C', 'C'),
            ('7', '7'), ('8', '8'), ('9', '9'), ('/', '/'),
            ('4', '4'), ('5', '5'), ('6', '6'), ('*', '*'),
            ('1', '1'), ('2', '2'), ('3', '3'), ('-', '-'),
            ('0', '0'), ('.', '.'), ('=', '='), ('+', '+'),
            ('sin', 'sin('), ('cos', 'cos('), ('tan', 'tan('), ('pi', 'pi')
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(4)  # Клавиатура 4 столбца
        return builder.as_markup()

    @dp.message(F.text == '/calc')
    async def send_calculator(message: types.Message):
        # При /calc отправляем новое сообщение с пустым выражением (пробелом)
        await message.answer(" ", reply_markup=get_calculator_keyboard())

    @dp.callback_query()
    async def callback_calculator(callback_query: types.CallbackQuery):
        action = callback_query.data
        current_expression = callback_query.message.text.strip()

        # Если видим результат или ошибку — чистим строку для нового ввода
        if '=' in current_expression or current_expression.startswith("Ошибка") or current_expression == "":
            current_expression = ""

        new_expression = current_expression

        if action == 'C':
            new_expression = ""
        elif action == '=':
            result = safe_eval_restricted(current_expression)
            new_expression = f"{current_expression} = <b>{result}</b>"
        else:
            new_expression += action

        if not new_expression:
            new_expression = " "

        try:
            await bot.edit_message_text(
                text=new_expression,
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=get_calculator_keyboard()
            )
        except Exception:
            pass

        await callback_query.answer()

    async def main():
        await dp.start_polling(bot)

    if __name__ == "__main__":
        try:
            loop = asyncio.get_running_loop()
            if loop and loop.is_running():
                loop.create_task(main())
            else:
                asyncio.run(main())
        except RuntimeError:
            asyncio.run(main())

    # sql фрагмент

    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER
        )
    ''')

    cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", 30))
    cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Bob", 25))

    conn.commit()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())