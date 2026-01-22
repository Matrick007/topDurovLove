# utils.py (обновлённый)
import sqlite3
import hashlib
from contextlib import contextmanager
import datetime
import uuid

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
                status TEXT,
                banner_photo TEXT,
                banner_color TEXT
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
                status TEXT DEFAULT 'sent',  -- sent, delivered, read
                parent_message_id INTEGER REFERENCES messages(id),
                edited BOOLEAN DEFAULT FALSE
            )
        """)

        # === ГРУППЫ ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                creator TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                pinned_msg_id INTEGER,
                description TEXT
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
                edited BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        """)

        # Добавить тестовых пользователей
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('test1', hash_password('pass1'), 'Москва', 'Привет'))
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('test2', hash_password('pass2'), 'СПб', 'Хай'))
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('user1', hash_password('pass1'), 'Екатеринбург', 'Тест'))
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('user2', hash_password('pass2'), 'Казань', 'Привет всем'))
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('alex', hash_password('pass1'), 'Новосибирск', 'Разработчик'))
        conn.execute("INSERT OR IGNORE INTO users (username, password, city, bio_short) VALUES (?, ?, ?, ?)", ('maria', hash_password('pass2'), 'Владивосток', 'Дизайнер'))

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

        # === Комментарии к сообщениям ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS message_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                user_id INTEGER,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # === Комментарии к профилям ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profile_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                profile_user_id INTEGER,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (profile_user_id) REFERENCES users (id)
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

        # === Реакции ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                emoji TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """)

        # === Ответы на комментарии ===
        try:
            conn.execute("ALTER TABLE comments ADD COLUMN parent_comment_id INTEGER REFERENCES comments(id)")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE messages ADD COLUMN parent_message_id INTEGER REFERENCES messages(id)")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # === Сообщения в каналах ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                edited BOOLEAN DEFAULT FALSE,
                parent_message_id INTEGER REFERENCES channel_messages(id),
                FOREIGN KEY (channel_id) REFERENCES channels (id)
            )
        """)

        try:
            conn.execute("ALTER TABLE group_messages ADD COLUMN parent_message_id INTEGER REFERENCES group_messages(id)")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE messages ADD COLUMN edited BOOLEAN DEFAULT FALSE")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE group_messages ADD COLUMN edited BOOLEAN DEFAULT FALSE")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE channel_messages ADD COLUMN parent_message_id INTEGER REFERENCES channel_messages(id)")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # === Добавление полей для голосовых сообщений ===
        try:
            conn.execute("ALTER TABLE messages ADD COLUMN message_type VARCHAR DEFAULT 'text'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE messages ADD COLUMN audio_path VARCHAR")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE group_messages ADD COLUMN message_type VARCHAR DEFAULT 'text'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE group_messages ADD COLUMN audio_path VARCHAR")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE channel_messages ADD COLUMN message_type VARCHAR DEFAULT 'text'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE channel_messages ADD COLUMN audio_path VARCHAR")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # === Закрепленные посты ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pinned_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
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

        # === Каналы ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                creator TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_private BOOLEAN DEFAULT FALSE
            )
        """)

        # === Участники каналов ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                user_id INTEGER,
                role_id INTEGER,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (role_id) REFERENCES channel_roles (id),
                UNIQUE(channel_id, user_id)
            )
        """)

        # === Приглашения в каналы ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                invite_code TEXT UNIQUE NOT NULL,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                max_uses INTEGER DEFAULT NULL,
                uses INTEGER DEFAULT 0,
                FOREIGN KEY (channel_id) REFERENCES channels (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)

        # === Роли в каналах ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                role_name TEXT NOT NULL,
                permissions TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels (id),
                UNIQUE(channel_id, role_name)
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
            conn.execute("ALTER TABLE groups ADD COLUMN description TEXT")
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

        try:
            conn.execute("ALTER TABLE users ADD COLUMN banner_photo TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN banner_color TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE channel_invites ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
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
            SELECT DISTINCT u.username, u.id, u.avatar,
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
            SELECT m.id, m.sender, m.message, m.timestamp, m.status, m.parent_message_id, m.edited, m.message_type, m.audio_path,
                   p.sender as parent_sender, p.message as parent_message,
                   u.avatar as sender_avatar
            FROM messages m
            LEFT JOIN messages p ON m.parent_message_id = p.id
            LEFT JOIN users u ON m.sender = u.username
            WHERE m.chat_id = ? ORDER BY m.timestamp
        """, (chat_id,)).fetchall()
    print(f"Getting messages for chat {chat_id}: {len(messages)} messages")
    return [dict(m) for m in messages]

