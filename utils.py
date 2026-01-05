# utils.py (обновлённый)
import sqlite3
import hashlib
from contextlib import contextmanager

DATABASE = 'database.db'

def init_db():
    print("init_db called")
    with get_db_connection() as conn:
        # === Таблица пользователей ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                city TEXT,
                bio_short TEXT,
                country TEXT,
                languages TEXT,
                bio_full TEXT,
                hobbies TEXT,
                avatar TEXT,
                status TEXT
            )
        """)

        # === Таблица чатов ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                UNIQUE(user1_id, user2_id)
            )
        """)

        # === Таблица личных сообщений ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent'  -- sent, delivered, read
            )
        """)

        # === ГРУППЫ ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                creator TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                pinned_msg_id INTEGER
            )
        """)

        # === Участники групп ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(group_id, user_id)
            )
        """)

        # === Сообщения в группах ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        """)

        # Добавить тестовых пользователей
        conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('test1', hash_password('pass1')))
        conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('test2', hash_password('pass2')))
        conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('user1', hash_password('pass1')))
        conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('user2', hash_password('pass2')))

        # === Подписки ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER,
                following_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(follower_id, following_id),
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (following_id) REFERENCES users (id)
            )
        """)

        # === Посты ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT NOT NULL,
                image_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # === Лайки ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """)

        # === Комментарии ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """)

        # === Репосты ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reposts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_post_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, original_post_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (original_post_id) REFERENCES posts (id)
            )
        """)

        # === Сессии пользователей ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                logout_time DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()

        # Добавить колонки если не существуют
        try:
            conn.execute("ALTER TABLE groups ADD COLUMN pinned_msg_id INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Колонка уже существует

        try:
            conn.execute("ALTER TABLE users ADD COLUMN registration_date DATETIME DEFAULT CURRENT_TIMESTAMP")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN city TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN bio_short TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN country TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN languages TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN bio_full TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN hobbies TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN status TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Обновить usernames на lower
        conn.execute("UPDATE users SET username = LOWER(username)")
        conn.commit()
        print("Updated usernames to lower")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_user_by_username(username):
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower(),)).fetchone()
    print(f"get_user_by_username({username}) -> {dict(user) if user else None}")
    return user

def create_user(username, password, city='', bio_short=''):
    hashed = hash_password(password)
    with get_db_connection() as conn:
        conn.execute('INSERT INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)', (username, hashed, city, bio_short))
        conn.commit()

def get_active_users(exclude_user_id=None):
    query = "SELECT id, username FROM users"
    params = ()
    if exclude_user_id:
        query += " WHERE id != ?"
        params = (exclude_user_id,)
    with get_db_connection() as conn:
        users = conn.execute(query, params).fetchall()
    return users


def get_user_chats(user_id):
    with get_db_connection() as conn:
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        my_username = user['username']
        chats = conn.execute('''
            SELECT DISTINCT u.username, u.id,
                (SELECT m.message FROM messages m WHERE m.chat_id = c.id ORDER BY m.timestamp DESC LIMIT 1) as last_message,
                (SELECT m.timestamp FROM messages m WHERE m.chat_id = c.id ORDER BY m.timestamp DESC LIMIT 1) as last_time,
                (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id AND m.sender != ? AND m.status != 'read') as unread_count
            FROM users u
            JOIN chats c ON (c.user1_id = u.id OR c.user2_id = u.id)
            WHERE (c.user1_id = ? OR c.user2_id = ?) AND u.id != ?
            AND EXISTS (SELECT 1 FROM messages m WHERE m.chat_id = c.id)
        ''', (my_username, user_id, user_id, user_id)).fetchall()
    return [dict(chat) for chat in chats]

def get_or_create_chat(user1_id, user2_id):
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id
    with get_db_connection() as conn:
        chat = conn.execute(
            'SELECT id FROM chats WHERE user1_id = ? AND user2_id = ?',
            (user1_id, user2_id)
        ).fetchone()
        if chat:
            return chat['id']
        conn.execute(
            'INSERT INTO chats (user1_id, user2_id) VALUES (?, ?)',
            (user1_id, user2_id)
        )
        conn.commit()
        return conn.execute('SELECT last_insert_rowid() AS id').fetchone()['id']

def get_messages(chat_id):
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT id, sender, message, timestamp, status FROM messages
            WHERE chat_id = ? ORDER BY timestamp
        """, (chat_id,)).fetchall()
    print(f"Getting messages for chat {chat_id}: {len(messages)} messages")
    return [dict(m) for m in messages]

