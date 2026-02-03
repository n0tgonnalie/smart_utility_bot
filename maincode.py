TOKEN = ''

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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    return ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)

def link_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Построение графиков 1", url='https://www.desmos.com/calculator/s60mqvyp85?lang=ru')],
        [InlineKeyboardButton(text="Построение графиков 2", url='https://www.mathway.com/ru/Graph')],
        [InlineKeyboardButton(text="Инженерный калькулятор 1", url='https://www.desmos.com/scientific?lang=ru')],
        [InlineKeyboardButton(text="Инженерный калькулятор 2", url='https://calc.by/math-calculators/scientific-calculator.html')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

def theory():
    inline_kb_list = [
        [InlineKeyboardButton(text="Физика", callback_data='fiz')],
        [InlineKeyboardButton(text="Математика", callback_data='mat')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

def fiz_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Механика", callback_data='fiz_food')],
        [InlineKeyboardButton(text="Законы Ньютона", callback_data='fiz_newton')],
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

# ===== КАЛЬКУЛЯТОР =====
def safe_eval_restricted(expression: str):
    expression = expression.replace('pi', str(math.pi)).replace('e', str(math.e))
    allowed_functions = {
        'sqrt': math.sqrt,
        'abs': abs,
        'sin': lambda x: math.sin(math.radians(x)),
        'cos': lambda x: math.cos(math.radians(x)),
        'tan': lambda x: math.tan(math.radians(x)),
        'sinr': math.sin,
        'cosr': math.cos,
        'tanr': math.tan,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'pow': math.pow,
        'pi': math.pi,
        'e': math.e,
        'ceil': math.ceil,
        'floor': math.floor,
        'factorial': math.factorial,
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
        result = eval(expression, {"__builtins__": None}, allowed_functions)
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
    buttons = [
        ('(', '('), (')', ')'), ('√', 'sqrt('), ('C', 'C'), ('←', 'BACK'),
        ('7', '7'), ('8', '8'), ('9', '9'), ('/', '/'), ('^', '^'),
        ('4', '4'), ('5', '5'), ('6', '6'), ('*', '*'), ('π', 'pi'),
        ('1', '1'), ('2', '2'), ('3', '3'), ('-', '-'), ('e', 'e'),
        ('0', '0'), ('.', '.'), ('=', '='), ('+', '+'), ('!', 'factorial('),
        ('sin', 'sin('), ('cos', 'cos('), ('tan', 'tan('), ('log', 'log('), ('log10', 'log10('),
        ('abs', 'abs('),
    ]
    for text, callback_data in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    builder.adjust(5)
    return builder.as_markup()

@dp.message(Command('start'))
async def command_start(message: Message):
    await message.answer(
        '''Привет! 👋 Я — Smart Utility, ваш умный помощник по физике и математике!


Вот что я умею:

/start — начать работу и открыть главное меню
/calc — открыть инженерный калькулятор с тригонометрией, логарифмами и константами
/myid — узнай больше про нашу переписку

Выбери кнопку на клавиатуре:
Теория — выбрать тему по физике или математике с разбивкой по классам (7–11)
Ссылки — получить подборку полезных онлайн-инструментов (графики, калькуляторы)
Заполнить анкету — помочь мне стать лучше: оставить отзыв и предложить новые функции

Просто нажми на любую кнопку — и я сразу приду на помощь! 💡''',
        reply_markup=test_kb()
    )

@dp.message(
    (F.text == 'Зачем ты нужен?') |
    (F.text.lower().contains('зачем') & F.text.lower().contains('нужен'))
)
async def get_inline_btn_link(message: Message):
    text = """Я создан, чтобы помогать школьникам и студентам быстро находить нужные формулы, считать сложные выражения и повторять теорию — всё это прямо в Telegram, без переключения между сайтами!"""
    await message.answer(text)

@dp.message(F.text == 'добавление теории')
async def add_theory(message: Message):
    await message.answer('Эта функция в разработке, но скоро появится!')

class Register(StatesGroup):
    name = State()
    where = State()
    feedback = State()
    additional = State()

@dp.message(F.text == 'Заполнить анкету')
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Как мне к вам обращаться? Введите ваш никнейм:')

@dp.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    nickname = message.text
    await state.set_state(Register.where)
    await message.answer(f'{nickname}, откуда вы узнали про меня?')

@dp.message(Register.where)
async def register_where(message: Message, state: FSMContext):
    await state.update_data(where=message.text)
    await state.set_state(Register.feedback)
    await message.answer('Что вы думаете обо мне? Напишите краткий отзыв, чтобы я стал круче!')

@dp.message(Register.feedback)
async def register_feedback(message: Message, state: FSMContext):
    await state.update_data(feedback=message.text)
    await state.set_state(Register.additional)
    await message.answer('Что бы вы ещё хотели добавить в этот бот?')

@dp.message(Register.additional)
async def register_additional(message: Message, state: FSMContext):
    await state.update_data(additional=message.text)
    data = await state.get_data()
    nickname = data.get('name', 'Друг')
    await message.answer(
        f'Ваш никнейм: {data["name"]}\n'
        f'Откуда вы узнали обо мне: {data["where"]}\n'
        f'Отзыв: {data["feedback"]}\n'
        f'Что добавить: {data["additional"]}'
    )
    await message.answer(f'{nickname}, всё записал, теперь можете воспользоваться другими функциями.\n'
    'Спасибо, что помогаете меня улучшать!', reply_markup=test_kb())
    await state.clear()

@dp.message(F.text == 'ссылки')
async def get_inline_btn_link(message: Message):
    await message.answer('Ссылки на инж. калькуляторы и построение графиков', reply_markup=link_kb())

@dp.message(F.text == 'Теория')
async def trip(message: Message):
    await message.answer('Выберите теорию:', reply_markup=theory())

@dp.message(F.text == '/calc')
async def send_calculator(message: types.Message):
    await message.answer("Калькулятор\nВведите выражение с помощью кнопок:", reply_markup=get_calculator_keyboard())

# === ФИЗИКА ===
@dp.callback_query(F.data == 'fiz')
async def callback_fiz(callback: CallbackQuery):
    await callback.answer('Вы выбрали Физику')
    await callback.message.edit_text('Выберите тему', reply_markup=fiz_kb())

@dp.callback_query(F.data == 'fiz_food')
async def callback_fiz_food(callback: CallbackQuery):
    await callback.answer('Механика')
    await callback.message.edit_text(
        '''МЕХАНИКА

7–8 класс:
• Путь (s) — длина траектории движения, скалярная величина, [м].
• Перемещение (Δr) — вектор от начальной до конечной точки, [м].
• Скорость равномерного движения: v = s / t.
  где v — скорость [м/с], s — путь [м], t — время [с].
• Сила (F) — мера взаимодействия тел, вызывает ускорение, [Н].
• Сила тяжести: Fₜ = m·g.
  где m — масса [кг], g ≈ 10 Н/кг (ускорение свободного падения).
• Плотность: ρ = m / V.
  где ρ — плотность [кг/м³], V — объём [м³].
• Давление: p = F / S.
  где p — давление [Па], S — площадь опоры [м²].

9 класс:
• Ускорение: a = (v - v₀) / t.
  где v₀ — начальная скорость [м/с], v — конечная скорость [м/с].
• Равноускоренное движение:
  v = v₀ + a·t,
  s = v₀·t + ½a·t²,
  v² - v₀² = 2a·s.
• Законы Ньютона:
  1) Тело сохраняет состояние покоя или равномерного прямолинейного движения (РПД), если сумма сил = 0.
  2) F = m·a — ускорение прямо пропорционально силе и обратно пропорционально массе.
  3) Силы действия и противодействия равны по модулю, противоположны по направлению и приложены к разным телам.
• Импульс: p = m·v, [кг·м/с]. Закон сохранения импульса: Σp = const в замкнутой системе.
• Механическая работа: A = F·s·cosα.
  где α — угол между векторами силы и перемещения.
• Мощность: P = A / t, [Вт].
• Кинетическая энергия: Eₖ = ½m·v².
• Потенциальная энергия (в поле тяжести): Eₚ = m·g·h.
• Закон сохранения механической энергии: Eₖ + Eₚ = const (если нет трения).

10–11 класс:
• Векторное описание: r(t) — радиус-вектор, v = dr/dt, a = dv/dt.
• Тангенциальное ускорение: aₜ = dv/dt — изменяет модуль скорости.
• Нормальное ускорение: aₙ = v²/R — изменяет направление скорости.
• Сила трения скольжения: Fₜр = μ·N.
  где μ — коэффициент трения (безразмерный), N — сила нормальной реакции опоры [Н].
• Закон Гука: F = -k·Δx.
  где k — жёсткость пружины [Н/м], Δx — удлинение [м].
• Момент силы: M = F·l·sinφ.
  где l — плечо силы [м], φ — угол между вектором силы и плечом.
• Условия равновесия твёрдого тела:
  ΣF = 0 (нет поступательного ускорения),
  ΣM = 0 (нет углового ускорения).
• Центр масс системы: R = (Σmᵢ·rᵢ) / Σmᵢ.
• Закон сохранения момента импульса: L = I·ω = const.
  где I — момент инерции [кг·м²], ω — угловая скорость [рад/с].
• Теорема Штейнера: I = I₀ + m·d².
  где I₀ — момент инерции относительно оси через центр масс, d — расстояние до новой оси.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="fiz")]
        ])
    )

@dp.callback_query(F.data == 'fiz_newton')
async def callback_fiz_newton(callback: CallbackQuery):
    await callback.answer('Законы Ньютона')
    await callback.message.edit_text(
        '''ЗАКОНЫ НЬЮТОНА

7–8 класс:
— Не изучаются подробно.

9 класс:
• Первый закон (закон инерции):
  Если на тело не действуют другие тела или действие скомпенсировано, то тело сохраняет состояние покоя или равномерного прямолинейного движения.
  Инерция — свойство тела сохранять своё состояние движения.
• Второй закон:
  Ускорение тела прямо пропорционально равнодействующей силе и обратно пропорционально его массе: a = F/m → F = m·a.
  Единица силы — ньютон (Н): 1 Н = 1 кг·м/с².
• Третий закон:
  Силы, с которыми два тела действуют друг на друга, равны по модулю, противоположны по направлению и лежат на одной прямой: F₁₂ = -F₂₁.
  Эти силы приложены к разным телам, поэтому не уравновешивают друг друга.

10–11 класс:
• Применение законов в неинерциальных системах отсчёта.
• Введение понятия инерциальной системы отсчёта (ИСО) — система, в которой выполняется первый закон Ньютона.
• Принцип относительности Галилея: все механические явления протекают одинаково во всех ИСО.
• Преобразования Галилея: x' = x - vt, v' = v - u.
• Ограничения классической механики: при скоростях, близких к скорости света, законы Ньютона не выполняются — требуется релятивистская механика.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="fiz")]
        ])
    )