def save_message(chat_id, sender, message, parent_message_id=None, message_type='text', audio_path=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (chat_id, sender, message, parent_message_id, message_type, audio_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chat_id, sender, message, parent_message_id, message_type, audio_path))
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




def create_group(name, creator, description=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (name, creator, description) VALUES (?, ?, ?)", (name, creator, description))
        conn.commit()
        return cursor.lastrowid


def get_group_by_name(name):
    with get_db_connection() as conn:
        group = conn.execute("SELECT * FROM groups WHERE name = ?", (name,)).fetchone()
        return group


def get_groups_for_user(user_id):
    print(f"get_groups_for_user called for user_id: {user_id}")
    try:
        with get_db_connection() as conn:
            user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                print(f"No user found for id {user_id}")
                return []
            my_username = user['username']
            print(f"Username: {my_username}")
            groups = conn.execute("""
                SELECT g.name,
                    (SELECT gm2.message FROM group_messages gm2 WHERE gm2.group_id = g.id ORDER BY gm2.timestamp DESC LIMIT 1) as last_message,
                    (SELECT gm2.timestamp FROM group_messages gm2 WHERE gm2.group_id = g.id ORDER BY gm2.timestamp DESC LIMIT 1) as last_time,
                    (SELECT COUNT(*) FROM group_messages gm2 WHERE gm2.group_id = g.id AND gm2.sender != ? AND gm2.is_read = 0) as unread_count
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = ?
            """, (my_username, user_id)).fetchall()
            print(f"Found groups: {[dict(g) for g in groups]}")
        return [dict(g) for g in groups]
    except Exception as e:
        print(f"Error in get_groups_for_user: {e}")
        import traceback
        traceback.print_exc()
        return []


def add_user_to_group(group_id, user_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()


def get_group_messages(group_id):
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT m.id, m.sender, m.message, m.timestamp, m.is_read, m.parent_message_id, m.edited, m.message_type, m.audio_path,
                   p.sender as parent_sender, p.message as parent_message,
                   u.avatar as sender_avatar
            FROM group_messages m
            LEFT JOIN group_messages p ON m.parent_message_id = p.id
            LEFT JOIN users u ON m.sender = u.username
            WHERE m.group_id = ?
            ORDER BY m.timestamp
        """, (group_id,)).fetchall()
        return [dict(m) for m in messages]


def save_group_message(group_id, sender, message, is_read=False, parent_message_id=None, message_type='text', audio_path=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender, message, is_read, parent_message_id, message_type, audio_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (group_id, sender, message, is_read, parent_message_id, message_type, audio_path))
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
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            # Добавить реакции для каждого поста
            reactions = get_reactions_for_post(post['id'])
            reactions_grouped = {}
            for r in reactions:
                emoji = r['emoji']
                if emoji not in reactions_grouped:
                    reactions_grouped[emoji] = []
                reactions_grouped[emoji].append({'username': r['username'], 'user_id': r['user_id']})
            post_dict['reactions'] = reactions_grouped
            post_dict['is_reacted'] = is_reacted(user_id, post['id'])
            posts_list.append(post_dict)
        return posts_list


def get_feed(user_id):
    try:
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
            posts_list = []
            for post in posts:
                post_dict = dict(post)
                # Добавить реакции для каждого поста
                reactions = get_reactions_for_post(post['id'])
                reactions_grouped = {}
                for r in reactions:
                    emoji = r['emoji']
                    if emoji not in reactions_grouped:
                        reactions_grouped[emoji] = []
                    reactions_grouped[emoji].append({'username': r['username'], 'user_id': r['user_id']})
                post_dict['reactions'] = reactions_grouped
                post_dict['is_reacted'] = is_reacted(user_id, post['id'])
                posts_list.append(post_dict)
            return posts_list
    except Exception as e:
        print(f"Error in get_feed for user_id {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return []


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
            WHERE c.post_id = ? AND c.parent_comment_id IS NULL
            ORDER BY c.created_at ASC
        """, (post_id,)).fetchall()]

def add_profile_comment(user_id, profile_user_id, content):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO profile_comments (user_id, profile_user_id, content) VALUES (?, ?, ?)", (user_id, profile_user_id, content))
        conn.commit()
        return cursor.lastrowid