def save_message(chat_id, sender, message):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (chat_id, sender, message)
            VALUES (?, ?, ?)
        """, (chat_id, sender, message))
        conn.commit()
        return cursor.lastrowid

def mark_message_as_delivered(msg_id):
    with get_db_connection() as conn:
        conn.execute('UPDATE messages SET status = "delivered" WHERE id = ?', (msg_id,))
        conn.commit()

def mark_message_as_read(msg_id):
    with get_db_connection() as conn:
        conn.execute('UPDATE messages SET status = "read" WHERE id = ?', (msg_id,))
        conn.commit()

def get_unread_messages(recipient_username, sender_username):
    with get_db_connection() as conn:
        return [
            dict(row) for row in conn.execute('''
                SELECT m.id, m.sender FROM messages m
                JOIN chats c ON m.chat_id = c.id
                JOIN users u1 ON c.user1_id = u1.id
                JOIN users u2 ON c.user2_id = u2.id
                WHERE m.status != 'read'
                  AND m.sender = ?
                  AND (u1.username = ? OR u2.username = ?)
            ''', (sender_username, recipient_username, recipient_username)).fetchall()
        ]




def create_group(name, creator):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (name, creator) VALUES (?, ?)", (name, creator))
        conn.commit()
        return cursor.lastrowid


def get_group_by_name(name):
    with get_db_connection() as conn:
        group = conn.execute("SELECT * FROM groups WHERE name = ?", (name,)).fetchone()
        return group


def get_groups_for_user(user_id):
    with get_db_connection() as conn:
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        my_username = user['username']
        groups = conn.execute("""
            SELECT g.name,
                (SELECT gm2.message FROM group_messages gm2 WHERE gm2.group_id = g.id ORDER BY gm2.timestamp DESC LIMIT 1) as last_message,
                (SELECT gm2.timestamp FROM group_messages gm2 WHERE gm2.group_id = g.id ORDER BY gm2.timestamp DESC LIMIT 1) as last_time,
                (SELECT COUNT(*) FROM group_messages gm2 WHERE gm2.group_id = g.id AND gm2.sender != ? AND gm2.is_read = 0) as unread_count
            FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = ?
        """, (my_username, user_id)).fetchall()
    return [dict(g) for g in groups]


def add_user_to_group(group_id, user_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()


def get_group_messages(group_id):
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT id, sender, message, timestamp, is_read FROM group_messages
            WHERE group_id = ?
            ORDER BY timestamp
        """, (group_id,)).fetchall()
        return [dict(m) for m in messages]


