TOKEN = '8504544886:AAF6sLIQNakDcrWmKj2yu2UXI4e72nLyjCA'

import sqlite3
import asyncio
import logging
import re
import math
import time

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

last_callback_time = {}


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
        [InlineKeyboardButton(text="Построение графиков 1",
                              url='https://www.desmos.com/calculator/s60mqvyp85?lang=ru')],
        [InlineKeyboardButton(text="Построение графиков 2", url='https://www.mathway.com/ru/Graph')],
        [InlineKeyboardButton(text="Инженерный калькулятор 1", url='https://www.desmos.com/scientific?lang=ru')],
        [InlineKeyboardButton(text="Инженерный калькулятор 2",
                              url='https://calc.by/math-calculators/scientific-calculator.html')]
    ]
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
        [InlineKeyboardButton(text="Законы Ньютона", callback_data='fiz_entertainment')],
        [InlineKeyboardButton(text="Тепловые явления", callback_data='fiz_tepl')],
        [InlineKeyboardButton(text="Электродинамика", callback_data='fiz_eldin')],
        [InlineKeyboardButton(text="Колебания и волны", callback_data='fiz_coleb')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def mat_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Алгебра", callback_data='mat_algebra')],
        [InlineKeyboardButton(text="Геометрия", callback_data='mat_geometry')],
        [InlineKeyboardButton(text="Тригонометрия", callback_data='mat_trigonometry')],
        [InlineKeyboardButton(text="Функции", callback_data='mat_functions')],
        [InlineKeyboardButton(text="Матанализ", callback_data='mat_calculus')],
        [InlineKeyboardButton(text="Теория вероятностей", callback_data='mat_probability')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


# ===== УЛУЧШЕННЫЙ КАЛЬКУЛЯТОР =====
def safe_eval_restricted(expression: str):
    expression = expression.replace('pi', str(math.pi)).replace('e', str(math.e))

    allowed_functions = {
        # Основные функции
        'sqrt': math.sqrt,
        'abs': abs,

        # Тригонометрия (градусы)
        'sin': lambda x: math.sin(math.radians(x)),
        'cos': lambda x: math.cos(math.radians(x)),
        'tan': lambda x: math.tan(math.radians(x)),

        # Тригонометрия (радианы)
        'sinr': math.sin,
        'cosr': math.cos,
        'tanr': math.tan,

        # Логарифмы
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,

        # Степени
        'pow': math.pow,

        # Константы
        'pi': math.pi,
        'e': math.e,

        # Округление
        'ceil': math.ceil,
        'floor': math.floor,

        # Факториал
        'factorial': math.factorial,

        # Другие функции
        'degrees': math.degrees,
        'radians': math.radians,
    }

    allowed_chars_pattern = re.compile(r"^[0-9+\-*/().\s^,]+$")
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
        expression = expression.replace('^', '**')
        result = eval(
            expression,
            {"__builtins__": None},
            allowed_functions
        )

        if isinstance(result, (int, float)):
            if abs(result) > 1e12 or (abs(result) < 1e-12 and result != 0):
                return f"{result:.4e}"
            elif isinstance(result, float):
                rounded = round(result, 10)
                if rounded.is_integer():
                    return str(int(rounded))
                formatted = f"{rounded:.10f}".rstrip('0').rstrip('.')
                return formatted
        return str(result)

    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        return f"Ошибка: {e}"
    except Exception as e:
        return f"Ошибка: {e}"


def get_calculator_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Убраны кнопки asin, acos, atan, exp
    buttons = [
        ('(', '('), (')', ')'), ('√', 'sqrt('), ('C', 'C'), ('←', 'BACK'),
        ('7', '7'), ('8', '8'), ('9', '9'), ('/', '/'), ('^', '^'),
        ('4', '4'), ('5', '5'), ('6', '6'), ('*', '*'), ('π', 'pi'),
        ('1', '1'), ('2', '2'), ('3', '3'), ('-', '-'), ('e', 'e'),
        ('0', '0'), ('.', '.'), ('=', '='), ('+', '+'), ('!', 'factorial('),
        ('sin', 'sin('), ('cos', 'cos('), ('tan', 'tan('), ('log', 'log('), ('log10', 'log10('),
        ('abs', 'abs('),  # Оставлена только кнопка abs
    ]
    for text, callback_data in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    builder.adjust(5)
    return builder.as_markup()


@dp.message(Command('start'))
async def command_start(message: Message):
    await message.answer(
        'Привет! Выбери функцию с помощью которой я смогу помочь тебе, а иначе... ничего не сделаю :)',
        reply_markup=test_kb()
    )


@dp.message(
    (F.text == 'Зачем ты нужен?') |
    (F.text.lower().contains('зачем') & F.text.lower().contains('нужен'))
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
    await message.answer("Калькулятор\nВведите выражение с помощью кнопок:", reply_markup=get_calculator_keyboard())


@dp.callback_query(F.data == 'fiz')
async def callback_fiz(callback: CallbackQuery):
    await callback.answer('вы выбрали Физику')
    await callback.message.edit_text('Выберите тему', reply_markup=fiz_kb())


@dp.callback_query(F.data == 'fiz_food')
async def callback_fiz_food(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.answer('''
    МЕХАНИКА

КИНЕМАТИКА - описание движения без анализа причин.

    Перемещение (s, Δr) - вектор, соединяющий начальное и конечное положение.

    Скорость (v): v = Δr / Δt (средняя), v = dr / dt (мгновенная).

    Ускорение (a): a = Δv / Δt (среднее), a = dv / dt (мгновенное). Нормальное (a_n = v² / R) отвечает за поворот, тангенциальное (a_τ = dv / dt) - за изменение модуля скорости.

    Равномерное прямолинейное движение: s = s₀ + v·t.

    Равноускоренное прямолинейное движение: v = v₀ + a·t, s = s₀ + v₀·t + (a·t²)/2, v² - v₀² = 2a·s.

    Движение по окружности: период T, частота ν = 1/T, угловая скорость ω = 2π/T = φ/t, линейная скорость v = ωR, центростремительное ускорение a = v²/R = ω²R.

ДИНАМИКА - причины движения.

    1-й закон Ньютона (закон инерции): тело сохраняет состояние покоя или равномерного прямолинейного движения, если нет действия других тел.

    2-й закон Ньютона (основной): F = m·a. Ускорение пропорционально равнодействующей силе и обратно пропорционально массе.

    3-й закон Ньютона: F₁₂ = -F₂₁. Силы действия и противодействия равны по модулю и противоположны по направлению.

    Сила тяжести: F_тяж = m·g, где g ≈ 9.8 м/с².

    Сила упругости (закон Гука): F_упр = -k·Δx, где k - жёсткость.

    Сила трения скольжения: F_тр = μ·N, где μ - коэффициент трения, N - сила нормальной реакции опоры.

ЗАКОНЫ СОХРАНЕНИЯ

    Импульс тела: p = m·v. Закон сохранения импульса: в замкнутой системе Σp_i = const.

    Механическая работа: A = F·s·cosα, где α - угол между векторами силы и перемещения.

    Мощность: P = A / t = F·v.

    Кинетическая энергия: E_кин = (m·v²)/2.

    Потенциальная энергия:

        В гравитационном поле: E_пот = m·g·h.

        Упруго деформированного тела: E_пот = (k·Δx²)/2.

    Закон сохранения механической энергии: в замкнутой системе без сил трения E_кин + E_пот = const. При наличии трения: ΔE_мех = A_тр, где A_тр - работа силы трения.

СТАТИКА И ГИДРОСТАТИКА

    Условия равновесия тела: ΣF = 0 (первое условие), ΣM = 0 (второе условие), где M - момент силы.

    Давление: p = F / S.

    Давление столба жидкости: p = ρ·g·h, где ρ - плотность.

    Закон Архимеда: F_A = ρ_ж·g·V_погр - выталкивающая сила, равная весу вытесненной жидкости.

ОСНОВНЫЕ КОНСТАНТЫ И ЕДИНИЦЫ

    g ~ 9.8 м/с² (ускорение свободного падения).

    СИ: масса (m) - кг, путь (s) - м, время (t) - с, сила (F) - Н (Ньютон), энергия (E) - Дж (Джоуль).
''')


@dp.callback_query(F.data == 'fiz_entertainment')
async def callback_fiz_entertainment(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме')
    await callback.message.answer('''скоро
появится
''')


@dp.callback_query(F.data == 'fiz_tepl')
async def callback_fiz_tepl(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме "Тепловые явления"')
    await callback.message.answer('''
    ТЕПЛОВЫЕ ЯВЛЕНИЯ

Молекулярная физика

    Основное уравнение МКТ: p = (1/3)·n·m₀·v² = (2/3)·n·Eₖ, где n – концентрация молекул, m₀ – масса одной молекулы, v² – средний квадрат скорости, Eₖ – средняя кинетическая энергия поступательного движения.

    Абсолютная температура: T (кельвины). Связь с энергией: Eₖ = (3/2)·k·T, где k ≈ 1.38·10⁻²³ Дж/К – постоянная Больцмана.

    Уравнение состояния идеального газа: p·V = (m/M)·R·T, где R ≈ 8.31 Дж/(моль·К) – универсальная газовая постоянная, M – молярная масса.

    Изопроцессы идеального газа:

        Изотермический (T=const): p·V = const (закон Бойля–Мариотта).

        Изобарный (p=const): V/T = const (закон Гей-Люссака).

        Изохорный (V=const): p/T = const (закон Шарля).

Термодинамика

    Внутренняя энергия идеального одноатомного газа: U = (3/2)·(m/M)·R·T. Для двухатомного (при комнатной температуре) U = (5/2)·(m/M)·R·T.

    Первый закон термодинамики: Q = ΔU + A´, где Q – количество теплоты, подведённое к системе, ΔU – изменение её внутренней энергии, A´ – работа, совершённая газом против внешних сил.

    Работа газа при изобарном расширении: A´ = p·ΔV.

    Теплоёмкость: удельная (c = Q/(m·ΔT)), молярная (C = Q/(ν·ΔT)).

    Фазовые переходы: плавление/кристаллизация Q = ±λ·m, парообразование/конденсация Q = ±L·m, где λ – удельная теплота плавления, L – удельная теплота парообразования.

    КПД тепловой машины: η = A´/Q₁ = (Q₁ – Q₂)/Q₁, где Q₁ – теплота от нагревателя, Q₂ – теплота холодильнику. Максимальный КПД цикла Карно: ηₘₐₓ = (T₁ – T₂)/T₁.
    ''')


@dp.callback_query(F.data == 'fiz_eldin')
async def callback_fiz_eldin(callback: CallbackQuery):
    await callback.answer('Вот вся загруженная теория по теме "Электродинамика"')
    await callback.message.answer('''
    ЭЛЕКТРОДИНАМИКА

Электростатика

    Закон Кулона: F = k·(|q₁·q₂|)/(ε·r²), где k = 1/(4πε₀) ≈ 9·10⁹ Н·м²/Кл², ε – диэлектрическая проницаемость среды.

    Напряжённость электрического поля: E = F/q (вектор). Для точечного заряда: E = k·q/r².

    Потенциал электростатического поля: φ = Wₚ/q. Разность потенциалов (напряжение): U = A/q = φ₁ – φ₂.

    Связь между напряжённостью и напряжением в однородном поле: U = E·d.

    Электроёмкость уединённого проводника: C = q/φ. Ёмкость плоского конденсатора: C = ε·ε₀·S/d, где ε₀ ≈ 8.85·10⁻¹² Ф/м.

    Энергия заряженного конденсатора: W = (q·U)/2 = (C·U²)/2 = q²/(2C).

Постоянный электрический ток

    Сила тока: I = Δq/Δt. Плотность тока: j = I/S = n·e·u, где u – скорость направленного движения носителей.

    Закон Ома для участка цепи: I = U/R.

    Сопротивление однородного проводника: R = ρ·l/S, где ρ – удельное сопротивление.

    Закон Джоуля–Ленца: Q = I²·R·t = U²·t/R (выделение тепла в неподвижном проводнике).

    Электродвижущая сила (ЭДС) источника: ε = Aст/q. Закон Ома для полной цепи: I = ε/(R + r), где r – внутреннее сопротивление источника.

    Законы последовательного и параллельного соединений:

        Последовательное: I = const, U = ΣUᵢ, R = ΣRᵢ.

        Параллельное: U = const, I = ΣIᵢ, 1/R = Σ(1/Rᵢ).

Магнитное поле. Электромагнитная индукция

    Сила Ампера, действующая на проводник с током в магнитном поле: Fₐ = I·B·l·sinα, где α – угол между направлением тока и вектором магнитной индукции B.

    Сила Лоренца, действующая на движущийся заряд: Fₗ = q·B·v·sinα. Заряд, движущийся перпендикулярно линиям B, описывает окружность радиусом R = (m·v)/(|q|·B).

    Магнитный поток через контур: Φ = B·S·cosα.

    Закон электромагнитной индукции Фарадея: ЭДС индукции в контуре εᵢ = –ΔΦ/Δt.

    Индуктивность контурa (катушки): L = Φ/I. ЭДС самоиндукции: εₛᵢ = –L·(ΔI/Δt).

    Энергия магнитного поля катушки с током: W = (L·I²)/2.
''')


@dp.callback_query(F.data == 'fiz_coleb')
async def callback_fiz_coleb(callback: CallbackQuery):
    await callback.message.answer('''
КОЛЕБАНИЯ И ВОЛНЫ

Механические колебания

    Уравнение гармонических колебаний: x(t) = A·cos(ωt + φ₀), где A – амплитуда, ω – циклическая частота, φ₀ – начальная фаза.

    Связь периода и частоты: T = 1/ν = 2π/ω.

    Периоды свободных колебаний: пружинного маятника T = 2π·√(m/k), математического маятника T = 2π·√(l/g).

    Энергия гармонического осциллятора: кинетическая Eₖ = (m·v²)/2, потенциальная Eₚ = (k·x²)/2, полная E = Eₖ + Eₚ = (k·A²)/2 = (m·ω²·A²)/2.

    Резонанс – резкое возрастание амплитуды вынужденных колебаний при совпадении частоты вынуждающей силы с собственной частотой колебательной системы.

Волны (механические и электромагнитные)

    Связь длины волны λ, скорости v, периода T и частоты ν: λ = v·T = v/ν.

    Уравнение гармонической бегущей волны: s(x,t) = A·cos(ωt – kx), где k = 2π/λ – волновое число.

    Условия интерференционного максимума и минимума для двух когерентных источников:

        Максимум (усиление): Δd = |d₂ – d₁| = m·λ, m = 0, 1, 2...

        Минимум (ослабление): Δd = |d₂ – d₁| = (2m + 1)·λ/2.

    Скорость звука в воздухе при 20°C ≈ 343 м/с.

    Электромагнитные волны: скорость в вакууме c ≈ 3·10⁸ м/с. Связь между модулями векторов E и B в волне: E = c·B.    
''')


@dp.callback_query(F.data == 'mat')
async def callback_mat(callback: CallbackQuery):
    await callback.answer('вы выбрали математику')
    await callback.message.edit_text('Выберите тему', reply_markup=mat_kb())


@dp.callback_query(F.data == 'mat_algebra')
async def callback_mat_algebra(callback: CallbackQuery):
    await callback.answer('Алгебра')
    await callback.message.edit_text('''
АЛГЕБРА

Квадратные уравнения: ax² + bx + c = 0
Дискриминант: D = b² - 4ac
Корни: x₁,₂ = (-b ± √D) / (2a)
Теорема Виета: x₁ + x₂ = -b/a, x₁·x₂ = c/a

Степени и корни:
aᵐ·aⁿ = aᵐ⁺ⁿ, aᵐ/aⁿ = aᵐ⁻ⁿ, (aᵐ)ⁿ = aᵐⁿ
ⁿ√(a·b) = ⁿ√a·ⁿ√b, ⁿ√(a/b) = ⁿ√a/ⁿ√b
aᵐ/ⁿ = ⁿ√(aᵐ)

Логарифмы:
Определение: aˣ = b ⇔ x = logₐb
Свойства: logₐ(b·c) = logₐb + logₐc
          logₐ(b/c) = logₐb - logₐc
          logₐbᵐ = m·logₐb
Формула перехода: logₐb = logₑb / logₑa

Прогрессии:
Арифметическая: aₙ = a₁ + d(n-1), Sₙ = n(a₁ + aₙ)/2
Геометрическая: bₙ = b₁·qⁿ⁻¹, Sₙ = b₁(1 - qⁿ)/(1 - q)

Комбинаторика:
Перестановки: Pₙ = n!
Сочетания: Cₙᵏ = n!/(k!(n-k)!)
Размещения: Aₙᵏ = n!/(n-k)!
''')


@dp.callback_query(F.data == 'mat_geometry')
async def callback_mat_geometry(callback: CallbackQuery):
    await callback.answer('Геометрия')
    await callback.message.edit_text('''
ГЕОМЕТРИЯ

Планиметрия:
Треугольник: S = ½·a·h, теорема Пифагора: c² = a² + b²
Площади: квадрат - a², прямоугольник - a·b, круг - πr²
Теорема косинусов: c² = a² + b² - 2ab·cosγ
Теорема синусов: a/sinα = b/sinβ = c/sinγ = 2R

Стереометрия:
Объёмы: куб - a³, параллелепипед - a·b·c, шар - (4/3)πr³
Призма: V = Sосн·h
Пирамида: V = (1/3)·Sосн·h
Цилиндр: V = πr²h, Sбок = 2πrh
Конус: V = (1/3)πr²h, Sбок = πrl

Векторы:
Скалярное произведение: a·b = |a|·|b|·cosφ = x₁x₂ + y₁y₂ + z₁z₂
Векторное произведение: |a×b| = |a|·|b|·sinφ
Длина вектора: |a| = √(x² + y² + z²)
''')


@dp.callback_query(F.data == 'mat_trigonometry')
async def callback_mat_trigonometry(callback: CallbackQuery):
    await callback.answer('Тригонометрия')
    await callback.message.edit_text('''
ТРИГОНОМЕТРИЯ

Основные тождества:
sin²α + cos²α = 1
1 + tg²α = 1/cos²α
1 + ctg²α = 1/sin²α

Формулы сложения:
sin(α±β) = sinα·cosβ ± cosα·sinβ
cos(α±β) = cosα·cosβ ∓ sinα·sinβ
tg(α±β) = (tgα ± tgβ)/(1 ∓ tgα·tgβ)

Формулы двойного угла:
sin2α = 2sinα·cosα
cos2α = cos²α - sin²α = 2cos²α - 1 = 1 - 2sin²α
tg2α = 2tgα/(1 - tg²α)

Формулы половинного угла:
sin(α/2) = ±√((1 - cosα)/2)
cos(α/2) = ±√((1 + cosα)/2)
tg(α/2) = sinα/(1 + cosα) = (1 - cosα)/sinα

Преобразование суммы в произведение:
sinα + sinβ = 2sin((α+β)/2)·cos((α-β)/2)
sinα - sinβ = 2cos((α+β)/2)·sin((α-β)/2)
cosα + cosβ = 2cos((α+β)/2)·cos((α-β)/2)
cosα - cosβ = -2sin((α+β)/2)·sin((α-β)/2)

Обратные тригонометрические функции:
arcsin x ∈ [-π/2, π/2]
arccos x ∈ [0, π]
arctg x ∈ (-π/2, π/2)
''')


@dp.callback_query(F.data == 'mat_functions')
async def callback_mat_functions(callback: CallbackQuery):
    await callback.answer('Функции')
    await callback.message.edit_text('''
ФУНКЦИИ И ИХ СВОЙСТВА

Основные функции:
Линейная: y = kx + b, график - прямая
Квадратичная: y = ax² + bx + c, график - парабола
Степенная: y = xⁿ
Показательная: y = aˣ (a > 0, a ≠ 1)
Логарифмическая: y = logₐx
Тригонометрические: y = sin x, cos x, tg x, ctg x

Свойства функций:
Область определения
Область значений
Чётность/нечётность
Периодичность
Монотонность (возрастание/убывание)
Экстремумы (максимумы/минимумы)
Асимптоты

Преобразования графиков:
y = f(x + a) - сдвиг вдоль OX
y = f(x) + b - сдвиг вдоль OY
y = k·f(x) - растяжение вдоль OY
y = f(kx) - сжатие вдоль OX
y = -f(x) - симметрия относительно OX
y = f(-x) - симметрия относительно OY
''')


@dp.callback_query(F.data == 'mat_calculus')
async def callback_mat_calculus(callback: CallbackQuery):
    await callback.answer('Математический анализ')
    await callback.message.edit_text('''
МАТЕМАТИЧЕСКИЙ АНАЛИЗ

Производные:
(xⁿ)′ = n·xⁿ⁻¹
(eˣ)′ = eˣ
(aˣ)′ = aˣ·ln a
(ln x)′ = 1/x
(logₐ x)′ = 1/(x·ln a)
(sin x)′ = cos x
(cos x)′ = -sin x
(tg x)′ = 1/cos²x
(ctg x)′ = -1/sin²x

Интегралы:
∫xⁿ dx = xⁿ⁺¹/(n+1) + C (n ≠ -1)
∫1/x dx = ln|x| + C
∫eˣ dx = eˣ + C
∫aˣ dx = aˣ/ln a + C
∫sin x dx = -cos x + C
∫cos x dx = sin x + C
∫dx/cos²x = tg x + C
∫dx/sin²x = -ctg x + C

Основные теоремы:
Теорема Лагранжа: f(b)-f(a) = f′(c)(b-a)
Теорема Коши: (f(b)-f(a))/(g(b)-g(a)) = f′(c)/g′(c)
Правило Лопиталя: lim f(x)/g(x) = lim f′(x)/g′(x)
''')


@dp.callback_query(F.data == 'mat_probability')
async def callback_mat_probability(callback: CallbackQuery):
    await callback.answer('Теория вероятностей')
    await callback.message.edit_text('''
ТЕОРИЯ ВЕРОЯТНОСТЕЙ

Основные понятия:
Вероятность: P(A) = m/n
Условная вероятность: P(A|B) = P(A∩B)/P(B)
Формула полной вероятности: P(A) = ΣP(Hᵢ)·P(A|Hᵢ)
Формула Байеса: P(Hᵢ|A) = P(Hᵢ)·P(A|Hᵢ)/P(A)

Распределения:
Биномиальное: Pₙ(k) = Cₙᵏ·pᵏ·(1-p)ⁿ⁻ᵏ
Пуассона: P(k) = (λᵏ/k!)·e⁻λ
Нормальное: f(x) = (1/(σ√(2π)))·exp(-(x-μ)²/(2σ²))

Числовые характеристики:
Математическое ожидание: M[X] = Σxᵢ·pᵢ
Дисперсия: D[X] = M[X²] - (M[X])²
Среднее квадратичное отклонение: σ = √D[X]

Статистика:
Выборочное среднее: x̄ = (1/n)Σxᵢ
Выборочная дисперсия: s² = (1/(n-1))Σ(xᵢ - x̄)²
Ковариация: cov(X,Y) = M[XY] - M[X]·M[Y]
Коэффициент корреляции: ρ = cov(X,Y)/(σₓ·σᵧ)
''')


@dp.callback_query()
async def callback_calculator(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_time = time.time()

    if user_id in last_callback_time:
        time_diff = current_time - last_callback_time[user_id]
        if time_diff < 0.5:
            await callback_query.answer("Подождите немного перед следующим нажатием")
            return

    last_callback_time[user_id] = current_time

    action = callback_query.data
    current_text = callback_query.message.text

    if 'Калькулятор' in current_text:
        lines = current_text.split('\n')
        if len(lines) > 1:
            current_expression = lines[-1] if not lines[-1].startswith('Введите') else ""
        else:
            current_expression = ""
    else:
        current_expression = current_text.strip()

    if '=' in current_expression or current_expression.startswith("Ошибка"):
        current_expression = ""

    new_expression = current_expression

    if action == 'C':
        new_expression = ""
    elif action == 'BACK':
        new_expression = current_expression[:-1] if current_expression else ""
    elif action == '=':
        if current_expression:
            result = safe_eval_restricted(current_expression)
            new_expression = f"{current_expression} = <b>{result}</b>"
        else:
            new_expression = "Введите выражение"
    else:
        new_expression += action

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
        if "message is not modified" not in str(e).lower():
            logging.error(f"Ошибка при редактировании сообщения: {e}")

    await callback_query.answer()


@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(
        f" Ваши ID:\n\n"
        f" Ваш User ID: `{message.from_user.id}`\n"
        f" ID этого чата: `{message.chat.id}`\n\n"
        f" Используйте User ID для добавления в админы.",
        parse_mode='Markdown'
    )


async def main():
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

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())