def get_profile_comments_for_user(profile_user_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT pc.*, u.username FROM profile_comments pc
            JOIN users u ON pc.user_id = u.id
            WHERE pc.profile_user_id = ?
            ORDER BY pc.created_at ASC
        """, (profile_user_id,)).fetchall()]

def get_replies_for_comment(comment_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT c.*, u.username FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.parent_comment_id = ?
            ORDER BY c.created_at ASC
        """, (comment_id,)).fetchall()]

def add_reply(user_id, post_id, parent_comment_id, content):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (user_id, post_id, parent_comment_id, content) VALUES (?, ?, ?, ?)", (user_id, post_id, parent_comment_id, content))
        conn.commit()
        return cursor.lastrowid

def add_reaction(user_id, post_id, emoji):
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO reactions (user_id, post_id, emoji) VALUES (?, ?, ?)", (user_id, post_id, emoji))
        conn.commit()

def remove_reaction(user_id, post_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM reactions WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.commit()

def get_reactions_for_post(post_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT r.*, u.username FROM reactions r
            JOIN users u ON r.user_id = u.id
            WHERE r.post_id = ?
            ORDER BY r.created_at ASC
        """, (post_id,)).fetchall()]

def is_reacted(user_id, post_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT emoji FROM reactions WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone() is not None

def pin_post(user_id, post_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO pinned_posts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()

def unpin_post(user_id, post_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM pinned_posts WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.commit()

def is_pinned(user_id, post_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM pinned_posts WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone() is not None

def get_pinned_posts(user_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT p.*, u.username FROM pinned_posts pp
            JOIN posts p ON pp.post_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE pp.user_id = ?
            ORDER BY pp.created_at DESC
        """, (user_id,)).fetchall()]


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


def get_reposts_for_user(user_id):
    with get_db_connection() as conn:
        reposts = conn.execute("""
            SELECT p.*, u.username,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                   (SELECT COUNT(*) FROM reposts WHERE original_post_id = p.id) as reposts_count
            FROM reposts r
            JOIN posts p ON r.original_post_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,)).fetchall()
        reposts_list = []
        for repost in reposts:
            repost_dict = dict(repost)
            # Добавить реакции для каждого поста
            reactions = get_reactions_for_post(repost['id'])
            reactions_grouped = {}
            for r in reactions:
                emoji = r['emoji']
                if emoji not in reactions_grouped:
                    reactions_grouped[emoji] = []
                reactions_grouped[emoji].append({'username': r['username'], 'user_id': r['user_id']})
            repost_dict['reactions'] = reactions_grouped
            repost_dict['is_reacted'] = is_reacted(user_id, repost['id'])
            reposts_list.append(repost_dict)
        return reposts_list


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


# === Дополнительная статистика для профиля ===

def get_top_posts(user_id, limit=3):
    """Получить топ постов пользователя по количеству лайков"""
    with get_db_connection() as conn:
        posts = conn.execute("""
            SELECT p.id, p.content, p.created_at, p.image_url,
                   COUNT(l.id) as likes_count
            FROM posts p
            LEFT JOIN likes l ON p.id = l.post_id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY likes_count DESC, p.created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(post) for post in posts]


def get_monthly_activity(user_id):
    """Получить активность по месяцам (количество постов)"""
    with get_db_connection() as conn:
        monthly_data = conn.execute("""
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as count
            FROM posts
            WHERE user_id = ?
            GROUP BY month
            ORDER BY month
        """, (user_id,)).fetchall()

        # Преобразуем в словарь для удобства
        monthly = {}
        for row in monthly_data:
            monthly[row['month']] = row['count']

        return monthly


def get_followers_growth(user_id):
    """Получить динамику роста подписчиков"""
    with get_db_connection() as conn:
        # Получаем подписки по месяцам
        growth_data = conn.execute("""
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as new_followers
            FROM subscriptions
            WHERE following_id = ?
            GROUP BY month
            ORDER BY month
        """, (user_id,)).fetchall()

        # Преобразуем в кумулятивный график
        cumulative = {}
        total = 0
        for row in growth_data:
            total += row['new_followers']
            cumulative[row['month']] = total

        return cumulative


