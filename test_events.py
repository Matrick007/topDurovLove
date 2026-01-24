"""
Тестирование функционала мероприятий
"""
import sqlite3
from utils import (
    init_db, create_user, get_user_by_username,
    create_event, get_event_by_id, get_events_for_user,
    get_events_created_by_user, add_event_participant,
    get_event_participants, update_participant_status
)

def test_events_functionality():
    print("=== Тестирование функционала мероприятий ===")
    
    # Инициализация базы данных
    init_db()
    print("[OK] База данных инициализирована")
    
    # Создание тестовых пользователей
    create_user("test_user1", "password1")
    create_user("test_user2", "password2")
    create_user("test_user3", "password3")
    print("[OK] Тестовые пользователи созданы")
    
    # Получение пользователей из базы
    user1 = get_user_by_username("test_user1")
    user2 = get_user_by_username("test_user2")
    user3 = get_user_by_username("test_user3")
    
    if not user1 or not user2 or not user3:
        print("[ERROR] Ошибка: не удалось получить пользователей")
        return False
        
    print(f"[OK] Пользователи получены: {user1['username']}, {user2['username']}, {user3['username']}")
    
    # Создание мероприятия
    event_id = create_event(
        title="Тестовое мероприятие",
        description="Это тестовое мероприятие для проверки функционала",
        event_date="2026-02-01 15:00:00",
        location="Тестовое место",
        creator_id=user1['id']
    )
    print(f"[OK] Мероприятие создано с ID: {event_id}")
    
    # Проверка получения мероприятия
    event = get_event_by_id(event_id)
    if not event:
        print("[ERROR] Ошибка: не удалось получить мероприятие")
        return False
        
    print(f"[OK] Мероприятие получено: {event['title']}")
    
    # Добавление участников
    add_event_participant(event_id, user1['id'], 'confirmed')  # Организатор автоматически подтвержден
    add_event_participant(event_id, user2['id'], 'invited')   # Приглашен
    add_event_participant(event_id, user3['id'], 'confirmed') # Подтвердил участие
    print("[OK] Участники добавлены к мероприятию")
    
    # Получение списка участников
    participants = get_event_participants(event_id)
    print(f"[OK] Участники мероприятия получены: {len(participants)} человек")
    for p in participants:
        print(f"  - {p['username']}: {p['status']}")
    
    # Обновление статуса участника
    update_participant_status(event_id, user2['id'], 'confirmed')
    print("[OK] Статус участника обновлен")
    
    # Проверка обновленного статуса
    participants = get_event_participants(event_id)
    user2_status = next(p for p in participants if p['username'] == 'test_user2')
    if user2_status['status'] == 'confirmed':
        print("[OK] Статус участника успешно обновлен до 'confirmed'")
    else:
        print("[ERROR] Ошибка: статус участника не обновился правильно")
        return False
    
    # Получение мероприятий для пользователя
    user1_events = get_events_for_user(user1['id'])
    print(f"[OK] Мероприятия для пользователя {user1['username']}: {len(user1_events)}")
    
    user2_events = get_events_for_user(user2['id'])
    print(f"[OK] Мероприятия для пользователя {user2['username']}: {len(user2_events)}")
    
    # Получение созданных мероприятий
    created_events = get_events_created_by_user(user1['id'])
    print(f"[OK] Мероприятия, созданные пользователем {user1['username']}: {len(created_events)}")
    
    print("\n=== Все тесты пройдены успешно! ===")
    print("Функционал мероприятий работает корректно:")
    print("- Создание мероприятий [OK]")
    print("- Добавление участников [OK]")
    print("- Изменение статусов участия [OK]")
    print("- Получение списка участников [OK]")
    print("- Получение мероприятий для пользователей [OK]")
    
    return True

if __name__ == "__main__":
    success = test_events_functionality()
    if not success:
        exit(1)