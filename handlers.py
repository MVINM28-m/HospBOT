import logging
from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, DOCTORS
from database import db
from keyboards import *
from utils import format_appointment, generate_calendar_event

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для FSM (Finite State Machine)
class AppointmentStates(StatesGroup):
    waiting_for_patient_name = State()
    waiting_for_doctor = State()
    waiting_for_procedure = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()

class EditStates(StatesGroup):
    waiting_for_new_patient_name = State()
    waiting_for_new_doctor = State()
    waiting_for_new_procedure = State()
    waiting_for_new_date = State()
    waiting_for_new_time = State()

# Обработчики команд
async def cmd_start(message: Message):
    """Обработчик команды /start - приветствие пользователя по имени"""
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name)

    welcome_text = (
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        f"Добро пожаловать в бот клиники «Здоровье».\n"
        f"Здесь вы можете записаться на прием к врачу, "
        f"просмотреть свои записи и управлять ими."
    )

    is_admin = user.id in ADMIN_IDS
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin)
    )

async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/menu - Главное меню\n"
        "/stop - Завершить работу\n\n"
        "Также вы можете использовать инлайн-кнопки для навигации."
    )
    await message.answer(help_text)

async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    user = message.from_user
    is_admin = user.id in ADMIN_IDS
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(is_admin)
    )

async def cmd_stop(message: Message):
    """Обработчик команды /stop"""
    await message.answer(
        "👋 До свидания! Чтобы возобновить работу, нажмите /start"
    )

# Обработчики колбэков
async def process_callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = callback.from_user
    is_admin = user.id in ADMIN_IDS

    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard(is_admin)
    )
    await callback.answer()

async def process_callback_make_appointment(callback: CallbackQuery, state: FSMContext):
    """Начало процесса записи"""
    await callback.message.edit_text(
        "👤 Введите имя и фамилию пациента:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AppointmentStates.waiting_for_patient_name)
    await callback.answer()

async def process_patient_name(message: Message, state: FSMContext):
    """Обработка имени пациента"""
    patient_name = message.text.strip()

    if len(patient_name) < 2 or len(patient_name) > 50:
        await message.answer(
            "❌ Пожалуйста, введите корректное имя (от 2 до 50 символов):"
        )
        return

    await state.update_data(patient_name=patient_name)

    await message.answer(
        "👨‍⚕️ Выберите врача:",
        reply_markup=get_doctors_keyboard()
    )
    await state.set_state(AppointmentStates.waiting_for_doctor)

async def process_callback_select_doctor(callback: CallbackQuery, state: FSMContext):
    """Выбор врача"""
    doctor = callback.data.split(':', 1)[1]
    await state.update_data(doctor=doctor)

    await callback.message.edit_text(
        f"💉 Выберите процедуру для {doctor}:",
        reply_markup=get_procedures_keyboard(doctor)
    )
    await state.set_state(AppointmentStates.waiting_for_procedure)
    await callback.answer()

async def process_callback_select_procedure(callback: CallbackQuery, state: FSMContext):
    """Выбор процедуры"""
    procedure = callback.data.split(':', 1)[1]
    await state.update_data(procedure=procedure)

    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=get_dates_keyboard()
    )
    await state.set_state(AppointmentStates.waiting_for_date)
    await callback.answer()

async def process_callback_select_date(callback: CallbackQuery, state: FSMContext):
    """Выбор даты"""
    date = callback.data.split(':', 1)[1]
    await state.update_data(date=date)

    await callback.message.edit_text(
        "⏰ Выберите время:",
        reply_markup=get_times_keyboard()
    )
    await state.set_state(AppointmentStates.waiting_for_time)
    await callback.answer()

async def process_callback_select_time(callback: CallbackQuery, state: FSMContext):
    """Выбор времени"""
    time = callback.data.split(':', 1)[1]
    data = await state.get_data()

    # Проверка доступности времени
    if not db.is_appointment_available(data['doctor'], data['date'], time):
        await callback.message.edit_text(
            "❌ Это время уже занято. Пожалуйста, выберите другое время:",
            reply_markup=get_times_keyboard()
        )
        await callback.answer()
        return

    await state.update_data(time=time)

    # Показываем подтверждение
    appointment_info = (
        f"📋 Проверьте данные записи:\n\n"
        f"👤 Пациент: {data['patient_name']}\n"
        f"👨‍⚕️ Врач: {data['doctor']}\n"
        f"💉 Процедура: {data['procedure']}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {time}\n\n"
        f"Всё верно?"
    )

    await callback.message.edit_text(
        appointment_info,
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(AppointmentStates.waiting_for_confirmation)
    await callback.answer()

async def process_callback_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    data = await state.get_data()
    user = callback.from_user

    # Создаем запись в базе данных
    appointment_id = db.create_appointment(
        user_id=user.id,
        patient_name=data['patient_name'],
        doctor=data['doctor'],
        procedure=data['procedure'],
        date=data['date'],
        time=data['time']
    )

    success_text = (
        f"✅ Запись успешно создана!\n\n"
        f"Номер записи: #{appointment_id}\n"
        f"👤 Пациент: {data['patient_name']}\n"
        f"👨‍⚕️ Врач: {data['doctor']}\n"
        f"💉 Процедура: {data['procedure']}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}"
    )

    await callback.message.edit_text(success_text)

    # Возвращаемся в главное меню
    is_admin = user.id in ADMIN_IDS
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(is_admin)
    )

    await state.clear()
    await callback.answer()

