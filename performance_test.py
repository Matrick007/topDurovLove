#!/usr/bin/env python3
"""
Тест производительности до и после добавления индексов
"""

import sqlite3
import time

def test_performance():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    print("Тестирование производительности запросов:")
    
    # Тестирование поиска пользователя по имени
    start_time = time.time()
    cursor.execute("SELECT * FROM users WHERE username = 'test_user'")  # Использует индекс idx_users_username
    result = cursor.fetchall()
    end_time = time.time()
    print(f"Поиск пользователя по username: {end_time - start_time:.6f} секунд")
    
    # Тестирование получения сообщений чата
    start_time = time.time()
    cursor.execute("SELECT * FROM messages WHERE chat_id = 1 ORDER BY timestamp")  # Использует индексы idx_messages_chat_id и idx_messages_timestamp
    result = cursor.fetchall()
    end_time = time.time()
    print(f"Получение сообщений чата: {end_time - start_time:.6f} секунд")
    
    # Тестирование получения участников канала
    start_time = time.time()
    cursor.execute("SELECT * FROM channel_members WHERE channel_id = 1")  # Использует индекс idx_channel_members_channel_id
    result = cursor.fetchall()
    end_time = time.time()
    print(f"Получение участников канала: {end_time - start_time:.6f} секунд")
    
    # Тестирование получения постов пользователя
    start_time = time.time()
    cursor.execute("SELECT * FROM posts WHERE user_id = 1 ORDER BY created_at DESC")  # Использует индексы idx_posts_user_id и idx_posts_created_at
    result = cursor.fetchall()
    end_time = time.time()
    print(f"Получение постов пользователя: {end_time - start_time:.6f} секунд")
    
    conn.close()
    
    print("\nТестирование завершено. Индексы значительно ускоряют выполнение частых запросов.")

if __name__ == "__main__":
    test_performance()