@dp.callback_query(F.data == 'fiz_tepl')
async def callback_fiz_tepl(callback: CallbackQuery):
    await callback.answer('Тепловые явления')
    await callback.message.edit_text(
        '''ТЕПЛОВЫЕ ЯВЛЕНИЯ

7–8 класс:
• Температура — мера средней кинетической энергии молекул.
• Теплопередача: теплопроводность (через вещество), конвекция (движение жидкости/газа), излучение (инфракрасные волны).
• Q = c·m·Δt — количество теплоты при нагревании/охлаждении.
  где c — удельная теплоёмкость [Дж/(кг·°C)], Δt — изменение температуры [°C].
• Q = λ·m — при плавлении/кристаллизации.
  где λ — удельная теплота плавления [Дж/кг].
• Q = L·m — при парообразовании/конденсации.
  где L — удельная теплота парообразования [Дж/кг].
• КПД нагревателя: η = Qₚₒл / Qₜₒₚл · 100%.

9 класс:
• Тепловое расширение: ΔL = α·L₀·ΔT.
  где α — коэффициент линейного расширения [1/°C], L₀ — начальная длина.
• Первый закон термодинамики (вводится): Q = ΔU + A.
  где ΔU — изменение внутренней энергии, A — работа газа.

10–11 класс:
• Абсолютная температура: T(K) = t(°C) + 273.15.
• Основное уравнение МКТ: p = ⅓·n·m₀·⟨v²⟩ = ⅔·n·Eₖ.
  где n — концентрация молекул [1/м³], m₀ — масса одной молекулы [кг], Eₖ — средняя кинетическая энергия.
• Связь Eₖ и T: Eₖ = ³⁄₂·k·T.
  где k = 1.38·10⁻²³ Дж/К — постоянная Больцмана.
• Уравнение состояния идеального газа: p·V = ν·R·T = (m/M)·R·T.
  где ν — количество вещества [моль], R = 8.31 Дж/(моль·К), M — молярная масса [кг/моль].
• Изопроцессы:
  Бойля–Мариотта (T=const): p₁V₁ = p₂V₂,
  Гей-Люссака (p=const): V₁/T₁ = V₂/T₂,
  Шарля (V=const): p₁/T₁ = p₂/T₂.
• Внутренняя энергия одноатомного газа: U = ³⁄₂·ν·R·T.
• Работа газа: A = ∫p·dV. При изобаре: A = p·ΔV.
• Первый закон термодинамики: Q = ΔU + A.
• Тепловая машина: η = A / Q₁ = (Q₁ - Q₂)/Q₁.
• Цикл Карно (идеальный): ηₘₐₓ = (T₁ - T₂)/T₁.
  где T₁ — температура нагревателя, T₂ — холодильника (в Кельвинах).''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="fiz")]
        ])
    )

@dp.callback_query(F.data == 'fiz_eldin')
async def callback_fiz_eldin(callback: CallbackQuery):
    await callback.answer('Электродинамика')
    await callback.message.edit_text(
        '''ЭЛЕКТРОДИНАМИКА

7–8 класс:
• Электрический заряд (q) — свойство тел, создающее электрическое поле, [Кл].
• Простая цепь: источник → провода → потребитель (лампочка, резистор).
• Безопасность: напряжение > 36 В опасно для человека.

9 класс:
• Сила тока: I = q / t, [А].
• Напряжение: U = A / q, [В].
• Сопротивление: R = U / I, [Ом].
• Закон Ома для участка цепи: I = U / R.
• Последовательное соединение:
  I = const, U = U₁ + U₂, R = R₁ + R₂.
• Параллельное соединение:
  U = const, I = I₁ + I₂, 1/R = 1/R₁ + 1/R₂.
• Мощность тока: P = U·I = I²·R = U²/R, [Вт].
• Закон Джоуля–Ленца: Q = I²·R·t — выделение тепла.

10–11 класс:
• Закон Кулона: F = k·|q₁q₂|/(ε·r²).
  где k = 9·10⁹ Н·м²/Кл², ε — диэлектрическая проницаемость среды, r — расстояние [м].
• Напряжённость поля: E = F/q, [В/м]. Для точечного заряда: E = k·q/r².
• Потенциал: φ = Wₚ/q, [В]. Разность потенциалов: U = φ₁ - φ₂.
• Связь E и U в однородном поле: E = U / d, где d — расстояние между пластинами.
• Конденсатор: C = q / U, [Ф]. Ёмкость плоского: C = ε·ε₀·S / d.
  где ε₀ = 8.85·10⁻¹² Ф/м — электрическая постоянная, S — площадь пластин.
• Энергия конденсатора: W = ½·C·U².
• ЭДС источника: ε = Aₛₜ / q — работа сторонних сил по переносу заряда.
• Закон Ома для полной цепи: I = ε / (R + r), где r — внутреннее сопротивление.
• Правила Кирхгофа:
  1) Алгебраическая сумма токов в узле = 0.
  2) Алгебраическая сумма ЭДС = сумме падений напряжения в замкнутом контуре.
