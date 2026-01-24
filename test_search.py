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
    print("=== TESTING SEARCH FUNCTIONALITY ===\n")
    
    # Создадим тестового пользователя
    test_user_id = 999  # Используем несуществующий ID для тестирования
    
    print("1. Testing global message search...")
    try:
        results = search_messages_global("test", test_user_id)
        print(f"   Result: {len(results)} messages found")
        print("   [OK] search_messages_global function works")
    except Exception as e:
        print(f"   [ERROR] search_messages_global error: {e}")
    
    print("\n2. Testing global post search...")
    try:
        results = search_posts_global("test", test_user_id)
        print(f"   Result: {len(results)} posts found")
        print("   [OK] search_posts_global function works")
    except Exception as e:
        print(f"   [ERROR] search_posts_global error: {e}")
    
    print("\n3. Testing global content search...")
    try:
        results = search_all_content("test", test_user_id)
        print(f"   Result: {results['total_messages']} messages, {results['total_posts']} posts")
        print("   [OK] search_all_content function works")
    except Exception as e:
        print(f"   [ERROR] search_all_content error: {e}")
    
    print("\n4. Testing local chat message search...")
    try:
        results = search_messages_in_chat("test_user", "test", test_user_id)
        print(f"   Result: {len(results)} messages found")
        print("   [OK] search_messages_in_chat function works")
    except Exception as e:
        print(f"   [ERROR] search_messages_in_chat error: {e}")
    
    print("\n5. Testing local group message search...")
    try:
        results = search_messages_in_group("test_group", "test", test_user_id)
        print(f"   Result: {len(results)} messages found")
        print("   [OK] search_messages_in_group function works")
    except Exception as e:
        print(f"   [ERROR] search_messages_in_group error: {e}")
    
    print("\n6. Testing local channel message search...")
    try:
        results = search_messages_in_channel("test_channel", "test", test_user_id)
        print(f"   Result: {len(results)} messages found")
        print("   [OK] search_messages_in_channel function works")
    except Exception as e:
        print(f"   [ERROR] search_messages_in_channel error: {e}")
    
    print("\n=== TESTING COMPLETED ===")

if __name__ == "__main__":
    test_search_functionality()