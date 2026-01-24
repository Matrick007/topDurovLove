#!/usr/bin/env python3
"""
Скрипт для добавления индексов в базу данных SQLite
"""

import sqlite3

def add_indexes_to_database(db_path='database.db'):
    """
    Функция для добавления индексов в базу данных
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Индексы для таблицы users
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    
    # Индексы для таблицы chats
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_user1_id ON chats(user1_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_user2_id ON chats(user2_id)")
    
    # Индексы для таблицы messages
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
    
    # Индексы для таблицы channels
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(name)")
    
    # Индексы для таблицы channel_members
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_members_channel_id ON channel_members(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_members_user_id ON channel_members(user_id)")
    
    # Индексы для таблицы groups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name)")
    
    # Индексы для таблицы group_members
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id)")
    
    # Индексы для таблицы posts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)")
    
    # Индексы для таблицы likes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id)")
    
    # Индексы для таблицы comments
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
    
    # Индексы для таблицы subscriptions
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_follower_id ON subscriptions(follower_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_following_id ON subscriptions(following_id)")
    
    # Индексы для таблицы group_messages
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_group_id ON group_messages(group_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_sender ON group_messages(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_timestamp ON group_messages(timestamp)")
    
    # Индексы для таблицы channel_messages
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_messages_channel_id ON channel_messages(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_messages_sender ON channel_messages(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_messages_timestamp ON channel_messages(timestamp)")
    
    # Индексы для таблицы user_sessions
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_logout_time ON user_sessions(logout_time)")
    
    # Индексы для таблицы channel_invites
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_invites_channel_id ON channel_invites(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_invites_invite_code ON channel_invites(invite_code)")
    
    # Индексы для таблицы channel_roles
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_roles_channel_id ON channel_roles(channel_id)")

    conn.commit()
    conn.close()
    
    print("Все индексы успешно добавлены в базу данных!")

if __name__ == "__main__":
    add_indexes_to_database()