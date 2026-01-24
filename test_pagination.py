#!/usr/bin/env python3
"""
Тестирование функционала пагинации
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = 'http://localhost:5000'

def test_pagination():
    """
    Тестируем пагинацию для различных маршрутов
    """
    print("Тестирование пагинации...")
    
    # Проверим пагинацию для личных сообщений
    print("\n1. Тестирование пагинации для личных сообщений:")
    try:
        # Сначала нужно залогиниться (в реальном тесте нужно будет выполнить аутентификацию)
        # Для тестирования предположим, что у нас есть сессия
        response = requests.get(f"{BASE_URL}/chat/test1/history?page=1&per_page=10")
        print(f"   Статус ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Количество сообщений: {len(data.get('messages', []))}")
            print(f"   Есть ли чат ID: {'chat_id' in data}")
    except Exception as e:
        print(f"   Ошибка при тестировании личных сообщений: {e}")
    
    # Проверим пагинацию для групповых сообщений
    print("\n2. Тестирование пагинации для групповых сообщений:")
    try:
        response = requests.get(f"{BASE_URL}/group/test_group/history?page=1&per_page=10")
        print(f"   Статус ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Количество сообщений: {len(data.get('messages', []))}")
            print(f"   Есть ли группа ID: {'group_id' in data}")
    except Exception as e:
        print(f"   Ошибка при тестировании групповых сообщений: {e}")
    
    # Проверим пагинацию для каналов
    print("\n3. Тестирование пагинации для каналов:")
    try:
        response = requests.get(f"{BASE_URL}/channel/test_channel/history?page=1&per_page=10")
        print(f"   Статус ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Количество сообщений: {len(data.get('messages', []))}")
            print(f"   Есть ли канал ID: {'channel_id' in data}")
    except Exception as e:
        print(f"   Ошибка при тестировании каналов: {e}")
    
    # Проверим пагинацию для ленты
    print("\n4. Тестирование пагинации для ленты:")
    try:
        response = requests.get(f"{BASE_URL}/feed_data?page=1&per_page=5")
        print(f"   Статус ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Количество постов: {len(data.get('feed', []))}")
            if data.get('feed'):
                print(f"   Первый пост ID: {data['feed'][0].get('id')}")
    except Exception as e:
        print(f"   Ошибка при тестировании ленты: {e}")

    print("\nТестирование завершено.")

if __name__ == "__main__":
    test_pagination()