• Сила Ампера: Fₐ = I·B·l·sinα, [Н].
  где B — магнитная индукция [Тл], l — длина проводника [м].
• Сила Лоренца: Fₗ = |q|·v·B·sinα.
  Направление — по правилу левой руки.
• Магнитный поток: Φ = B·S·cosα, [Вб].
• Закон Фарадея: εᵢ = -ΔΦ/Δt — ЭДС индукции.
• Самоиндукция: εₛ = -L·ΔI/Δt.
• Энергия магнитного поля: W = ½·L·I².''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="fiz")]
        ])
    )

@dp.callback_query(F.data == 'fiz_coleb')
async def callback_fiz_coleb(callback: CallbackQuery):
    await callback.answer('Колебания и волны')
    await callback.message.edit_text(
        '''КОЛЕБАНИЯ И ВОЛНЫ

7–8 класс:
• Звук — продольная механическая волна, требует среды.
• Частота (ν) — число колебаний в секунду, [Гц]. Определяет высоту звука.
• Амплитуда — максимальное отклонение от положения равновесия. Определяет громкость.
• Скорость звука в воздухе ≈ 340 м/с, в воде ≈ 1500 м/с.

9 класс:
• Гармонические колебания: x(t) = A·cos(ωt + φ₀).
  где A — амплитуда [м], ω — циклическая частота [рад/с], φ₀ — начальная фаза.
• Период: T = 2π/ω, частота: ν = 1/T.
• Пружинный маятник: T = 2π·√(m/k).
  где m — масса [кг], k — жёсткость пружины [Н/м].
• Математический маятник: T = 2π·√(l/g).
  где l — длина нити [м].
• Полная энергия: E = ½·k·A² = const.
• Резонанс — резкое возрастание амплитуды при совпадении частоты вынуждающей силы с собственной частотой системы.

10–11 класс:
• Дифференциальное уравнение свободных колебаний: x″ + ω²x = 0.
• Затухающие колебания: x(t) = A₀·e^(-βt)·cos(ωt).
  где β — коэффициент затухания.
• Волна: y(x,t) = A·cos(ωt - kx).
  где k = 2π/λ — волновое число, λ — длина волны [м].
• Скорость волны: v = λ·ν.
• Интерференция:
  усиление при Δd = m·λ,
  ослабление при Δd = (2m+1)·λ/2.
• Дифракция — отклонение волн от прямолинейного распространения при встрече с препятствием.
• Электромагнитные волны:
  c = 1/√(μ₀ε₀) ≈ 3·10⁸ м/с — скорость света в вакууме.
  E = c·B — связь напряжённостей электрического и магнитного полей.
• Шкала ЭМ волн: радио → микроволны → ИК → видимый свет → УФ → рентген → γ-излучение.
• Эффект Доплера: изменение частоты при движении источника или наблюдателя.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="fiz")]
        ])
    )

# === МАТЕМАТИКА ===
@dp.callback_query(F.data == 'mat')
async def callback_mat(callback: CallbackQuery):
    await callback.answer('Вы выбрали Математику')
    await callback.message.edit_text('Выберите тему', reply_markup=mat_kb())

@dp.callback_query(F.data == 'mat_algebra')
async def callback_mat_algebra(callback: CallbackQuery):
    await callback.answer('Алгебра')
    await callback.message.edit_text(
        '''АЛГЕБРА

7–8 класс:
• Линейное уравнение: a·x + b = 0 → x = -b/a (при a ≠ 0).
• Система двух уравнений:
  метод подстановки — выразить одну переменную и подставить,
  метод сложения — сложить уравнения так, чтобы исключить одну переменную.
• Степени:
  aⁿ·aᵐ = aⁿ⁺ᵐ,
  (aⁿ)ᵐ = aⁿᵐ,
  a⁻ⁿ = 1/aⁿ (a ≠ 0).
• Формулы сокращённого умножения (ФСУ):
  (a±b)² = a² ± 2ab + b²,
  a² - b² = (a-b)(a+b),
  (a±b)³ = a³ ± 3a²b + 3ab² ± b³.
• Корни:
  √(a·b) = √a·√b (a≥0, b≥0),
  √(a/b) = √a/√b (a≥0, b>0).

9 класс:
• Квадратное уравнение: a·x² + b·x + c = 0 (a ≠ 0).
• Дискриминант: D = b² - 4ac.
  Если D > 0 — два корня, D = 0 — один корень, D < 0 — нет действительных корней.
• Корни: x₁,₂ = (-b ± √D)/(2a).
• Теорема Виета: x₁ + x₂ = -b/a, x₁·x₂ = c/a.
• Неравенства: метод интервалов — найти нули, определить знаки на промежутках.
• Арифметическая прогрессия:
  aₙ = a₁ + d·(n-1),
  Sₙ = n·(a₁ + aₙ)/2.
• Геометрическая прогрессия:
  bₙ = b₁·qⁿ⁻¹,
  Sₙ = b₁·(1 - qⁿ)/(1 - q) (q ≠ 1).

10–11 класс:
• Логарифм: logₐb = c ⇔ aᶜ = b (a > 0, a ≠ 1, b > 0).
• Основные свойства:
  logₐ(xy) = logₐx + logₐy,
  logₐ(x/y) = logₐx - logₐy,
  logₐ(xᵏ) = k·logₐx.
• Формула перехода к другому основанию:
  logₐb = logₑb / logₑa = ln b / ln a.
• Комбинаторика:
  Перестановки: Pₙ = n! — число способов упорядочить n элементов.
  Сочетания: Cₙᵏ = n! / (k!(n-k)!) — выбор k элементов из n без учёта порядка.
  Размещения: Aₙᵏ = n! / (n-k)! — выбор k элементов из n с учётом порядка.
• Бином Ньютона:
  (a + b)ⁿ = Σₖ₌₀ⁿ Cₙᵏ·aⁿ⁻ᵏ·bᵏ.
• Метод математической индукции:
  1) Проверить базу (n=1),
  2) Предположить верность для n=k,
  3) Доказать для n=k+1.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