def get_posts_with_images_percentage(user_id):
    """Получить процент постов с изображениями"""
    with get_db_connection() as conn:
        total_posts = conn.execute("SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)).fetchone()[0]
        posts_with_images = conn.execute("SELECT COUNT(*) FROM posts WHERE user_id = ? AND image_url IS NOT NULL", (user_id,)).fetchone()[0]

        if total_posts == 0:
            return 0

        return round((posts_with_images / total_posts) * 100)


def get_message_by_id(msg_id):
    with get_db_connection() as conn:
        msg = conn.execute("SELECT sender, message FROM messages WHERE id = ?", (msg_id,)).fetchone()
        if not msg:
            msg = conn.execute("SELECT sender, message FROM group_messages WHERE id = ?", (msg_id,)).fetchone()
        if not msg:
            msg = conn.execute("SELECT sender, message FROM channel_messages WHERE id = ?", (msg_id,)).fetchone()
        return msg


def get_channel_messages(channel_id):
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT m.id, m.sender, m.message, m.timestamp, m.is_read, m.parent_message_id, m.edited, m.message_type, m.audio_path,
                   p.sender as parent_sender, p.message as parent_message,
                   u.avatar as sender_avatar
            FROM channel_messages m
            LEFT JOIN channel_messages p ON m.parent_message_id = p.id
            LEFT JOIN users u ON m.sender = u.username
            WHERE m.channel_id = ?
            ORDER BY m.timestamp
        """, (channel_id,)).fetchall()
        return [dict(m) for m in messages]


def save_channel_message(channel_id, sender, message, is_read=False, parent_message_id=None, message_type='text', audio_path=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO channel_messages (channel_id, sender, message, is_read, parent_message_id, message_type, audio_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (channel_id, sender, message, is_read, parent_message_id, message_type, audio_path))
        conn.commit()
        return cursor.lastrowid


def update_channel_message_read(msg_id, is_read=True):
    with get_db_connection() as conn:
        conn.execute("UPDATE channel_messages SET is_read = ? WHERE id = ?", (is_read, msg_id))
        conn.commit()


# === Каналы ===

def create_channel(name, creator, description=None, is_private=False):
    print(f"create_channel called with name: {repr(name)}, creator: {repr(creator)}, description: {repr(description)}, is_private: {is_private}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO channels (name, creator, description, is_private) VALUES (?, ?, ?, ?)", (name, creator, description, is_private))
        channel_id = cursor.lastrowid
        print(f"Channel created successfully, channel_id: {channel_id}")
        # Создать дефолтные роли для канала
        cursor.execute("INSERT INTO channel_roles (channel_id, role_name, permissions) VALUES (?, 'Admin', 'read,write,manage_members,manage_roles,manage_invites')", (channel_id,))
        admin_role_id = cursor.lastrowid
        print(f"Admin role id: {admin_role_id}")
        cursor.execute("INSERT INTO channel_roles (channel_id, role_name, permissions) VALUES (?, 'Moderator', 'read,write,manage_members')", (channel_id,))
        moderator_role_id = cursor.lastrowid
        cursor.execute("INSERT INTO channel_roles (channel_id, role_name, permissions) VALUES (?, 'Member', 'read,write')", (channel_id,))
        member_role_id = cursor.lastrowid
        # Добавить создателя как участника с ролью администратора
        user = conn.execute("SELECT id FROM users WHERE username = ?", (creator.lower(),)).fetchone()
        print(f"User found: {user}")
        if user:
            cursor.execute("INSERT INTO channel_members (channel_id, user_id, role_id) VALUES (?, ?, ?)", (channel_id, user['id'], admin_role_id))
            print(f"Inserted member: channel_id={channel_id}, user_id={user['id']}, role_id={admin_role_id}")
        else:
            print(f"Creator {creator} not found")
        conn.commit()
        print(f"Channel setup complete for channel_id: {channel_id}")
        return channel_id


def get_channel_by_name(name):
    print(f"get_channel_by_name called with name: {repr(name)}")
    print(f"name type: {type(name)}, len: {len(name)}")
    with get_db_connection() as conn:
        all_channels = conn.execute("SELECT name FROM channels").fetchall()
        print(f"All channels in DB: {[repr(row[0]) for row in all_channels]}")
        channel = conn.execute("SELECT * FROM channels WHERE name = ?", (name,)).fetchone()
        print(f"SQL Query: SELECT * FROM channels WHERE name = {repr(name)}")
        print(f"Query returned: {channel}")
        if not channel:
            print(f"Channel '{name}' not found in DB")
            # Попробуем не точное совпадение, сравним
            for row in all_channels:
                db_name = row[0]
                print(f"Comparing '{repr(name)}' with DB '{repr(db_name)}'")
        else:
            print(f"Channel found: {dict(channel) if channel else None}")
        return channel


def get_channels_for_user(user_id):
    with get_db_connection() as conn:
        channels = conn.execute("""
            SELECT c.name FROM channels c
            JOIN channel_members cm ON c.id = cm.channel_id
            WHERE cm.user_id = ?
        """, (user_id,)).fetchall()
        print(f"get_channels_for_user({user_id}) -> {[dict(c) for c in channels]}")
        return [dict(channel) for channel in channels]


def add_user_to_channel(channel_id, user_id, role_id=None):
    print(f"add_user_to_channel({channel_id}, {user_id}, {role_id})")
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO channel_members (channel_id, user_id, role_id) VALUES (?, ?, ?)", (channel_id, user_id, role_id))
        conn.commit()
        print(f"Added user {user_id} to channel {channel_id} with role {role_id}")


def remove_user_from_channel(channel_id, user_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel_id, user_id))
        conn.commit()


def create_channel_role(channel_id, role_name, permissions):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO channel_roles (channel_id, role_name, permissions) VALUES (?, ?, ?)", (channel_id, role_name, permissions))
        conn.commit()
        return cursor.lastrowid


def get_channel_members(channel_id):
    with get_db_connection() as conn:
        members = conn.execute("""
            SELECT u.username, cr.role_name FROM channel_members cm
            JOIN users u ON cm.user_id = u.id
            LEFT JOIN channel_roles cr ON cm.role_id = cr.id
            WHERE cm.channel_id = ?
        """, (channel_id,)).fetchall()
        return [dict(member) for member in members]


def get_user_channel_role(user_id, channel_id):
    with get_db_connection() as conn:
        role = conn.execute("""
            SELECT cr.role_name FROM channel_members cm
            JOIN channel_roles cr ON cm.role_id = cr.id
            WHERE cm.channel_id = ? AND cm.user_id = ?
        """, (channel_id, user_id)).fetchone()
        return role['role_name'] if role else None


def create_channel_invite(channel_id, created_by, expires_at=None, max_uses=None):
    invite_code = str(uuid.uuid4())
    print(f"DEBUG: Creating invite for channel {channel_id}, expires_at={expires_at}, max_uses={max_uses}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO channel_invites (channel_id, invite_code, created_by, expires_at, max_uses) VALUES (?, ?, ?, ?, ?)", (channel_id, invite_code, created_by, expires_at, max_uses))
        conn.commit()
        print(f"DEBUG: Invite created with code {invite_code}")
        return invite_code


def use_channel_invite(invite_code, user_id):
    with get_db_connection() as conn:
        invite = conn.execute("SELECT * FROM channel_invites WHERE invite_code = ?", (invite_code,)).fetchone()
        if not invite:
            return False
        if invite['expires_at'] and invite['expires_at'] < datetime.now():
            return False
        if invite['max_uses'] and invite['uses'] >= invite['max_uses']:
            return False
        # Добавить пользователя в канал
        add_user_to_channel(invite['channel_id'], user_id)
        # Увеличить счетчик использований
        conn.execute("UPDATE channel_invites SET uses = uses + 1 WHERE id = ?", (invite['id'],))
        conn.commit()
        return True


def get_channel_invites(channel_id):
    with get_db_connection() as conn:
        invites = conn.execute("SELECT * FROM channel_invites WHERE channel_id = ?", (channel_id,)).fetchall()
        invites_list = [dict(invite) for invite in invites]
        print(f"DEBUG: Loaded {len(invites_list)} invites for channel {channel_id}: {[i['invite_code'] for i in invites_list]}")
        return invites_list


def delete_channel_invite(invite_id):
    with get_db_connection() as conn:
        # Проверить, что инвайт существует
        invite = conn.execute("SELECT * FROM channel_invites WHERE id = ?", (invite_id,)).fetchone()
        if not invite:
            raise ValueError("Инвайт не найден")
        # Удалить инвайт
        conn.execute("DELETE FROM channel_invites WHERE id = ?", (invite_id,))
        conn.commit()


def add_message_comment(message_id, user_id, content):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO message_comments (message_id, user_id, content) VALUES (?, ?, ?)", (message_id, user_id, content))
        conn.commit()
        return cursor.lastrowid


def get_comments_for_message(message_id):
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT mc.*, u.username FROM message_comments mc
            JOIN users u ON mc.user_id = u.id
            WHERE mc.message_id = ?
            ORDER BY mc.created_at ASC
        """, (message_id,)).fetchall()]