from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from config import DOCTORS, AVAILABLE_TIMES, PROCEDURES


def get_main_keyboard(is_admin: bool = False):
    """Основная клавиатура с инлайн кнопками (минимум 4 кнопки)"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton("📅 Записаться", callback_data="make_appointment"),
        InlineKeyboardButton("📋 Мои записи", callback_data="my_appointments"),
        InlineKeyboardButton("👨‍⚕️ Врачи", callback_data="doctors_list"),
        InlineKeyboardButton("ℹ️ О клинике", callback_data="about"),
    ]

    # Дополнительные кнопки для администратора
    if is_admin:
        buttons.extend([
            InlineKeyboardButton("📊 Все записи", callback_data="all_appointments"),
            InlineKeyboardButton("👥 Пользователи", callback_data="users_list"),
        ])

    keyboard.add(*buttons)
    return keyboard


def get_doctors_keyboard():
    """Клавиатура с врачами"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for doctor in DOCTORS:
        keyboard.add(InlineKeyboardButton(
            doctor,
            callback_data=f"select_doctor:{doctor}"
        ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return keyboard


def get_procedures_keyboard(doctor: str):
    """Клавиатура с процедурами для выбранного врача"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Получаем первую часть названия врача для поиска в PROCEDURES
    doctor_key = doctor.split()[0].lower()
    procedures = PROCEDURES.get(doctor_key, ["Консультация"])

    for procedure in procedures:
        keyboard.add(InlineKeyboardButton(
            procedure,
            callback_data=f"select_procedure:{procedure}"
        ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="select_doctor"))
    return keyboard


def get_dates_keyboard():
    """Клавиатура с датами на ближайшие 7 дней"""
    keyboard = InlineKeyboardMarkup(row_width=3)

    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        day_name = date.strftime("%A")[:3]

        keyboard.insert(InlineKeyboardButton(
            f"{date_str} ({day_name})",
            callback_data=f"select_date:{date_str}"
        ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="select_doctor"))
    return keyboard


def get_times_keyboard():
    """Клавиатура с доступным временем"""
    keyboard = InlineKeyboardMarkup(row_width=3)

    for time in AVAILABLE_TIMES:
        keyboard.insert(InlineKeyboardButton(
            time,
            callback_data=f"select_time:{time}"
        ))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="select_date"))
    return keyboard


def get_appointments_keyboard(appointments: list, is_admin: bool = False):
    """Клавиатура со списком записей"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for apt in appointments:
        text = f"{apt['date']} {apt['time']} - {apt['doctor']}"
        if is_admin:
            callback = f"admin_view:{apt['id']}"
        else:
            callback = f"view_appointment:{apt['id']}"
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))

    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return keyboard


def get_appointment_actions_keyboard(appointment_id: int, is_admin: bool = False):
    """Клавиатура действий для конкретной записи"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    if is_admin:
        buttons = [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_appointment:{appointment_id}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"delete_appointment:{appointment_id}"),
            InlineKeyboardButton("📅 В календарь", callback_data=f"add_to_calendar:{appointment_id}"),
            InlineKeyboardButton("◀️ Назад", callback_data="all_appointments"),
        ]
    else:
        buttons = [
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_appointment:{appointment_id}"),
            InlineKeyboardButton("📅 В календарь", callback_data=f"add_to_calendar:{appointment_id}"),
            InlineKeyboardButton("◀️ Назад", callback_data="my_appointments"),
        ]

    keyboard.add(*buttons)
    return keyboard


def get_admin_edit_keyboard(appointment_id: int):
    """Клавиатура для редактирования записи (админ)"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton("👤 Имя пациента", callback_data=f"edit_patient_name:{appointment_id}"),
        InlineKeyboardButton("👨‍⚕️ Врача", callback_data=f"edit_doctor:{appointment_id}"),
        InlineKeyboardButton("💉 Процедуру", callback_data=f"edit_procedure:{appointment_id}"),
        InlineKeyboardButton("📅 Дату", callback_data=f"edit_date:{appointment_id}"),
        InlineKeyboardButton("⏰ Время", callback_data=f"edit_time:{appointment_id}"),
        InlineKeyboardButton("◀️ Назад", callback_data=f"view_appointment:{appointment_id}"),
    ]

    keyboard.add(*buttons)
    return keyboard


def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return keyboard


def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard