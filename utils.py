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

        # === Мероприятия ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_date DATETIME,
                location TEXT,
                creator_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users (id)
            )
        """)

        # === Участники мероприятий ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'invited',  -- invited, confirmed, declined
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(event_id, user_id)
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
    print(f"DEBUG: get_user_chats called with user_id: {user_id}")
    with get_db_connection() as conn:
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        print(f"DEBUG: user fetchone result: {user}")
        if user is None:
            print(f"DEBUG: User with id {user_id} not found, returning empty list")
            return []
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

def get_messages(chat_id, offset=0, limit=50):
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT m.id, m.sender, m.message, m.timestamp, m.status, m.parent_message_id, m.edited, m.message_type, m.audio_path,
                   p.sender as parent_sender, p.message as parent_message,
                   u.avatar as sender_avatar
            FROM messages m
            LEFT JOIN messages p ON m.parent_message_id = p.id
            LEFT JOIN users u ON m.sender = u.username
            WHERE m.chat_id = ? ORDER BY m.timestamp
            LIMIT ? OFFSET ?
        """, (chat_id, limit, offset)).fetchall()
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


def get_group_messages(group_id, offset=0, limit=50):
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
            LIMIT ? OFFSET ?
        """, (group_id, limit, offset)).fetchall()
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


def get_feed(user_id, offset=0, limit=10):
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
                LIMIT ? OFFSET ?
            """, (user_id, user_id, limit, offset)).fetchall()
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


def get_channel_messages(channel_id, offset=0, limit=50):
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
            LIMIT ? OFFSET ?
        """, (channel_id, limit, offset)).fetchall()
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


# === Функции для поиска ===

def search_messages_global(query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Глобальный поиск по сообщениям (личные, групповые, каналы)
    
    Args:
        query (str): Поисковый запрос
        user_id (int): ID пользователя для фильтрации доступа
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        list: Список найденных сообщений с типом и контекстом
    """
    with get_db_connection() as conn:
        # Подготовить параметры поиска
        search_pattern = f"%{query}%"
        search_params = (search_pattern, user_id, user_id, limit, offset)
        
        # SQL шаблон для поиска с учетом или без регистра
        search_column = "message" if case_sensitive else "LOWER(message)"
        query_condition = f"{search_column} LIKE ?" if case_sensitive else f"LOWER({search_column}) LIKE LOWER(?)"
        
        # Поиск по личным сообщениям
        private_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                'private' as message_type,
                c.id as chat_id,
                CASE 
                    WHEN c.user1_id = ? THEN (SELECT username FROM users WHERE id = c.user2_id)
                    ELSE (SELECT username FROM users WHERE id = c.user1_id)
                END as chat_partner
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE {query_condition}
              AND (c.user1_id = ? OR c.user2_id = ?)
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        # Поиск по сообщениям в группах
        group_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                'group' as message_type,
                g.id as group_id,
                g.name as group_name
            FROM group_messages m
            JOIN groups g ON m.group_id = g.id
            JOIN group_members gm ON g.id = gm.group_id
            WHERE {query_condition}
              AND gm.user_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        # Поиск по сообщениям в каналах
        channel_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                'channel' as message_type,
                ch.id as channel_id,
                ch.name as channel_name
            FROM channel_messages m
            JOIN channels ch ON m.channel_id = ch.id
            JOIN channel_members cm ON ch.id = cm.channel_id
            WHERE {query_condition}
              AND cm.user_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        # Выполнить все три запроса
        private_messages = conn.execute(
            private_messages_query, 
            (search_pattern, user_id, user_id, user_id, limit, offset)
        ).fetchall()
        
        group_messages = conn.execute(
            group_messages_query, 
            (search_pattern, user_id, limit, offset)
        ).fetchall()
        
        channel_messages = conn.execute(
            channel_messages_query, 
            (search_pattern, user_id, limit, offset)
        ).fetchall()
        
        # Объединить результаты и отсортировать по времени
        all_messages = []
        for msg in private_messages:
            all_messages.append(dict(msg))
        for msg in group_messages:
            all_messages.append(dict(msg))
        for msg in channel_messages:
            all_messages.append(dict(msg))
        
        # Сортировать по времени (новые первыми)
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_messages[:limit]