async def process_callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    user = callback.from_user
    is_admin = user.id in ADMIN_IDS

    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.\n\nГлавное меню:",
        reply_markup=get_main_keyboard(is_admin)
    )
    await callback.answer()

async def process_callback_my_appointments(callback: CallbackQuery):
    """Просмотр записей пользователя"""
    user = callback.from_user
    appointments = db.get_appointments(user.id)

    if not appointments:
        await callback.message.edit_text(
            "📭 У вас пока нет записей.\n\n"
            "Чтобы создать новую запись, нажмите «Записаться».",
            reply_markup=get_main_keyboard(user.id in ADMIN_IDS)
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📋 Ваши записи:",
        reply_markup=get_appointments_keyboard(appointments)
    )
    await callback.answer()

async def process_callback_view_appointment(callback: CallbackQuery):
    """Просмотр конкретной записи"""
    appointment_id = int(callback.data.split(':')[1])
    appointment = db.get_appointment(appointment_id)
    user = callback.from_user

    if not appointment:
        await callback.message.edit_text(
            "❌ Запись не найдена.",
            reply_markup=get_main_keyboard(user.id in ADMIN_IDS)
        )
        await callback.answer()
        return

    text = format_appointment(appointment)
    is_admin = user.id in ADMIN_IDS

    await callback.message.edit_text(
        text,
        reply_markup=get_appointment_actions_keyboard(appointment_id, is_admin)
    )
    await callback.answer()

async def process_callback_cancel_appointment(callback: CallbackQuery):
    """Отмена записи пользователем"""
    appointment_id = int(callback.data.split(':')[1])

    if db.delete_appointment(appointment_id):
        await callback.message.edit_text(
            "✅ Запись успешно отменена.",
            reply_markup=get_main_keyboard(callback.from_user.id in ADMIN_IDS)
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось отменить запись.",
            reply_markup=get_main_keyboard(callback.from_user.id in ADMIN_IDS)
        )
    await callback.answer()

async def process_callback_add_to_calendar(callback: CallbackQuery):
    """Добавление записи в календарь"""
    appointment_id = int(callback.data.split(':')[1])
    appointment = db.get_appointment(appointment_id)

    if not appointment:
        await callback.answer("❌ Запись не найдена")
        return

    # Генерируем файл для календаря
    calendar_file = generate_calendar_event(appointment)

    if calendar_file:
        with open(calendar_file, 'rb') as f:
            await callback.message.answer_document(
                types.FSInputFile(calendar_file),
                caption="📅 Файл для добавления в календарь"
            )

    await callback.answer("✅ Файл для календаря создан")

async def process_callback_doctors_list(callback: CallbackQuery):
    """Список врачей"""
    text = "👨‍⚕️ Наши врачи:\n\n"
    for doctor in DOCTORS:
        text += f"• {doctor}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_main_keyboard(callback.from_user.id in ADMIN_IDS)
    )
    await callback.answer()

async def process_callback_about(callback: CallbackQuery):
    """Информация о клинике"""
    text = (
        "🏥 Клиника «Здоровье»\n\n"
        "📍 Адрес: г. Москва, ул. Медицинская, д. 10\n"
        "📞 Телефон: +7 (495) 123-45-67\n"
        "🕒 Режим работы: Пн-Пт 8:00-20:00, Сб 9:00-18:00\n\n"
        "Мы заботимся о вашем здоровье!"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_main_keyboard(callback.from_user.id in ADMIN_IDS)
    )
    await callback.answer()

# Админские обработчики
async def process_callback_all_appointments(callback: CallbackQuery):
    """Просмотр всех записей (для админа)"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен")
        return

    appointments = db.get_appointments()

    if not appointments:
        await callback.message.edit_text(
            "📭 Нет записей.",
            reply_markup=get_main_keyboard(True)
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📋 Все записи:",
        reply_markup=get_appointments_keyboard(appointments, is_admin=True)
    )
    await callback.answer()

async def process_callback_admin_view(callback: CallbackQuery):
    """Просмотр записи админом"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен")
        return

    appointment_id = int(callback.data.split(':')[1])
    appointment = db.get_appointment(appointment_id)

    if not appointment:
        await callback.message.edit_text(
            "❌ Запись не найдена.",
            reply_markup=get_main_keyboard(True)
        )
        await callback.answer()
        return

    text = format_appointment(appointment, is_admin=True)

    await callback.message.edit_text(
        text,
        reply_markup=get_appointment_actions_keyboard(appointment_id, is_admin=True)
    )
    await callback.answer()

