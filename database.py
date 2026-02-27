import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, filename='appointments.json'):
        self.filename = filename
        self.load_data()

    def load_data(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                'appointments': [],
                'users': {},
                'next_id': 1
            }
            self.save_data()

    def save_data(self):
        """Сохранение данных в файл"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавление нового пользователя"""
        if str(user_id) not in self.data['users']:
            self.data['users'][str(user_id)] = {
                'username': username,
                'first_name': first_name,
                'registered_at': datetime.now().isoformat()
            }
            self.save_data()

    def create_appointment(self, user_id: int, patient_name: str,
                           doctor: str, procedure: str,
                           date: str, time: str) -> int:
        """Создание новой записи"""
        appointment_id = self.data['next_id']
        appointment = {
            'id': appointment_id,
            'user_id': user_id,
            'patient_name': patient_name,
            'doctor': doctor,
            'procedure': procedure,
            'date': date,
            'time': time,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        self.data['appointments'].append(appointment)
        self.data['next_id'] += 1
        self.save_data()
        return appointment_id

    def get_appointments(self, user_id: Optional[int] = None) -> List[Dict]:
        """Получение записей (всех или для конкретного пользователя)"""
        if user_id:
            return [a for a in self.data['appointments']
                    if a['user_id'] == user_id and a['status'] == 'active']
        return [a for a in self.data['appointments'] if a['status'] == 'active']

    def get_appointment(self, appointment_id: int) -> Optional[Dict]:
        """Получение конкретной записи"""
        for appointment in self.data['appointments']:
            if appointment['id'] == appointment_id:
                return appointment
        return None

    def update_appointment(self, appointment_id: int, **kwargs) -> bool:
        """Обновление записи"""
        for appointment in self.data['appointments']:
            if appointment['id'] == appointment_id:
                appointment.update(kwargs)
                self.save_data()
                return True
        return False

    def delete_appointment(self, appointment_id: int) -> bool:
        """Удаление записи"""
        return self.update_appointment(appointment_id, status='deleted')

    def get_users(self) -> Dict:
        """Получение всех пользователей"""
        return self.data['users']

    def is_appointment_available(self, doctor: str, date: str, time: str) -> bool:
        """Проверка доступности времени"""
        for appointment in self.data['appointments']:
            if (appointment['status'] == 'active' and
                    appointment['doctor'] == doctor and
                    appointment['date'] == date and
                    appointment['time'] == time):
                return False
        return True


# Создаем глобальный экземпляр базы данных
db = Database()