TOKEN = '8504544886:AAF6sLIQNakDcrWmKj2yu2UXI4e72nLyjCA'

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


logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
bot = Bot(TOKEN)


# ===== КЛАВИАТУРЫ =====
def test_kb():
    kb_list = [
        [KeyboardButton(text="зачем ты нужен?"), KeyboardButton(text="Заполнить анкету")],
        [KeyboardButton(text="/calc"), KeyboardButton(text="ссылки")],
        [KeyboardButton(text="Теория"), KeyboardButton(text="добавление теории")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard


def link_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="график функции", url='https://www.desmos.com/calculator/s60mqvyp85?lang=ru'),
         InlineKeyboardButton(text="Калькулятор", url='https://www.desmos.com/scientific?lang=ru')]]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def city():
    inline_kb_list = [
        [InlineKeyboardButton(text="Физика", callback_data='fiz')],
        [InlineKeyboardButton(text="Математика", callback_data='mat')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def fiz_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Механика", callback_data='fiz_food')],
        [InlineKeyboardButton(text="Законы Ньютона", callback_data='fiz_entertainment')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def mat_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Функции", callback_data='mat_food')],
        [InlineKeyboardButton(text="Теоремы", callback_data='mat_entertainment')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


# ===== КАЛЬКУЛЯТОР =====
def safe_eval_restricted(expression: str):
    expression = expression.replace('pi', str(math.pi))
    allowed_functions = {
        'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'log': math.log, 'pow': math.pow, 'pi': math.pi
    }
    allowed_chars_pattern = re.compile(r"^[0-9+\-*/().\s]+$")
    cleaned_expr = expression
    for func in allowed_functions:
        cleaned_expr = cleaned_expr.replace(func, '')
    if not allowed_chars_pattern.match(cleaned_expr):
        return "Ошибка: Недопустимые символы"
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
    builder.adjust(4)
    return builder.as_markup()


# ===== ОБРАБОТЧИКИ СООБЩЕНИЙ =====
@dp.message(Command('start'))
async def command_start(message: Message):
    await message.answer(
        'Привет! Выбери функцию с помощью которой я смогу помочь тебе, а иначе... ничего не сделаю :)',
        reply_markup=test_kb()
    )


@dp.message(
    (F.text == 'Зачем ты нужен?') |  # Для кнопки
    (F.text.lower().contains('зачем') & F.text.lower().contains('нужен'))  # Для ручного ввода
)
async def get_inline_btn_link(message: Message):
    text = """Я — твой личный помощник по физике и математике!

Могу:
• Объяснить построение графиков
• Посчитать на инженерном калькуляторе  
• Подобрать формулы по физике
• Подготовить к контрольной

Просто напиши, что тебя интересует, или выбери одну из опций ниже!"""
    await message.answer(text)


@dp.message(F.text == 'добавление теории')
async def add_theory(message: Message):
    await message.answer(
        'Эта функция в разработке, но скоро появится!',
    )



class Register(StatesGroup):
    name = State()
    age = State()
    number = State()
    regon = State()


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
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await state.set_state(Register.regon)
    await message.answer('Введите ваш регион')


@dp.message(Register.regon)
async def register_regon(message: Message, state: FSMContext):
    await state.update_data(regon=message.text)
    data = await state.get_data()
    await message.answer(
        f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}\nРегион: {data["regon"]}')
    await message.answer('Данные приняты, можете воспользоваться другими функциями', reply_markup=test_kb())
    await state.clear()


@dp.message(F.text == 'ссылки')
async def get_inline_btn_link(message: Message):
    await message.answer('Это важные ссылки', reply_markup=link_kb())


@dp.message(F.text == 'Теория')
async def trip(message: Message):
    await message.answer('Выберите теорию:', reply_markup=city())


@dp.message(F.text == '/calc')
async def send_calculator(message: types.Message):
    # Исправлено: отправляем не пробел, а начальное сообщение
    await message.answer("Калькулятор\nВведите выражение с помощью кнопок:", reply_markup=get_calculator_keyboard())


# ===== ОБРАБОТЧИКИ CALLBACK =====
@dp.callback_query(F.data == 'fiz')
async def callback_fiz(callback: CallbackQuery):
    await callback.answer('вы выбрали Физику')
    await callback.message.edit_text('Выберите тему', reply_markup=fiz_kb())


@dp.callback_query(F.data == 'fiz_food')
async def callback_fiz_food(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.edit_text('''Eкин=(mv^2)/2
Eпот=mgh
''')


@dp.callback_query(F.data == 'fiz_entertainment')
async def callback_fiz_entertainment(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.edit_text('''скоро
появится
''')


@dp.callback_query(F.data == 'mat')
async def callback_mat(callback: CallbackQuery):
    await callback.answer('вы выбрали математику')
    await callback.message.edit_text('Выберите тему', reply_markup=mat_kb())


@dp.callback_query(F.data == 'mat_food')
async def callback_mat_food(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.edit_text('''x=y прямая
y=x^2 парабола
''')


@dp.callback_query(F.data == 'mat_entertainment')
async def callback_mat_entertainment(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.edit_text('''Пифагоровы штаны
во все стороны равны
''')


@dp.callback_query()
async def callback_calculator(callback_query: types.CallbackQuery):
    action = callback_query.data
    current_text = callback_query.message.text

    # Извлекаем текущее выражение из текста сообщения
    if 'Калькулятор' in current_text:
        # Если это начальное сообщение калькулятора
        lines = current_text.split('\n')
        if len(lines) > 1 and '=' not in current_text:
            current_expression = lines[-1] if not lines[-1].startswith('Введите') else ""
        else:
            current_expression = ""
    else:
        current_expression = current_text.strip()

    # Очищаем если видим результат или ошибку
    if '=' in current_expression or current_expression.startswith("Ошибка"):
        current_expression = ""

    new_expression = current_expression

    if action == 'C':
        new_expression = ""
    elif action == '=':
        if current_expression:
            result = safe_eval_restricted(current_expression)
            new_expression = f"{current_expression} = <b>{result}</b>"
        else:
            new_expression = "Введите выражение"
    else:
        new_expression += action

    # Формируем полный текст сообщения
    full_text = f"Калькулятор\n{new_expression if new_expression else 'Введите выражение:'}"

    try:
        await bot.edit_message_text(
            text=full_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=get_calculator_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при редактировании сообщения: {e}")

    await callback_query.answer()





# Команда для получения ID
@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(
        f"📋 Ваши ID:\n\n"
        f"👤 Ваш User ID: `{message.from_user.id}`\n"
        f"💬 ID этого чата: `{message.chat.id}`\n\n"
        f"📍 Используйте User ID для добавления в админы.",
        parse_mode='Markdown'
    )



# ===== ОСНОВНАЯ ФУНКЦИЯ =====
async def main():
    # Инициализация базы данных
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
    conn.close()

    print("База данных инициализирована")

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())