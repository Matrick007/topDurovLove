#!/usr/bin/env python3
# update_channels.py
# Скрипт для обновления старых каналов: добавление creator в channel_members с ролью Admin

import sys
import os

# Добавляем текущую директорию в путь для импорта utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_db_connection

def update_old_channels():
    with get_db_connection() as conn:
        # Получить все каналы
        channels = conn.execute("SELECT id, name, creator FROM channels").fetchall()
        for channel in channels:
            channel_id = channel['id']
            creator_username = channel['creator']
            # Найти user_id создателя
            user = conn.execute("SELECT id FROM users WHERE username = ?", (creator_username,)).fetchone()
            if not user:
                print(f"Creator {creator_username} not found for channel {channel['name']}")
                continue
            creator_id = user['id']
            # Проверить, есть ли creator в channel_members
            member = conn.execute("SELECT 1 FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel_id, creator_id)).fetchone()
            if member:
                print(f"Creator already in channel_members for {channel['name']}")
                continue
            # Найти или создать роль Admin
            role = conn.execute("SELECT id FROM channel_roles WHERE channel_id = ? AND role_name = 'Admin'", (channel_id,)).fetchone()
            if not role:
                # Создать роль Admin
                cursor = conn.cursor()
                cursor.execute("INSERT INTO channel_roles (channel_id, role_name, permissions) VALUES (?, 'Admin', 'read,write,manage_members,manage_roles,manage_invites')", (channel_id,))
                role_id = cursor.lastrowid
                print(f"Created Admin role for channel {channel['name']}")
            else:
                role_id = role['id']
            # Добавить creator в channel_members
            conn.execute("INSERT INTO channel_members (channel_id, user_id, role_id) VALUES (?, ?, ?)", (channel_id, creator_id, role_id))
            print(f"Added creator to channel_members for {channel['name']}")
        conn.commit()

if __name__ == '__main__':
    print("Updating old channels...")
    update_old_channels()
    print("Done.")