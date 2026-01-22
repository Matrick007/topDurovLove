#!/usr/bin/env python3
# delete_channels.py
# Скрипт для удаления всех каналов из базы данных

import sys
import os

# Добавляем текущую директорию в путь для импорта utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_db_connection

def delete_all_channels():
    with get_db_connection() as conn:
        # Удалить все инвайты каналов
        conn.execute("DELETE FROM channel_invites")
        # Удалить все роли каналов
        conn.execute("DELETE FROM channel_roles")
        # Удалить всех участников каналов
        conn.execute("DELETE FROM channel_members")
        # Удалить все каналы
        conn.execute("DELETE FROM channels")
        conn.commit()
        print("Все каналы удалены из базы данных.")

if __name__ == '__main__':
    print("Удаление всех каналов...")
    delete_all_channels()
    print("Готово.")