async def process_callback_delete_appointment(callback: CallbackQuery):
    """Удаление записи админом"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен")
        return

    appointment_id = int(callback.data.split(':')[1])

    if db.delete_appointment(appointment_id):
        await callback.message.edit_text(
            "✅ Запись успешно удалена.",
            reply_markup=get_main_keyboard(True)
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось удалить запись.",
            reply_markup=get_main_keyboard(True)
        )
    await callback.answer()

async def process_callback_edit_appointment(callback: CallbackQuery):
    """Начало редактирования записи"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен")
        return

    appointment_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        "✏️ Что вы хотите отредактировать?",
        reply_markup=get_admin_edit_keyboard(appointment_id)
    )
    await callback.answer()

async def process_callback_users_list(callback: CallbackQuery):
    """Список пользователей для админа"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Доступ запрещен")
        return

    users = db.get_users()

    if not users:
        await callback.message.edit_text(
            "👥 Нет зарегистрированных пользователей.",
            reply_markup=get_main_keyboard(True)
        )
        await callback.answer()
        return

    text = "👥 Список пользователей:\n\n"
    for user_id, user_data in users.items():
        text += f"ID: {user_id}\n"
        text += f"Имя: {user_data['first_name']}\n"
        if user_data['username']:
            text += f"Username: @{user_data['username']}\n"
        text += f"Регистрация: {user_data['registered_at'][:10]}\n"
        text += "-" * 20 + "\n"

    await callback.message.edit_text(text)
    await callback.answer()

# Функция регистрации обработчиков для aiogram 3.x
def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""

    # Команды
    dp.message.register(cmd_start, Command(commands=['start']))
    dp.message.register(cmd_help, Command(commands=['help']))
    dp.message.register(cmd_menu, Command(commands=['menu']))
    dp.message.register(cmd_stop, Command(commands=['stop']))

    # Основные callback'и
    dp.callback_query.register(process_callback_main_menu, lambda c: c.data == 'main_menu')
    dp.callback_query.register(process_callback_make_appointment, lambda c: c.data == 'make_appointment')
    dp.callback_query.register(process_callback_my_appointments, lambda c: c.data == 'my_appointments')
    dp.callback_query.register(process_callback_doctors_list, lambda c: c.data == 'doctors_list')
    dp.callback_query.register(process_callback_about, lambda c: c.data == 'about')

    # Процесс записи
    dp.callback_query.register(process_callback_select_doctor,
                              lambda c: c.data.startswith('select_doctor:'),
                              StateFilter(AppointmentStates.waiting_for_doctor))
    dp.callback_query.register(process_callback_select_procedure,
                              lambda c: c.data.startswith('select_procedure:'),
                              StateFilter(AppointmentStates.waiting_for_procedure))
    dp.callback_query.register(process_callback_select_date,
                              lambda c: c.data.startswith('select_date:'),
                              StateFilter(AppointmentStates.waiting_for_date))
    dp.callback_query.register(process_callback_select_time,
                              lambda c: c.data.startswith('select_time:'),
                              StateFilter(AppointmentStates.waiting_for_time))
    dp.callback_query.register(process_callback_confirm,
                              lambda c: c.data == 'confirm',
                              StateFilter(AppointmentStates.waiting_for_confirmation))

    # Управление записями
    dp.callback_query.register(process_callback_view_appointment,
                              lambda c: c.data.startswith('view_appointment:'))
    dp.callback_query.register(process_callback_cancel_appointment,
                              lambda c: c.data.startswith('cancel_appointment:'))
    dp.callback_query.register(process_callback_add_to_calendar,
                              lambda c: c.data.startswith('add_to_calendar:'))

    # Админские callback'и
    dp.callback_query.register(process_callback_all_appointments,
                              lambda c: c.data == 'all_appointments')
    dp.callback_query.register(process_callback_admin_view,
                              lambda c: c.data.startswith('admin_view:'))
    dp.callback_query.register(process_callback_delete_appointment,
                              lambda c: c.data.startswith('delete_appointment:'))
    dp.callback_query.register(process_callback_edit_appointment,
                              lambda c: c.data.startswith('edit_appointment:'))
    dp.callback_query.register(process_callback_users_list,
                              lambda c: c.data == 'users_list')

    # Общий обработчик отмены
    dp.callback_query.register(process_callback_cancel,
                              lambda c: c.data == 'cancel',
                              StateFilter('*'))

    # Обработчик имени пациента
    dp.message.register(process_patient_name,
                       StateFilter(AppointmentStates.waiting_for_patient_name))