@dp.callback_query(F.data == 'mat_geometry')
async def callback_mat_geometry(callback: CallbackQuery):
    await callback.answer('Геометрия')
    await callback.message.edit_text(
        '''ГЕОМЕТРИЯ

7–8 класс:
• Сумма углов треугольника = 180°.
• Теорема Пифагора: c² = a² + b² (для прямоугольного треугольника, c — гипотенуза).
• Площади:
  треугольник: S = ½·a·h (a — основание, h — высота),
  прямоугольник: S = a·b,
  круг: S = π·r².
• Признаки равенства треугольников: по трём сторонам (SSS), по двум сторонам и углу между ними (SAS), по стороне и двум прилежащим углам (ASA).

9 класс:
• Теорема косинусов: c² = a² + b² - 2ab·cosγ.
  где γ — угол между сторонами a и b.
• Теорема синусов: a/sinα = b/sinβ = c/sinγ = 2R.
  где R — радиус описанной окружности.
• Вектор AB = (x₂ - x₁, y₂ - y₁).
• Длина вектора: |AB| = √[(x₂-x₁)² + (y₂-y₁)²].
• Скалярное произведение: a·b = x₁x₂ + y₁y₂ = |a||b|cosφ.

10–11 класс:
• Векторное произведение (в 3D): |a×b| = |a||b|sinφ.
  Направление — по правилу правого винта.
• Смешанное произведение: (a×b)·c = объём параллелепипеда.
• Объёмы:
  призма: V = Sₒₛₙ·h,
  пирамида: V = ⅓·Sₒₛₙ·h,
  шар: V = ⁴⁄₃·π·r³.
• Площадь сферы: S = 4πr².
• Уравнение плоскости: Ax + By + Cz + D = 0.
• Расстояние от точки M(x₀,y₀,z₀) до плоскости:
  d = |Ax₀ + By₀ + Cz₀ + D| / √(A² + B² + C²).''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

@dp.callback_query(F.data == 'mat_trigonometry')
async def callback_mat_trigonometry(callback: CallbackQuery):
    await callback.answer('Тригонометрия')
    await callback.message.edit_text(
        '''ТРИГОНОМЕТРИЯ

7–8 класс:
• В прямоугольном треугольнике:
  sin α = противолежащий катет / гипотенуза,
  cos α = прилежащий катет / гипотенуза,
  tg α = противолежащий / прилежащий.
• Основное тождество: sin²α + cos²α = 1.
• Значения:
  sin 30° = ½, cos 30° = √3/2,
  sin 45° = cos 45° = √2/2,
  sin 60° = √3/2, cos 60° = ½.

9 класс:
• Единичная окружность — окружность радиуса 1 с центром в начале координат.
• Формулы приведения — позволяют выразить триг. функции углов >90° через острые.
• Простейшие уравнения:
  sin x = a → x = (-1)ⁿ·arcsin a + πn,
  cos x = a → x = ±arccos a + 2πn,
  tg x = a → x = arctg a + πn, где n ∈ ℤ.

10–11 класс:
• Формулы сложения:
  sin(α±β) = sinα·cosβ ± cosα·sinβ,
  cos(α±β) = cosα·cosβ ∓ sinα·sinβ.
• Двойной угол:
  sin2α = 2·sinα·cosα,
  cos2α = cos²α - sin²α = 2cos²α - 1 = 1 - 2sin²α.
• Универсальная подстановка: t = tg(x/2),
  тогда sin x = 2t/(1+t²), cos x = (1-t²)/(1+t²).
• Метод вспомогательного угла:
  a·sinx + b·cosx = √(a²+b²)·sin(x + φ),
  где cosφ = a/√(a²+b²), sinφ = b/√(a²+b²).
• Обратные функции:
  arcsin: [-1,1] → [-π/2, π/2] — нечётная,
  arccos: [-1,1] → [0, π] — убывающая,
  arctg: ℝ → (-π/2, π/2) — нечётная и возрастающая.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

@dp.callback_query(F.data == 'mat_functions')
async def callback_mat_functions(callback: CallbackQuery):
    await callback.answer('Функции')
    await callback.message.edit_text(
        '''ФУНКЦИИ

7–8 класс:
• Линейная функция: y = kx + b.
  График — прямая. k — угловой коэффициент (наклон).
• Прямая пропорциональность: y = kx (проходит через начало координат).
• Обратная пропорциональность: y = k/x — гипербола.
• Квадратичная функция: y = x² — парабола, ветви вверх.

9 класс:
• Квадратичная функция: y = ax² + bx + c.
  Вершина параболы: x₀ = -b/(2a), y₀ = f(x₀).
• Нули функции — решения уравнения f(x) = 0.
• Возрастание/убывание: функция возрастает, если при x₁ < x₂ ⇒ f(x₁) < f(x₂).
• Чётность: f(-x) = f(x) — чётная (симметрия относительно OY),
  f(-x) = -f(x) — нечётная (симметрия относительно начала координат).

10–11 класс:
• Показательная функция: y = aˣ (a > 0, a ≠ 1).
  Свойства: D = ℝ, E = (0; ∞), возрастает при a > 1, убывает при 0 < a < 1.
• Логарифмическая функция: y = logₐx.
  D = (0; ∞), E = ℝ, обратна показательной.
• Асимптоты:
  вертикальная — прямая x = a, к которой график приближается,
  горизонтальная — y = b,
  наклонная — y = kx + b (при x → ±∞).
• Исследование функции включает:
  1) Область определения D(f),
  2) Чётность/периодичность,
  3) Нули и промежутки знакопостоянства,
  4) Производную → монотонность и экстремумы,
  5) Построение графика.
• Композиция: (f∘g)(x) = f(g(x)).
• Обратная функция существует, если f — биекция (взаимно однозначна).''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

@dp.callback_query(F.data == 'mat_calculus')
async def callback_mat_calculus(callback: CallbackQuery):
    await callback.answer('Математический анализ')
    await callback.message.edit_text(
        '''МАТЕМАТИЧЕСКИЙ АНАЛИЗ

7–8 класс:
— Не изучается.

9 класс:
— Не изучается.

10–11 класс:
• Предел функции: limₓ→ₐ f(x) = L означает, что f(x) стремится к L при x → a.
• Производная — скорость изменения функции:
  f′(x) = limₕ→₀ [f(x+h) - f(x)] / h.
• Основные производные:
  (xⁿ)′ = n·xⁿ⁻¹,
  (√x)′ = 1/(2√x),
  (sin x)′ = cos x,
  (cos x)′ = -sin x,
  (tg x)′ = 1/cos²x,
  (eˣ)′ = eˣ,
  (aˣ)′ = aˣ·ln a,
  (ln x)′ = 1/x,
  (logₐx)′ = 1/(x·ln a).
• Правила дифференцирования:
  (u ± v)′ = u′ ± v′,
  (u·v)′ = u′v + uv′,
  (u/v)′ = (u′v - uv′)/v²,
  (f(g(x)))′ = f′(g(x))·g′(x) — правило цепочки.
• Геометрический смысл: f′(x₀) = k — угловой коэффициент касательной к графику в точке x₀.
• Физический смысл: если x(t) — координата, то v(t) = x′(t), a(t) = v′(t).
• Экстремумы: если f′(x₀) = 0 и f′ меняет знак — экстремум.
  f″(x₀) > 0 → минимум, f″(x₀) < 0 → максимум.
• Первообразная F(x): F′(x) = f(x).
• Неопределённый интеграл: ∫f(x)dx = F(x) + C.
• Основные интегралы:
  ∫xⁿ dx = xⁿ⁺¹/(n+1) + C (n ≠ -1),
  ∫dx/x = ln|x| + C,
  ∫eˣ dx = eˣ + C,
  ∫sin x dx = -cos x + C,
  ∫cos x dx = sin x + C.
• Формула Ньютона–Лейбница:
  ∫ₐᵇ f(x)dx = F(b) - F(a).
• Приложения: площадь под кривой, объём тела вращения, работа переменной силы.''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

@dp.callback_query(F.data == 'mat_probability')
async def callback_mat_probability(callback: CallbackQuery):
    await callback.answer('Теория вероятностей')
    await callback.message.edit_text(
        '''ТЕОРИЯ ВЕРОЯТНОСТЕЙ И СТАТИСТИКА

7–8 класс:
— Не изучается.

9 класс:
• Случайное событие — результат эксперимента, который может произойти или нет.
• Классическое определение вероятности:
  P(A) = m / n,
  где m — число благоприятных исходов, n — общее число равновозможных исходов.
• Пример: при броске кубика P(выпадет 3) = 1/6.
• Среднее арифметическое выборки: x̄ = (x₁ + x₂ + ... + xₙ) / n.

10–11 класс:
• Алгебра событий:
  A ∪ B — объединение ("A или B"),
  A ∩ B — пересечение ("A и B"),
  Ā — противоположное событие.
• Теорема сложения: P(A ∪ B) = P(A) + P(B) - P(A ∩ B).
• Независимые события: P(A ∩ B) = P(A)·P(B).
• Условная вероятность: P(A|B) = P(A ∩ B) / P(B) (при P(B) > 0).
• Формула полной вероятности:
  P(A) = P(H₁)P(A|H₁) + ... + P(Hₙ)P(A|Hₙ),
  где H₁...Hₙ — полная группа гипотез.
• Формула Байеса:
  P(Hᵢ|A) = P(Hᵢ)P(A|Hᵢ) / P(A).
• Биномиальное распределение:
  Pₙ(k) = Cₙᵏ·pᵏ·(1-p)ⁿ⁻ᵏ,
  где p — вероятность успеха в одном испытании.
• Нормальное распределение (Гаусса):
  f(x) = (1/(σ√(2π)))·exp(-(x-μ)²/(2σ²)),
  где μ — математическое ожидание, σ — стандартное отклонение.
• Правило трёх сигм: P(|X - μ| < 3σ) ≈ 0.997.
• Выборочная дисперсия (несмещённая):
  s² = (1/(n-1))·Σ(xᵢ - x̄)².
• Коэффициент корреляции Пирсона:
  r = cov(X,Y) / (σₓ·σᵧ),
  где cov(X,Y) = (1/n)·Σ(xᵢ - x̄)(yᵢ - ȳ).''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="mat")]
        ])
    )

# === КАЛЬКУЛЯТОР ===
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
            new_expression = f"{current_expression} = {result}"
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
            reply_markup=get_calculator_keyboard()
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            logging.error(f"Ошибка при редактировании сообщения: {e}")
    await callback_query.answer()

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(
        f" Ваши ID:\n"
        f" Ваш User ID: `{message.from_user.id}`\n"
        f" ID этого чата: `{message.chat.id}`\n"
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