def save_group_message(group_id, sender, message, is_read=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender, message, is_read)
            VALUES (?, ?, ?, ?)
        """, (group_id, sender, message, is_read))
        conn.commit()
        return cursor.lastrowid


def update_group_message_read(msg_id, is_read=True):
    with get_db_connection() as conn:
        conn.execute("UPDATE group_messages SET is_read = ? WHERE id = ?", (is_read, msg_id))
        conn.commit()



def delete_message(msg_id, is_group=False):
    table = 'group_messages' if is_group else 'messages'
    with get_db_connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (msg_id,))
        conn.commit()


def save_pinned_message(group_id, msg_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE groups SET pinned_msg_id = ? WHERE id = ?", (msg_id, group_id))
        conn.commit()


def get_pinned_message(group_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT pinned_msg_id FROM groups WHERE id = ?", (group_id,)).fetchone()
        if row and row['pinned_msg_id']:
            msg = conn.execute("SELECT * FROM group_messages WHERE id = ?", (row['pinned_msg_id'],)).fetchone()
            return dict(msg) if msg else None
        return None


def remove_pinned_message(group_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE groups SET pinned_msg_id = NULL WHERE id = ?", (group_id,))
        conn.commit()


# === Социальная сеть ===

def follow_user(follower_id, following_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO subscriptions (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
        conn.commit()


def unfollow_user(follower_id, following_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM subscriptions WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
        conn.commit()


def is_following(follower_id, following_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM subscriptions WHERE follower_id = ? AND following_id = ?", (follower_id, following_id)).fetchone() is not None


def get_followers(user_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("SELECT u.username FROM subscriptions s JOIN users u ON s.follower_id = u.id WHERE s.following_id = ?", (user_id,)).fetchall()]


def get_following(user_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("SELECT u.username FROM subscriptions s JOIN users u ON s.following_id = u.id WHERE s.follower_id = ?", (user_id,)).fetchall()]


def create_post(user_id, content, image_url=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (user_id, content, image_url) VALUES (?, ?, ?)", (user_id, content, image_url))
        conn.commit()
        return cursor.lastrowid


def get_posts_for_user(user_id):
    with get_db_connection() as conn:
        posts = conn.execute("""
            SELECT p.*, u.username,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                   (SELECT COUNT(*) FROM reposts WHERE original_post_id = p.id) as reposts_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        """, (user_id,)).fetchall()
        return [dict(post) for post in posts]


def get_feed(user_id):
    with get_db_connection() as conn:
        posts = conn.execute("""
            SELECT p.*, u.username,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                   (SELECT COUNT(*) FROM reposts WHERE original_post_id = p.id) as reposts_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id IN (SELECT following_id FROM subscriptions WHERE follower_id = ?) OR p.user_id = ?
            ORDER BY p.created_at DESC
        """, (user_id, user_id)).fetchall()
        return [dict(post) for post in posts]


def like_post(user_id, post_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()


def unlike_post(user_id, post_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.commit()


def is_liked(user_id, post_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone() is not None


def add_comment(user_id, post_id, content):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)", (user_id, post_id, content))
        conn.commit()
        return cursor.lastrowid


def get_comments_for_post(post_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT c.*, u.username FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        """, (post_id,)).fetchall()]


def repost(user_id, original_post_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO reposts (user_id, original_post_id) VALUES (?, ?)", (user_id, original_post_id))
        conn.commit()


def unrepost(user_id, original_post_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM reposts WHERE user_id = ? AND original_post_id = ?", (user_id, original_post_id))
        conn.commit()


def is_reposted(user_id, post_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM reposts WHERE user_id = ? AND original_post_id = ?", (user_id, post_id)).fetchone() is not None


def edit_post(post_id, user_id, content=None, image_url=None):
    with get_db_connection() as conn:
        # Проверить, что пост принадлежит пользователю
        post = conn.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post or post['user_id'] != user_id:
            raise ValueError("Пост не найден или нет доступа")

        # Обновить пост
        update_fields = []
        params = []
        if content is not None:
            update_fields.append("content = ?")
            params.append(content)
        if image_url is not None:
            update_fields.append("image_url = ?")
            params.append(image_url)
        if update_fields:
            params.append(post_id)
            conn.execute(f"UPDATE posts SET {', '.join(update_fields)} WHERE id = ?", params)
            conn.commit()


def delete_post(post_id, user_id):
    with get_db_connection() as conn:
        # Проверить, что пост принадлежит пользователю
        post = conn.execute("SELECT user_id, image_url FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post or post['user_id'] != user_id:
            raise ValueError("Пост не найден или нет доступа")

        # Удалить файл изображения, если есть
        if post['image_url']:
            import os
            image_path = os.path.join(os.path.dirname(__file__), 'uploads', post['image_url'])
            if os.path.exists(image_path):
                os.remove(image_path)

        # Удалить пост
        conn.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM reposts WHERE original_post_id = ?", (post_id,))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()


def delete_chat(chat_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()


def delete_group(group_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM group_messages WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()