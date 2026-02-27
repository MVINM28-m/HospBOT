from datetime import datetime
from typing import Dict
import os


def format_appointment(appointment: Dict, is_admin: bool = False) -> str:
    """Форматирование информации о записи"""
    status_emoji = {
        'active': '✅',
        'deleted': '❌',
        'completed': '✔️'
    }.get(appointment['status'], '⏳')

    text = f"{status_emoji} Запись #{appointment['id']}\n\n"
    text += f"👤 Пациент: {appointment['patient_name']}\n"
    text += f"👨‍⚕️ Врач: {appointment['doctor']}\n"
    text += f"💉 Процедура: {appointment['procedure']}\n"
    text += f"📅 Дата: {appointment['date']}\n"
    text += f"⏰ Время: {appointment['time']}\n"

    if is_admin:
        text += f"🆔 ID пользователя: {appointment['user_id']}\n"
        text += f"📝 Статус: {appointment['status']}\n"
        text += f"📅 Создано: {appointment['created_at'][:16]}\n"

    return text


def generate_calendar_event(appointment: Dict) -> str:
    """Генерация файла для календаря (.ics)"""
    try:
        date_str = f"{appointment['date']} {appointment['time']}"
        event_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")

        # Форматируем дату для .ics
        start_time = event_date.strftime("%Y%m%dT%H%M%S")
        end_time = event_date.replace(hour=event_date.hour + 1).strftime("%Y%m%dT%H%M%S")

        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Clinic Bot//EN
BEGIN:VEVENT
UID:{appointment['id']}@clinicbot
DTSTART:{start_time}
DTEND:{end_time}
SUMMARY:Прием у {appointment['doctor']}
DESCRIPTION:Пациент: {appointment['patient_name']}\\nПроцедура: {appointment['procedure']}
LOCATION:Клиника «Здоровье»
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

        filename = f"appointment_{appointment['id']}.ics"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(ics_content)

        return filename
    except Exception as e:
        print(f"Ошибка создания календаря: {e}")
        return None


def cleanup_temp_files():
    """Очистка временных файлов"""
    for file in os.listdir('.'):
        if file.startswith('appointment_') and file.endswith('.ics'):
            try:
                os.remove(file)
            except:
                pass