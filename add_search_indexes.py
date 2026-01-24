#!/usr/bin/env python3
"""
Скрипт для добавления индексов для оптимизации поиска по содержимому сообщений и постов
"""

import sqlite3

DATABASE = 'database.db'

def add_search_indexes():
    """
    Добавляет индексы для оптимизации поиска по содержимому сообщений и постов
    """
    print("Добавление индексов для поиска...")
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Индекс для поиска по содержимому личных сообщений
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_content ON messages(message)")
            print("[OK] Index for private messages content created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating index for private messages: {e}")
        
        # Индекс для поиска по содержимому сообщений в группах
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_content ON group_messages(message)")
            print("[OK] Index for group messages content created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating index for group messages: {e}")
            
        # Индекс для поиска по содержимому сообщений в каналах
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_messages_content ON channel_messages(message)")
            print("[OK] Index for channel messages content created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating index for channel messages: {e}")
            
        # Индекс для поиска по содержимому постов
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_content ON posts(content)")
            print("[OK] Index for posts content created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating index for posts: {e}")
            
        # Комбинированные индексы для более эффективного поиска
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_content_sender ON messages(message, sender)")
            print("[OK] Combined index for private messages (content, sender) created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating combined index for private messages: {e}")
            
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_content_sender ON group_messages(message, sender)")
            print("[OK] Combined index for group messages (content, sender) created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating combined index for group messages: {e}")
            
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_messages_content_sender ON channel_messages(message, sender)")
            print("[OK] Combined index for channel messages (content, sender) created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating combined index for channel messages: {e}")
            
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_content_user ON posts(content, user_id)")
            print("[OK] Combined index for posts (content, user) created")
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating combined index for posts: {e}")
        
        conn.commit()
        print("\nAll search indexes added successfully!")

if __name__ == "__main__":
    add_search_indexes()