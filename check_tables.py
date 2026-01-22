#!/usr/bin/env python3
# check_tables.py
# Скрипт для проверки существования таблиц в базе данных

import sqlite3

DATABASE = 'database.db'

def check_tables():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Существующие таблицы:")
        for table in tables:
            print(f"- {table[0]}")

        # Проверим конкретные таблицы
        required_tables = ['channels', 'channel_members', 'channel_invites', 'channel_roles']
        print("\nПроверка новых таблиц:")
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if cursor.fetchone():
                print(f"[OK] Таблица {table} существует")
            else:
                print(f"[ERROR] Таблица {table} НЕ существует")

if __name__ == '__main__':
    check_tables()