def search_posts_global(query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Глобальный поиск по постам
    
    Args:
        query (str): Поисковый запрос
        user_id (int): ID пользователя для фильтрации доступа
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        list: Список найденных постов с дополнительной информацией
    """
    with get_db_connection() as conn:
        # Подготовить параметры поиска
        search_pattern = f"%{query}%"
        
        # SQL шаблон для поиска с учетом или без регистра
        search_column = "content" if case_sensitive else "LOWER(content)"
        query_condition = f"{search_column} LIKE ?" if case_sensitive else f"LOWER({search_column}) LIKE LOWER(?)"
        
        # Поиск по постам с информацией о пользователе и метриках
        posts_query = f"""
            SELECT 
                p.id,
                p.content,
                p.image_url,
                p.created_at,
                u.username,
                u.avatar,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count,
                (SELECT COUNT(*) FROM reposts WHERE original_post_id = p.id) as reposts_count,
                (SELECT COUNT(*) FROM reactions WHERE post_id = p.id) as reactions_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE {query_condition}
              AND (
                  p.user_id IN (SELECT following_id FROM subscriptions WHERE follower_id = ?) 
                  OR p.user_id = ?
              )
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """
        
        posts = conn.execute(
            posts_query, 
            (search_pattern, user_id, user_id, limit, offset)
        ).fetchall()
        
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            # Добавить информацию о том, лайкнул ли текущий пользователь этот пост
            post_dict['is_liked'] = is_liked(user_id, post['id'])
            post_dict['is_reposted'] = is_reposted(user_id, post['id'])
            post_dict['is_reacted'] = is_reacted(user_id, post['id'])
            
            # Добавить реакции для каждого поста
            reactions = get_reactions_for_post(post['id'])
            reactions_grouped = {}
            for r in reactions:
                emoji = r['emoji']
                if emoji not in reactions_grouped:
                    reactions_grouped[emoji] = []
                reactions_grouped[emoji].append({'username': r['username'], 'user_id': r['user_id']})
            post_dict['reactions'] = reactions_grouped
            
            posts_list.append(post_dict)
        
        return posts_list


def search_messages_in_chat(chat_partner_username, query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Локальный поиск по сообщениям в конкретном чате
    
    Args:
        chat_partner_username (str): Имя пользователя-собеседника
        query (str): Поисковый запрос
        user_id (int): ID текущего пользователя
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        list: Список найденных сообщений в чате
    """
    with get_db_connection() as conn:
        # Найти ID собеседника
        partner = conn.execute("SELECT id FROM users WHERE username = ?", (chat_partner_username,)).fetchone()
        if not partner:
            return []
        
        partner_id = partner['id']
        
        # Определить ID чата
        chat_ids = conn.execute("""
            SELECT id FROM chats 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        """, (user_id, partner_id, partner_id, user_id)).fetchall()
        
        if not chat_ids:
            return []
        
        chat_id = chat_ids[0]['id']
        
        # Подготовить параметры поиска
        search_pattern = f"%{query}%"
        
        # SQL шаблон для поиска с учетом или без регистра
        search_column = "message" if case_sensitive else "LOWER(message)"
        query_condition = f"{search_column} LIKE ?" if case_sensitive else f"LOWER({search_column}) LIKE LOWER(?)"
        
        # Поиск по сообщениям в конкретном чате
        chat_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                m.status,
                m.parent_message_id,
                m.edited,
                m.message_type,
                m.audio_path
            FROM messages m
            WHERE {query_condition}
              AND m.chat_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        messages = conn.execute(
            chat_messages_query, 
            (search_pattern, chat_id, limit, offset)
        ).fetchall()
        
        return [dict(msg) for msg in messages]


def search_messages_in_group(group_name, query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Локальный поиск по сообщениям в конкретной группе
    
    Args:
        group_name (str): Название группы
        query (str): Поисковый запрос
        user_id (int): ID текущего пользователя
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        list: Список найденных сообщений в группе
    """
    with get_db_connection() as conn:
        # Проверить, является ли пользователь участником группы
        group = conn.execute("SELECT id FROM groups WHERE name = ?", (group_name,)).fetchone()
        if not group:
            return []
        
        group_id = group['id']
        member = conn.execute(
            "SELECT id FROM group_members WHERE group_id = ? AND user_id = ?", 
            (group_id, user_id)
        ).fetchone()
        
        if not member:
            return []  # Пользователь не является участником группы
        
        # Подготовить параметры поиска
        search_pattern = f"%{query}%"
        
        # SQL шаблон для поиска с учетом или без регистра
        search_column = "message" if case_sensitive else "LOWER(message)"
        query_condition = f"{search_column} LIKE ?" if case_sensitive else f"LOWER({search_column}) LIKE LOWER(?)"
        
        # Поиск по сообщениям в конкретной группе
        group_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                m.is_read,
                m.parent_message_id,
                m.edited,
                m.message_type,
                m.audio_path
            FROM group_messages m
            WHERE {query_condition}
              AND m.group_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        messages = conn.execute(
            group_messages_query, 
            (search_pattern, group_id, limit, offset)
        ).fetchall()
        
        return [dict(msg) for msg in messages]


def search_messages_in_channel(channel_name, query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Локальный поиск по сообщениям в конкретном канале
    
    Args:
        channel_name (str): Название канала
        query (str): Поисковый запрос
        user_id (int): ID текущего пользователя
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        list: Список найденных сообщений в канале
    """
    with get_db_connection() as conn:
        # Проверить, является ли пользователь участником канала
        channel = conn.execute("SELECT id FROM channels WHERE name = ?", (channel_name,)).fetchone()
        if not channel:
            return []
        
        channel_id = channel['id']
        member = conn.execute(
            "SELECT id FROM channel_members WHERE channel_id = ? AND user_id = ?", 
            (channel_id, user_id)
        ).fetchone()
        
        if not member:
            return []  # Пользователь не является участником канала
        
        # Подготовить параметры поиска
        search_pattern = f"%{query}%"
        
        # SQL шаблон для поиска с учетом или без регистра
        search_column = "message" if case_sensitive else "LOWER(message)"
        query_condition = f"{search_column} LIKE ?" if case_sensitive else f"LOWER({search_column}) LIKE LOWER(?)"
        
        # Поиск по сообщениям в конкретном канале
        channel_messages_query = f"""
            SELECT 
                m.id,
                m.sender,
                m.message,
                m.timestamp,
                m.is_read,
                m.parent_message_id,
                m.edited,
                m.message_type,
                m.audio_path
            FROM channel_messages m
            WHERE {query_condition}
              AND m.channel_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        messages = conn.execute(
            channel_messages_query, 
            (search_pattern, channel_id, limit, offset)
        ).fetchall()
        
        return [dict(msg) for msg in messages]


def search_all_content(query, user_id, case_sensitive=False, limit=50, offset=0):
    """
    Поиск по всем типам контента (сообщения и посты)
    
    Args:
        query (str): Поисковый запрос
        user_id (int): ID текущего пользователя
        case_sensitive (bool): Учитывать регистр при поиске
        limit (int): Максимальное количество результатов
        offset (int): Смещение для пагинации
    
    Returns:
        dict: Результаты поиска по разным типам контента
    """
    messages = search_messages_global(query, user_id, case_sensitive, limit, offset)
    posts = search_posts_global(query, user_id, case_sensitive, limit, offset)
    
    return {
        'messages': messages,
        'posts': posts,
        'total_messages': len(messages),
        'total_posts': len(posts)
    }


# === Функции для работы с мероприятиями ===

def create_event(title, description, event_date, location, creator_id):
    """
    Создать новое мероприятие
    
    Args:
        title (str): Название мероприятия
        description (str): Описание мероприятия
        event_date (datetime): Дата и время мероприятия
        location (str): Место проведения мероприятия
        creator_id (int): ID создателя мероприятия
    
    Returns:
        int: ID созданного мероприятия
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (title, description, event_date, location, creator_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, event_date, location, creator_id))
        conn.commit()
        return cursor.lastrowid


def get_event_by_id(event_id):
    """
    Получить мероприятие по ID
    
    Args:
        event_id (int): ID мероприятия
    
    Returns:
        dict: Информация о мероприятии
    """
    with get_db_connection() as conn:
        event = conn.execute("""
            SELECT e.*, u.username as creator_username
            FROM events e
            JOIN users u ON e.creator_id = u.id
            WHERE e.id = ?
        """, (event_id,)).fetchone()
        return dict(event) if event else None


def get_events_for_user(user_id):
    """
    Получить мероприятия, в которых участвует пользователь
    
    Args:
        user_id (int): ID пользователя
    
    Returns:
        list: Список мероприятий
    """
    with get_db_connection() as conn:
        events = conn.execute("""
            SELECT e.*, u.username as creator_username,
                   ep.status as participant_status
            FROM events e
            JOIN event_participants ep ON e.id = ep.event_id
            JOIN users u ON e.creator_id = u.id
            WHERE ep.user_id = ?
            ORDER BY e.event_date DESC
        """, (user_id,)).fetchall()
        return [dict(event) for event in events]


def get_events_created_by_user(user_id):
    """
    Получить мероприятия, созданные пользователем
    
    Args:
        user_id (int): ID пользователя
    
    Returns:
        list: Список мероприятий
    """
    with get_db_connection() as conn:
        events = conn.execute("""
            SELECT e.*, u.username as creator_username,
                   (SELECT COUNT(*) FROM event_participants WHERE event_id = e.id) as participants_count
            FROM events e
            JOIN users u ON e.creator_id = u.id
            WHERE e.creator_id = ?
            ORDER BY e.event_date DESC
        """, (user_id,)).fetchall()
        return [dict(event) for event in events]


def add_event_participant(event_id, user_id, status='invited'):
    """
    Добавить участника к мероприятию
    
    Args:
        event_id (int): ID мероприятия
        user_id (int): ID пользователя
        status (str): Статус участника (invited, confirmed, declined)
    """
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO event_participants (event_id, user_id, status)
            VALUES (?, ?, ?)
        """, (event_id, user_id, status))
        conn.commit()


def remove_event_participant(event_id, user_id):
    """
    Удалить участника из мероприятия
    
    Args:
        event_id (int): ID мероприятия
        user_id (int): ID пользователя
    """
    with get_db_connection() as conn:
        conn.execute("""
            DELETE FROM event_participants WHERE event_id = ? AND user_id = ?
        """, (event_id, user_id))
        conn.commit()


def update_participant_status(event_id, user_id, status):
    """
    Обновить статус участника мероприятия
    
    Args:
        event_id (int): ID мероприятия
        user_id (int): ID пользователя
        status (str): Новый статус участника
    """
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE event_participants SET status = ?
            WHERE event_id = ? AND user_id = ?
        """, (status, event_id, user_id))
        conn.commit()


def get_event_participants(event_id):
    """
    Получить список участников мероприятия
    
    Args:
        event_id (int): ID мероприятия
    
    Returns:
        list: Список участников
    """
    with get_db_connection() as conn:
        participants = conn.execute("""
            SELECT u.username, ep.status, ep.joined_at
            FROM event_participants ep
            JOIN users u ON ep.user_id = u.id
            WHERE ep.event_id = ?
        """, (event_id,)).fetchall()
        return [dict(participant) for participant in participants]


def get_upcoming_events(limit=10):
    """
    Получить предстоящие мероприятия
    
    Args:
        limit (int): Максимальное количество мероприятий
    
    Returns:
        list: Список предстоящих мероприятий
    """
    with get_db_connection() as conn:
        events = conn.execute("""
            SELECT e.*, u.username as creator_username,
                   (SELECT COUNT(*) FROM event_participants WHERE event_id = e.id) as participants_count
            FROM events e
            JOIN users u ON e.creator_id = u.id
            WHERE e.event_date >= datetime('now')
            ORDER BY e.event_date ASC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(event) for event in events]