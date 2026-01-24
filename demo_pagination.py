#!/usr/bin/env python3
"""
Демонстрация работы пагинации
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = 'http://localhost:5000'

def demo_pagination():
    """
    Демонстрируем работу пагинации
    """
    print("Демонстрация работы пагинации...")
    
    # Создаем сессию для сохранения cookie
    session = requests.Session()
    
    # Регистрируем тестового пользователя
    print("\n1. Регистрация тестового пользователя...")
    register_data = {
        'username': 'test_pagination_user',
        'password': 'testpass123'
    }
    try:
        response = session.post(f"{BASE_URL}/register", data=register_data)
        print(f"   Регистрация статус: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка регистрации: {e}")
    
    # Логинимся
    print("\n2. Вход в систему...")
    login_data = {
        'username': 'test_pagination_user',
        'password': 'testpass123'
    }
    try:
        response = session.post(f"{BASE_URL}/login", data=login_data)
        print(f"   Вход статус: {response.status_code}")
        if response.status_code == 200:
            print("   Успешно вошли в систему")
        else:
            print("   Ошибка входа")
            return
    except Exception as e:
        print(f"   Ошибка входа: {e}")
        return
    
    # Создадим несколько тестовых постов
    print("\n3. Создание тестовых постов...")
    for i in range(15):  # Создадим 15 тестовых постов
        post_data = {
            'content': f'Тестовый пост #{i+1} для проверки пагинации'
        }
        try:
            response = session.post(f"{BASE_URL}/create_post", data=post_data)
            if response.status_code == 200:
                print(f"   Пост #{i+1} создан", end="")
                if i % 5 == 4:  # Раз в 5 постов
                    print("")  # Новая строка
                else:
                    print(", ", end="", flush=True)
            else:
                print(f"   Ошибка создания поста #{i+1}")
        except Exception as e:
            print(f"   Ошибка создания поста #{i+1}: {e}")
    
    print("\n\n4. Проверка пагинации для ленты постов...")
    
    # Проверим первую страницу (по умолчанию 10 постов)
    try:
        response = session.get(f"{BASE_URL}/feed_data?page=1&per_page=5")
        print(f"   Запрос первой страницы (5 постов) - статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            posts = data.get('feed', [])
            print(f"   Количество постов на странице 1: {len(posts)}")
            if posts:
                print(f"   Первый пост: {posts[0]['content']}")
                print(f"   Последний пост на странице: {posts[-1]['content']}")
    except Exception as e:
        print(f"   Ошибка при запросе первой страницы: {e}")
    
    # Проверим вторую страницу
    try:
        response = session.get(f"{BASE_URL}/feed_data?page=2&per_page=5")
        print(f"   Запрос второй страницы (5 постов) - статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            posts = data.get('feed', [])
            print(f"   Количество постов на странице 2: {len(posts)}")
            if posts:
                print(f"   Первый пост на странице 2: {posts[0]['content']}")
                print(f"   Последний пост на странице 2: {posts[-1]['content']}")
    except Exception as e:
        print(f"   Ошибка при запросе второй страницы: {e}")
    
    # Проверим третью страницу
    try:
        response = session.get(f"{BASE_URL}/feed_data?page=3&per_page=5")
        print(f"   Запрос третьей страницы (5 постов) - статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            posts = data.get('feed', [])
            print(f"   Количество постов на странице 3: {len(posts)}")
            if posts:
                print(f"   Первый пост на странице 3: {posts[0]['content']}")
                print(f"   Последний пост на странице 3: {posts[-1]['content']}")
    except Exception as e:
        print(f"   Ошибка при запросе третьей страницы: {e}")
    
    print("\n5. Проверка пагинации с разным количеством элементов на странице...")
    
    # Проверим разное количество элементов на странице
    for per_page in [3, 7, 10]:
        try:
            response = session.get(f"{BASE_URL}/feed_data?page=1&per_page={per_page}")
            print(f"   Запрос с per_page={per_page} - статус: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                posts = data.get('feed', [])
                print(f"     Количество постов: {len(posts)} (ожидается не более {per_page})")
        except Exception as e:
            print(f"   Ошибка при запросе с per_page={per_page}: {e}")
    
    print("\nДемонстрация пагинации завершена.")
    print("\nДля полной проверки откройте приложение в браузере по адресу http://localhost:5000")
    print("и убедитесь, что пагинация работает в интерфейсе (лента постов, сообщения в чатах и т.д.)")

if __name__ == "__main__":
    demo_pagination()