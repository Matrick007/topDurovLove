#!/usr/bin/env python3
"""
Проверка API-маршрутов поиска
"""
import requests
import json

def test_search_endpoints():
    """
    Тестируем API-эндпоинты поиска
    """
    print("=== ПРОВЕРКА API-МАРШРУТОВ ПОИСКА ===\n")
    
    # Базовый URL (предполагаем, что приложение запущено на localhost:5000)
    base_url = "http://localhost:5000"
    
    # Тестирование эндпоинтов (без авторизации, так как они требуют сессию)
    endpoints = [
        "/search?q=test",
        "/advanced_search?q=test",
        "/advanced_search?q=test&type=messages",
        "/advanced_search?q=test&type=posts",
        "/advanced_search?q=test&type=all",
        "/search_in_chat/test_user?q=test",
        "/search_in_group/test_group?q=test",
        "/search_in_channel/test_channel?q=test"
    ]
    
    print("Доступные эндпоинты поиска:")
    for endpoint in endpoints:
        print(f"  - {endpoint}")
    
    print("\nДля полного тестирования необходимо запустить приложение:")
    print("  flask run или python app.py")
    print("и затем выполнить реальные HTTP-запросы.")
    
    print("\n=== ПРОВЕРКА ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    test_search_endpoints()