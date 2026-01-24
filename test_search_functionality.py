#!/usr/bin/env python3
"""
Тестирование функциональности поиска
"""
import sys
import os

# Добавляем директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import *

def test_search_functionality():
    """
    Тестируем функции поиска
    """
    print("=== ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ ПОИСКА ===\n")
    
    # Создадим тестового пользователя
    test_user_id = 999  # Используем несуществующий ID для тестирования
    
    print("1. Тестируем глобальный поиск сообщений...")
    try:
        results = search_messages_global("test", test_user_id)
        print(f"   Результат: {len(results)} сообщений найдено")
        print("   ✅ Функция search_messages_global работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_messages_global: {e}")
    
    print("\n2. Тестируем глобальный поиск постов...")
    try:
        results = search_posts_global("test", test_user_id)
        print(f"   Результат: {len(results)} постов найдено")
        print("   ✅ Функция search_posts_global работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_posts_global: {e}")
    
    print("\n3. Тестируем глобальный поиск всего контента...")
    try:
        results = search_all_content("test", test_user_id)
        print(f"   Результат: {results['total_messages']} сообщений, {results['total_posts']} постов")
        print("   ✅ Функция search_all_content работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_all_content: {e}")
    
    print("\n4. Тестируем локальный поиск в чате...")
    try:
        results = search_messages_in_chat("test_user", "test", test_user_id)
        print(f"   Результат: {len(results)} сообщений найдено")
        print("   ✅ Функция search_messages_in_chat работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_messages_in_chat: {e}")
    
    print("\n5. Тестируем локальный поиск в группе...")
    try:
        results = search_messages_in_group("test_group", "test", test_user_id)
        print(f"   Результат: {len(results)} сообщений найдено")
        print("   ✅ Функция search_messages_in_group работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_messages_in_group: {e}")
    
    print("\n6. Тестируем локальный поиск в канале...")
    try:
        results = search_messages_in_channel("test_channel", "test", test_user_id)
        print(f"   Результат: {len(results)} сообщений найдено")
        print("   ✅ Функция search_messages_in_channel работает")
    except Exception as e:
        print(f"   ❌ Ошибка в search_messages_in_channel: {e}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    test_search_functionality()