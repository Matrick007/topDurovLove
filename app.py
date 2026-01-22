# app.py
import os
import sqlite3
import time
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from utils import (
    get_db_connection, init_db, hash_password, verify_password, get_user_by_username,
    get_or_create_chat, get_messages, get_active_users, create_user, save_message,
    mark_message_as_delivered, mark_message_as_read, get_unread_messages,
    create_group, get_group_by_name, get_groups_for_user, add_user_to_group,
    get_group_messages, save_group_message, delete_message, save_pinned_message,
    get_pinned_message, remove_pinned_message, delete_chat, delete_group, get_user_chats,
    follow_user, unfollow_user, is_following, get_followers, get_following,
    create_post, get_posts_for_user, get_feed, like_post, unlike_post, is_liked,
    add_comment, get_comments_for_post, repost, unrepost, is_reposted, get_reposts_for_user,
    update_group_message_read, edit_post, delete_post, get_top_posts,
    get_monthly_activity, get_followers_growth, get_posts_with_images_percentage,
    add_reply, get_replies_for_comment, add_reaction, remove_reaction, get_reactions_for_post, is_reacted,
    pin_post, unpin_post, is_pinned, get_pinned_posts, get_message_by_id,
    get_channel_messages, save_channel_message, update_channel_message_read,
    create_channel, get_channel_by_name, get_channels_for_user, add_user_to_channel,
    remove_user_from_channel, create_channel_role, get_channel_members, get_user_channel_role,
    create_channel_invite, use_channel_invite, get_channel_invites, delete_channel_invite,
    add_profile_comment, get_profile_comments_for_user, add_message_comment, get_comments_for_message
)
import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac'}

# Create uploads folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in AUDIO_EXTENSIONS

socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False, async_mode='threading')

# Трекинг
online_users = {}
user_sids = {}
user_chat_context = {}

init_db()


@app.route('/')
def index():
    print(f"index called, session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("No session in index")
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session['username']
    user = get_user_by_username(username)
    user_chats = get_user_chats(user_id)
    user_groups = get_groups_for_user(user_id)
    user_channels = get_channels_for_user(user_id)
    print(f"user_chats: {user_chats}")
    print(f"user_groups: {user_groups}")
    print(f"user_channels: {user_channels}")
    return render_template('index.html', username=username, user=user, user_chats=user_chats, user_groups=user_groups, user_channels=user_channels)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = get_user_by_username(username)
        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            # Log session
            with get_db_connection() as conn:
                conn.execute("INSERT INTO user_sessions (user_id) VALUES (?)", (user['id'],))
                conn.commit()
            return redirect(url_for('index'))
        return render_template('login.html', error="Неверный логин или пароль")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        city = request.form.get('city', '').strip()
        bio_short = request.form.get('bio_short', '').strip()
        if get_user_by_username(username):
            return render_template('register.html', error="Пользователь уже существует")
        create_user(username, password, city=city, bio_short=bio_short)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        username = session.get('username')
        # Очищаем онлайн статус при выходе
        if username:
            online_users.pop(username, None)
            user_sids.pop(username, None)
            user_chat_context.pop(username, None)
            # Уведомляем всех о выходе пользователя
            socketio.emit('user_status_update', {'user': username, 'status': 'offline'})

        # Log logout
        with get_db_connection() as conn:
            # Получаем последний незавершенный сеанс для пользователя
            session_record = conn.execute("""
                SELECT id FROM user_sessions
                WHERE user_id = ? AND logout_time IS NULL
                ORDER BY login_time DESC LIMIT 1
            """, (session['user_id'],)).fetchone()

            if session_record:
                conn.execute("UPDATE user_sessions SET logout_time = CURRENT_TIMESTAMP WHERE id = ?", (session_record['id'],))
                conn.commit()
    session.clear()
    return redirect(url_for('login'))


@app.route('/chat/<username>/history')
def chat_history(username):
    if 'user_id' not in session:
        return jsonify({'messages': [], 'chat_id': None})
    other_user = get_user_by_username(username)
    if not other_user:
        print(f"Other user {username} not found")
        return jsonify({'messages': [], 'chat_id': None})
    chat_id = get_or_create_chat(session['user_id'], other_user['id'])
    messages = get_messages(chat_id)
    print(f"Chat {chat_id} with {username} messages: {len(messages)}")
    return jsonify({'messages': messages, 'chat_id': chat_id})


@app.route('/group/<group_name>/history')
def group_history(group_name):
    if 'user_id' not in session:
        return jsonify({'messages': [], 'pinned': None, 'group_id': None})
    group = get_group_by_name(group_name)
    if not group:
        return jsonify({'messages': [], 'pinned': None, 'group_id': None})
    messages = get_group_messages(group['id'])
    try:
        pinned = get_pinned_message(group['id'])
    except:
        pinned = None
    return jsonify({'messages': messages, 'pinned': pinned, 'group_id': group['id']})


@app.route('/channel/<channel_name>/history')
def channel_history(channel_name):
    if 'user_id' not in session:
        return jsonify({'messages': [], 'pinned': None, 'channel_id': None})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'messages': [], 'pinned': None, 'channel_id': None})
    messages = get_channel_messages(channel['id'])
    pinned = None  # Каналы не имеют закрепленных сообщений пока
    return jsonify({'messages': messages, 'pinned': pinned, 'channel_id': channel['id']})


# === Socket.IO ===

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        user_sids[username] = request.sid
        online_users[username] = datetime.datetime.now()
        emit('user_status_update', {'user': username, 'status': 'online'}, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        online_users.pop(username, None)
        user_sids.pop(username, None)
        user_chat_context.pop(username, None)
        emit('user_status_update', {'user': username, 'status': 'offline'}, broadcast=True)


@socketio.on('set_chat_context')
def handle_set_context(data):
    username = session.get('username')
    if not username:
        return
    new_room = data.get('room')
    old_room = user_chat_context.get(username)
    user_chat_context[username] = new_room

    if new_room and new_room != old_room:
        if new_room.startswith('group_'):
            group_name = new_room.replace('group_', '')
            group = get_group_by_name(group_name)
            if group:
                for msg in get_group_messages(group['id']):
                    if msg['sender'] != username and not msg['is_read']:
                        update_group_message_read(msg['id'], True)
                        socketio.emit('message_status', {
                            'msg_id': msg['id'],
                            'status': 'read',
                            'room': new_room
                        }, room=new_room)
        elif new_room.startswith('channel_'):
            channel_name = new_room.replace('channel_', '')
            channel = get_channel_by_name(channel_name)
            if channel:
                for msg in get_channel_messages(channel['id']):
                    if msg['sender'] != username and not msg['is_read']:
                        update_channel_message_read(msg['id'], True)
                        socketio.emit('message_status', {
                            'msg_id': msg['id'],
                            'status': 'read',
                            'room': new_room
                        }, room=new_room)
        else:
            parts = new_room.split('_')
            if len(parts) == 2:
                sender = parts[0] if parts[1] == username else parts[1]
                unread_msgs = get_unread_messages(username, sender)
                for msg in unread_msgs:
                    mark_message_as_read(msg['id'])
                    socketio.emit('message_status', {
                        'msg_id': msg['id'],
                        'status': 'read'
                    }, room=new_room)


@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)


@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    sender = data['sender']
    emit('typing', {'sender': sender}, room=room, include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {}, room=room, include_self=False)


@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['msg']
    sender = session.get('username')
    parent_message_id = data.get('parent_message_id')
    message_type = data.get('message_type', 'text')
    audio_path = data.get('audio_path')
    print(f"DEBUG: Handling send_message from {sender} in room {room}: {message}")

    if parent_message_id:
        parent_msg = get_message_by_id(parent_message_id)
        parent_sender = parent_msg['sender'] if parent_msg else sender
        parent_message = parent_msg['message'] if parent_msg else message
    else:
        parent_sender = None
        parent_message = None

    if not room.startswith('channel_'):
        print(f"DEBUG: Emitting receive_message to room {room} (broadcast)")
        socketio.emit('receive_message', {
            'msg': message, 'sender': sender, 'room': room,
            'parent_message_id': parent_message_id,
            'parent_sender': parent_sender,
            'parent_message': parent_message,
            'message_type': message_type,
            'audio_path': audio_path
        }, room=room)

    if room.startswith('group_'):
        group_name = room.replace('group_', '')
        group = get_group_by_name(group_name)
        if group:
            msg_id = save_group_message(group['id'], sender, message, parent_message_id=parent_message_id, message_type=message_type, audio_path=audio_path)
            socketio.emit('message_status', {
                'msg_id': msg_id,
                'status': 'delivered'
            }, room=room)
            # Обновить список чатов для всех участников группы
            with get_db_connection() as conn:
                members = conn.execute("SELECT user_id FROM group_members WHERE group_id = ?", (group['id'],)).fetchall()
                for m in members:
                    uid = m['user_id']
                    uname = conn.execute("SELECT username FROM users WHERE id = ?", (uid,)).fetchone()['username']
                    if user_chat_context.get(uname) == room:
                        update_group_message_read(msg_id, True)
                    socketio.emit('update_chat_list', room=user_sids.get(uname))

    else:
        parts = room.split('_')
        if len(parts) == 2:
            u1, u2 = parts
            user1 = get_user_by_username(u1)
            user2 = get_user_by_username(u2)
            if user1 and user2:
                chat_id = get_or_create_chat(user1['id'], user2['id'])
                msg_id = save_message(chat_id, sender, message, parent_message_id, message_type, audio_path)
                mark_message_as_delivered(msg_id)
                socketio.emit('message_status', {
                    'msg_id': msg_id,
                    'status': 'delivered'
                }, room=room)

                # Если получатель в этом чате, отметить сообщение как прочитанное
                recipient = u2 if u1 == sender else u1
                if user_chat_context.get(recipient) == room:
                    mark_message_as_read(msg_id)

                # Обновить список чатов для отправителя и получателя
                socketio.emit('update_chat_list', room=user_sids.get(sender))
                socketio.emit('update_chat_list', room=user_sids.get(recipient))

                if recipient in user_sids:
                    recipient_sid = user_sids[recipient]
                    if user_chat_context.get(recipient) != room:
                        socketio.emit('push_notification', {
                            'sender': sender,
                            'message': message
                        }, room=recipient_sid)

    if room.startswith('channel_'):
        channel_name = room.replace('channel_', '')
        channel = get_channel_by_name(channel_name)
        if channel:
            user_role = get_user_channel_role(session.get('user_id'), channel['id'])
            if user_role == 'Admin':
                print(f"DEBUG: Emitting receive_message to channel room {room} (broadcast)")
                socketio.emit('receive_message', {
                    'msg': message, 'sender': sender, 'room': room,
                    'parent_message_id': parent_message_id,
                    'parent_sender': parent_sender,
                    'parent_message': parent_message,
                    'message_type': message_type,
                    'audio_path': audio_path
                }, room=room)
                msg_id = save_channel_message(channel['id'], sender, message, parent_message_id=parent_message_id, message_type=message_type, audio_path=audio_path)
                socketio.emit('message_status', {
                    'msg_id': msg_id,
                    'status': 'delivered'
                }, room=room)
                # Уведомить всех участников о новом сообщении
                with get_db_connection() as conn:
                    members = conn.execute("SELECT user_id FROM channel_members WHERE channel_id = ?", (channel['id'],)).fetchall()
                    for m in members:
                        uid = m['user_id']
                        uname = conn.execute("SELECT username FROM users WHERE id = ?", (uid,)).fetchone()['username']
                        if uname != sender:  # Не уведомлять отправителя
                            recipient_sid = user_sids.get(uname)
                            if recipient_sid:
                                if user_chat_context.get(uname) != room:
                                    socketio.emit('push_notification', {
                                        'sender': sender,
                                        'message': message
                                    }, room=recipient_sid)
                        socketio.emit('update_chat_list', room=user_sids.get(uname))
            else:
                emit('error', {'msg': 'Только администраторы могут отправлять сообщения в канале'})
        else:
            emit('error', {'msg': 'Канал не найден'})


@socketio.on('create_group')
def handle_create_group(data):
    group_name = data['name']
    members = data.get('members', [])
    creator = session.get('username')
    if get_group_by_name(group_name):
        emit('group_error', {'msg': 'Группа уже существует'})
        return
    group_id = create_group(group_name, creator)
    add_user_to_group(group_id, session['user_id'])
    for member_username in members:
        member = get_user_by_username(member_username)
        if member:
            add_user_to_group(group_id, member['id'])
    emit('group_created', {'name': group_name}, broadcast=True)


@socketio.on('delete_message')
def handle_delete_message(data):
    msg_id = data['msg_id']
    room = data['room']
    sender = session.get('username')

    # Проверяем: это его сообщение?
    if room.startswith('group_'):
        msg = next((m for m in get_group_messages(get_group_by_name(room.replace('group_', ''))['id']) if m['id'] == msg_id), None)
        is_group = True
    elif room.startswith('channel_'):
        channel_name = room.replace('channel_', '')
        channel = get_channel_by_name(channel_name)
        if channel:
            msg = next((m for m in get_channel_messages(channel['id']) if m['id'] == msg_id), None)
            is_group = False  # Для delete_message, канал не group
        else:
            msg = None
    else:
        parts = room.split('_')
        chat_id = get_or_create_chat(get_user_by_username(parts[0])['id'], get_user_by_username(parts[1])['id'])
        msg = next((m for m in get_messages(chat_id) if m['id'] == msg_id), None)
        is_group = False

    if msg and msg['sender'] == sender:
        if room.startswith('channel_'):
            # Для каналов удаляем из channel_messages
            with get_db_connection() as conn:
                conn.execute("DELETE FROM channel_messages WHERE id = ?", (msg_id,))
                conn.commit()
        else:
            delete_message(msg_id, is_group)
        emit('message_deleted', {'msg_id': msg_id}, room=room)


@socketio.on('edit_message')
def handle_edit_message(data):
    msg_id = data['msg_id']
    new_msg = data['new_msg']
    room = data['room']
    sender = session.get('username')

    # Проверяем: это его сообщение?
    if room.startswith('group_'):
        msg = next((m for m in get_group_messages(get_group_by_name(room.replace('group_', ''))['id']) if m['id'] == msg_id), None)
        if msg and msg['sender'] == sender:
            with get_db_connection() as conn:
                conn.execute("UPDATE group_messages SET message = ?, edited = 1 WHERE id = ?", (new_msg, msg_id))
                conn.commit()
    elif room.startswith('channel_'):
        channel_name = room.replace('channel_', '')
        channel = get_channel_by_name(channel_name)
        if channel:
            msg = next((m for m in get_channel_messages(channel['id']) if m['id'] == msg_id), None)
            if msg and msg['sender'] == sender:
                with get_db_connection() as conn:
                    conn.execute("UPDATE channel_messages SET message = ?, edited = 1 WHERE id = ?", (new_msg, msg_id))
                    conn.commit()
    else:
        parts = room.split('_')
        chat_id = get_or_create_chat(get_user_by_username(parts[0])['id'], get_user_by_username(parts[1])['id'])
        msg = next((m for m in get_messages(chat_id) if m['id'] == msg_id), None)
        if msg and msg['sender'] == sender:
            with get_db_connection() as conn:
                conn.execute("UPDATE messages SET message = ?, edited = 1 WHERE id = ?", (new_msg, msg_id))
                conn.commit()

    if msg and msg['sender'] == sender:
        emit('message_edited', {'msg_id': msg_id, 'new_msg': new_msg}, room=room)


@socketio.on('pin_message')
def handle_pin_message(data):
    group_name = data['group']
    msg_id = data['msg_id']
    sender = session.get('username')
    group_id = get_group_by_name(group_name)['id']
    save_pinned_message(group_id, msg_id)
    msg = next((m for m in get_group_messages(group_id) if m['id'] == msg_id), None)
    msg_text = msg['message'] if msg else 'Сообщение'
    emit('pinned_message', {'msg': msg_text, 'group': group_name}, broadcast=True)


@socketio.on('unpin_message')
def handle_unpin_message(data):
    group_name = data['group']
    remove_pinned_message(get_group_by_name(group_name)['id'])
    emit('unpinned_message', {'group': group_name}, broadcast=True)


@socketio.on('new_chat')
def handle_new_chat(data):
    other_user = data['with']
    if other_user in user_sids:
        socketio.emit('new_chat', {'with': session['username']}, room=user_sids[other_user])


@socketio.on('delete_chat_socket')
def handle_delete_chat_socket(data):
    other_user = data['with']
    if other_user in user_sids:
        socketio.emit('chat_deleted', {'with': session['username']}, room=user_sids[other_user])






@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user = get_user_by_username(username)
    if not user:
        session.clear()
        return redirect(url_for('login'))
    print(f"DEBUG: Profile for {username}, avatar: {user.get('avatar')}")
    # Преобразовать registration_date в datetime объект
    user_dict = dict(user)
    if user_dict.get('registration_date'):
        user_dict['registration_date'] = datetime.datetime.fromisoformat(user_dict['registration_date'])
    timestamp = int(time.time())
    is_owner = True
    is_following_user = None
    followers = get_followers(session['user_id'])
    following = get_following(session['user_id'])
    posts = get_posts_for_user(session['user_id'])
    reposts = get_reposts_for_user(session['user_id'])
    feed = get_feed(session['user_id'])
    return render_template('profile.html', user=user_dict, is_owner=is_owner, is_following=is_following_user, followers=followers, following=following, posts=posts, reposts=reposts, feed=feed, timestamp=timestamp)


@app.route('/profile/<username>')
def user_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_username(username)
    if not user:
        return "Пользователь не найден", 404
    # Преобразовать registration_date в datetime объект
    user_dict = dict(user)
    if user_dict.get('registration_date'):
        user_dict['registration_date'] = datetime.datetime.fromisoformat(user_dict['registration_date'])
    is_owner = user['id'] == session['user_id']
    is_following_user = is_following(session['user_id'], user['id']) if not is_owner else None
    followers = get_followers(user['id'])
    following = get_following(user['id'])
    posts = get_posts_for_user(user['id'])
    reposts = get_reposts_for_user(user['id'])
    timestamp = int(time.time())
    return render_template('profile.html', user=user_dict, is_owner=is_owner, is_following=is_following_user, followers=followers, following=following, posts=posts, reposts=reposts, timestamp=timestamp)


@app.route('/update_username', methods=['POST'])
def update_username():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    new_username = request.form['username'].strip()
    if not new_username or len(new_username) < 3:
        return jsonify({'success': False, 'error': 'Имя должно быть не менее 3 символов'})
    if get_user_by_username(new_username):
        return jsonify({'success': False, 'error': 'Имя занято'})
    
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, session['user_id']))
        conn.commit()
    
    session['username'] = new_username
    return jsonify({'success': True, 'username': new_username})


@app.route('/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    
    user = get_user_by_username(session['username'])
    if not verify_password(old_password, user['password']):
        return jsonify({'success': False, 'error': 'Старый пароль неверен'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Пароль должен быть не менее 6 символов'})
    
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(new_password), session['user_id']))
        conn.commit()
    
    return jsonify({'success': True})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    city = request.form.get('city', '').strip()
    bio_short = request.form.get('bio_short', '').strip()
    country = request.form.get('country', '').strip()
    languages = request.form.get('languages', '').strip()
    bio_full = request.form.get('bio_full', '').strip()
    hobbies = request.form.get('hobbies', '').strip()
    status = request.form.get('status', '').strip()
    banner_color = request.form.get('banner_color', '').strip()

    # Handle banner photo upload
    banner_photo = None
    if 'banner_photo' in request.files:
        file = request.files['banner_photo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_banner_{int(time.time() * 1000)}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            banner_photo = filename
    print(f"DEBUG: update_profile - banner_photo in files: {'banner_photo' in request.files}, banner_photo: {banner_photo}, banner_color: {banner_color}")

    # Build dynamic UPDATE query
    sql = "UPDATE users SET city = ?, bio_short = ?, country = ?, languages = ?, bio_full = ?, hobbies = ?, status = ?, banner_color = ?"
    params = (city, bio_short, country, languages, bio_full, hobbies, status, banner_color)

    if banner_photo is not None:
        sql += ", banner_photo = ?"
        params += (banner_photo,)

    sql += " WHERE id = ?"
    params += (session['user_id'],)

    with get_db_connection() as conn:
        conn.execute(sql, params)
        conn.commit()

    return jsonify({'success': True})

@app.route('/user_online_status/<username>')
def user_online_status(username):
    user = get_user_by_username(username)
    if not user:
        return jsonify({'online': False, 'last_seen': None}), 404

    # ЕДИНСТВЕННЫЙ способ определить онлайн статус - проверка подключения через Socket.IO
    # Активные сессии в базе данных не учитываются, так как они могут оставаться после выхода
    if username in online_users:
        return jsonify({'online': True, 'last_seen': None})

    # Если пользователь не подключен через Socket.IO, он оффлайн
    # Получаем время последнего выхода для отображения "был в сети"
    with get_db_connection() as conn:
        last_session = conn.execute("""
            SELECT logout_time FROM user_sessions
            WHERE user_id = ? AND logout_time IS NOT NULL
            ORDER BY logout_time DESC LIMIT 1
        """, (user['id'],)).fetchone()

        last_seen = last_session['logout_time'] if last_session else None

    return jsonify({'online': False, 'last_seen': last_seen})

@app.route('/get_stats/<username>')
def get_stats(username):
    user = get_user_by_username(username)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    user_id = user['id']

    with get_db_connection() as conn:
        # Messages count
        msg_count = conn.execute("SELECT COUNT(*) FROM messages WHERE sender = ?", (username,)).fetchone()[0]

        # Likes count
        likes_count = conn.execute("SELECT COUNT(*) FROM likes WHERE user_id = ?", (user_id,)).fetchone()[0]

        # Average time
        sessions = conn.execute("SELECT login_time, logout_time FROM user_sessions WHERE user_id = ? AND logout_time IS NOT NULL", (user_id,)).fetchall()
        total_time = 0
        for s in sessions:
            login = datetime.datetime.fromisoformat(s['login_time'])
            logout = datetime.datetime.fromisoformat(s['logout_time'])
            total_time += (logout - login).total_seconds()
        avg_time = total_time / len(sessions) if sessions else 0
        avg_hours = int(avg_time // 3600)
        avg_mins = int((avg_time % 3600) // 60)

        # Peak hour
        peak_hour_data = conn.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM messages WHERE sender = ?
            GROUP BY hour ORDER BY count DESC LIMIT 1
        """, (username,)).fetchone()
        peak_hour = peak_hour_data['hour'] if peak_hour_data else None

        # Peak day
        peak_day_data = conn.execute("""
            SELECT strftime('%w', timestamp) as day, COUNT(*) as count
            FROM messages WHERE sender = ?
            GROUP BY day ORDER BY count DESC LIMIT 1
        """, (username,)).fetchone()
        days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        peak_day = days[int(peak_day_data['day'])] if peak_day_data else None

    return jsonify({
        'messages': msg_count,
        'likes': likes_count,
        'avg_time': f'{avg_hours}ч {avg_mins}м',
        'peak_hour': peak_hour,
        'peak_day': peak_day
    })

@app.route('/user_stats/<username>')
def user_stats(username):
    user = get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404

    user_id = user['id']

    with get_db_connection() as conn:
        # Total posts
        total_posts = conn.execute("SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)).fetchone()[0]

        # Total likes received
        total_likes = conn.execute("SELECT COUNT(*) FROM likes WHERE post_id IN (SELECT id FROM posts WHERE user_id = ?)", (user_id,)).fetchone()[0]

        # Total reposts
        total_reposts = conn.execute("SELECT COUNT(*) FROM reposts WHERE user_id = ?", (user_id,)).fetchone()[0]

        # Followers count
        followers = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE following_id = ?", (user_id,)).fetchone()[0]

        # Following count
        following = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE follower_id = ?", (user_id,)).fetchone()[0]

        # Days registered
        # Try to get registration_date, fallback to 0 if column doesn't exist
        try:
            result = conn.execute("SELECT registration_date FROM users WHERE id = ?", (user_id,)).fetchone()
            registration_date = result['registration_date'] if result else None
            if registration_date:
                reg_date = datetime.datetime.fromisoformat(registration_date)
                days_registered = (datetime.datetime.now() - reg_date).days
            else:
                days_registered = 0
        except sqlite3.OperationalError:
            # Column doesn't exist, use default
            days_registered = 0

        # Posts with images percentage
        posts_with_images_percentage = get_posts_with_images_percentage(user_id)

    return jsonify({
        'success': True,
        'stats': {
            'total_posts': total_posts,
            'total_likes': total_likes,
            'total_reposts': total_reposts,
            'followers': followers,
            'following': following,
            'days_registered': days_registered,
            'posts_with_images': posts_with_images_percentage
        }
    })


@app.route('/user_detailed_stats/<username>')
def user_detailed_stats(username):
    user = get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404

    user_id = user['id']

    # Get detailed stats
    top_posts = get_top_posts(user_id)
    monthly_activity = get_monthly_activity(user_id)
    followers_growth = get_followers_growth(user_id)

    return jsonify({
        'success': True,
        'detailed_stats': {
            'top_posts': top_posts,
            'monthly_activity': monthly_activity,
            'followers_growth': followers_growth
        }
    })

@app.route('/feed_data')
def feed_data():
    print(f"feed_data called, session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("No user_id in session")
        return jsonify({'feed': []})
    user_id = session['user_id']
    print(f"Getting feed for user_id: {user_id}")
    try:
        feed = get_feed(user_id)
        print(f"Feed length: {len(feed)}")
        feed_data = []
        for p in feed:
            print(f"Processing post {p['id']} by {p['username']}")
            user_info = get_user_by_username(p['username'])
            avatar = user_info['avatar'] if user_info else None
            # Получить последние 3 комментария
            comments = get_comments_for_post(p['id'])[:3]
            # Получить реакции для поста
            reactions = get_reactions_for_post(p['id'])
            # Группировать реакции по эмодзи
            reactions_grouped = {}
            for r in reactions:
                emoji = r['emoji']
                if emoji not in reactions_grouped:
                    reactions_grouped[emoji] = []
                reactions_grouped[emoji].append({'username': r['username'], 'user_id': r['user_id']})
            feed_data.append({
                'id': p['id'],
                'username': p['username'],
                'content': p['content'],
                'image_url': p['image_url'],
                'created_at': p['created_at'],
                'likes_count': p['likes_count'],
                'comments_count': p['comments_count'],
                'reposts_count': p['reposts_count'],
                'is_liked': is_liked(user_id, p['id']),
                'is_reposted': is_reposted(user_id, p['id']),
                'is_reacted': is_reacted(user_id, p['id']),
                'avatar': avatar,
                'comments': comments,
                'reactions': reactions_grouped
            })
        print(f"Returning feed_data with {len(feed_data)} items")
        return jsonify({'feed': feed_data})
    except Exception as e:
        print(f"Error in feed_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/feed')
def feed_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    feed_posts = get_feed(session['user_id'])
    return render_template('feed.html', feed=feed_posts)


@app.route('/user_activity_data/<username>')
def user_activity_data(username):
    user = get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404

    user_id = user['id']

    with get_db_connection() as conn:
        # Активность по дням недели (0=воскресенье, 6=суббота)
        daily_data = conn.execute("""
            SELECT strftime('%w', timestamp) as day, COUNT(*) as count
            FROM messages WHERE sender = ?
            GROUP BY day ORDER BY day
        """, (username,)).fetchall()

        # Преобразуем в массив [пн, вт, ср, чт, пт, сб, вс]
        daily = [0] * 7
        for row in daily_data:
            day_index = int(row['day'])
            # Переставляем: 0=вс -> 6, 1=пн -> 0, ..., 6=сб -> 5
            if day_index == 0:  # воскресенье
                daily[6] = row['count']
            else:
                daily[day_index - 1] = row['count']

        # Активность по часам
        hourly_data = conn.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM messages WHERE sender = ?
            GROUP BY hour ORDER BY hour
        """, (username,)).fetchall()

        hourly = [0] * 24
        for row in hourly_data:
            hour = int(row['hour'])
            hourly[hour] = row['count']

    return jsonify({
        'success': True,
        'daily': daily,
        'hourly': hourly
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/photo/<filename>')
def serve_photo(filename):
    return send_from_directory('photo', filename)

@app.route('/get_audio/<filename>')
def get_audio(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), filename)

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    print(f"DEBUG: upload_avatar called, method: {request.method}, headers: {dict(request.headers)}")
    print(f"DEBUG: session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("DEBUG: No user_id in session, returning error")
        return jsonify({'success': False, 'error': 'Не авторизован'})

    print(f"DEBUG: request.files keys: {list(request.files.keys())}")
    if 'avatar' not in request.files:
        print("DEBUG: 'avatar' not in request.files, files: {request.files}")
        return jsonify({'success': False, 'error': 'Файл не найден'})

    file = request.files['avatar']
    print(f"DEBUG: file object: {file}, filename: {file.filename}, content_type: {file.content_type}, content_length: {file.content_length}")
    if file.filename == '':
        print("DEBUG: file.filename is empty")
        return jsonify({'success': False, 'error': 'Файл не выбран'})

    print(f"DEBUG: checking allowed_file for {file.filename}")
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['user_id']}_avatar_{int(time.time() * 1000)}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"DEBUG: generated filename: {filename}, full path: {filepath}")
        print(f"DEBUG: uploads folder exists: {os.path.exists(app.config['UPLOAD_FOLDER'])}, is writable: {os.access(app.config['UPLOAD_FOLDER'], os.W_OK)}")
        try:
            file.save(filepath)
            print(f"DEBUG: Avatar saved successfully to {filepath}")
            print(f"DEBUG: file exists after save: {os.path.exists(filepath)}, size: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")
        except Exception as e:
            print(f"DEBUG: Error saving file: {e}, type: {type(e)}")
            return jsonify({'success': False, 'error': 'Ошибка сохранения файла'})

        # Update DB
        try:
            with get_db_connection() as conn:
                print(f"DEBUG: updating DB for user {session['user_id']} with avatar {filename}")
                conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (filename, session['user_id']))
                conn.commit()
                print(f"DEBUG: Avatar updated in DB successfully")
                # Verify update
                updated = conn.execute("SELECT avatar FROM users WHERE id = ?", (session['user_id'],)).fetchone()
                print(f"DEBUG: verified avatar in DB: {updated['avatar'] if updated else 'None'}")
        except Exception as e:
            print(f"DEBUG: Error updating DB: {e}, type: {type(e)}")
            return jsonify({'success': False, 'error': 'Ошибка обновления базы данных'})

        print(f"DEBUG: upload_avatar completed successfully, returning filename: {filename}")
        return jsonify({'success': True, 'filename': filename})
    else:
        print("DEBUG: File not allowed, filename: {file.filename}, allowed: {allowed_file(file.filename)}")
        return jsonify({'success': False, 'error': 'Недопустимый файл'})

@app.route('/delete_avatar', methods=['POST'])
def delete_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})

    try:
        # Получаем текущий аватар
        with get_db_connection() as conn:
            result = conn.execute("SELECT avatar FROM users WHERE id = ?", (session['user_id'],)).fetchone()
            current_avatar = result['avatar'] if result else None

        # Удаляем файл, если он существует
        if current_avatar:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_avatar)
            if os.path.exists(filepath):
                os.remove(filepath)

        # Обновляем базу данных
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET avatar = NULL WHERE id = ?", (session['user_id'],))
            conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting avatar: {e}")
        return jsonify({'success': False, 'error': 'Ошибка при удалении аватара'})


@app.route('/upload_voice', methods=['POST'])
def upload_voice():
    print("DEBUG: upload_voice called")
    print(f"DEBUG: session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("DEBUG: No session user_id")
        return jsonify({'success': False, 'error': 'Не авторизован'})

    user_id = request.form.get('user_id')
    target_id = request.form.get('target_id')
    message_type = request.form.get('message_type')
    print(f"DEBUG: user_id: {user_id}, target_id: {target_id}, message_type: {message_type}")

    if not user_id or not target_id or message_type != 'voice':
        print("DEBUG: Invalid parameters")
        return jsonify({'success': False, 'error': 'Неверные параметры'})

    if 'file' not in request.files:
        print("DEBUG: No file in request.files")
        return jsonify({'success': False, 'error': 'Файл не найден'})

    file = request.files['file']
    print(f"DEBUG: file.filename: {file.filename}")
    if file.filename == '':
        print("DEBUG: Empty filename")
        return jsonify({'success': False, 'error': 'Файл не выбран'})

    print(f"DEBUG: allowed_audio_file check: {allowed_audio_file(file.filename)}")
    if file and allowed_audio_file(file.filename):
        filename = secure_filename(f"{session['user_id']}_{int(time.time() * 1000)}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
        print(f"DEBUG: Saving to {filepath}")
        try:
            file.save(filepath)
            print(f"DEBUG: File saved successfully, size: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")
        except Exception as e:
            print(f"DEBUG: Error saving file: {e}")
            return jsonify({'success': False, 'error': 'Ошибка сохранения файла'})
        audio_path = f"audio/{filename}"
        print(f"DEBUG: Returning success with audio_path: {audio_path}")
        return jsonify({'success': True, 'audio_path': audio_path})
    else:
        print("DEBUG: Invalid file")
        return jsonify({'success': False, 'error': 'Недопустимый файл'})

@app.route('/upload_banner', methods=['POST'])
def upload_banner():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})

    if 'banner_photo' not in request.files:
        return jsonify({'success': False, 'error': 'Файл не найден'})

    file = request.files['banner_photo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Файл не выбран'})

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['user_id']}_banner_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Update DB
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET banner_photo = ? WHERE id = ?", (filename, session['user_id']))
            conn.commit()

        return jsonify({'success': True, 'filename': filename})
    else:
        return jsonify({'success': False, 'error': 'Недопустимый файл'})


# === Социальная сеть ===

@app.route('/follow/<username>', methods=['POST'])
def follow(username):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    user = get_user_by_username(username)
    if not user or user['id'] == session['user_id']:
        return jsonify({'success': False, 'error': 'Невозможно подписаться'})
    follow_user(session['user_id'], user['id'])
    return jsonify({'success': True})


@app.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    user = get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    unfollow_user(session['user_id'], user['id'])
    return jsonify({'success': True})


@app.route('/create_post', methods=['POST'])
def create_post_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Контент обязателен'})

    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_{int(time.time() * 1000)}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = filename

    create_post(session['user_id'], content, image_url)
    return jsonify({'success': True})


@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    like_post(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/unlike/<int:post_id>', methods=['POST'])
def unlike(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    unlike_post(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Комментарий обязателен'})
    add_comment(session['user_id'], post_id, content)
    return jsonify({'success': True})

@app.route('/profile_comment/<int:profile_user_id>', methods=['POST'])
def profile_comment(profile_user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Комментарий обязателен'})
    add_profile_comment(session['user_id'], profile_user_id, content)
    return jsonify({'success': True})

@app.route('/profile_comments/<int:profile_user_id>')
def get_profile_comments(profile_user_id):
    comments = get_profile_comments_for_user(profile_user_id)
    return jsonify({'comments': comments})

@app.route('/comments/<int:post_id>')
def get_comments_route(post_id):
    comments = get_comments_for_post(post_id)
    return jsonify({'comments': comments})


@app.route('/message_comment/<int:message_id>', methods=['POST'])
def message_comment(message_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Комментарий обязателен'})
    add_message_comment(message_id, session['user_id'], content)
    return jsonify({'success': True})


@app.route('/message_comments/<int:message_id>')
def get_message_comments_route(message_id):
    comments = get_comments_for_message(message_id)
    return jsonify({'comments': comments})


@app.route('/repost/<int:post_id>', methods=['POST'])
def repost_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    repost(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/unrepost/<int:post_id>', methods=['POST'])
def unrepost_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    unrepost(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/reply/<int:post_id>/<int:parent_comment_id>', methods=['POST'])
def reply_route(post_id, parent_comment_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Ответ обязателен'})
    add_reply(session['user_id'], post_id, parent_comment_id, content)
    return jsonify({'success': True})


@app.route('/add_reaction/<int:post_id>', methods=['POST'])
def add_reaction_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    emoji = request.form.get('emoji', '').strip()
    if not emoji:
        return jsonify({'success': False, 'error': 'Эмодзи обязателен'})
    add_reaction(session['user_id'], post_id, emoji)
    return jsonify({'success': True})


@app.route('/remove_reaction/<int:post_id>', methods=['POST'])
def remove_reaction_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    remove_reaction(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/pin/<int:post_id>', methods=['POST'])
def pin_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    pin_post(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/unpin/<int:post_id>', methods=['POST'])
def unpin_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    unpin_post(session['user_id'], post_id)
    return jsonify({'success': True})


@app.route('/forward/<int:post_id>', methods=['POST'])
def forward_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    recipient = request.form.get('recipient', '').strip()
    if not recipient:
        return jsonify({'success': False, 'error': 'Получатель обязателен'})

    # Получить пост
    with get_db_connection() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post:
            return jsonify({'success': False, 'error': 'Пост не найден'})

    # Отправить в чат
    recipient_user = get_user_by_username(recipient)
    if not recipient_user:
        return jsonify({'success': False, 'error': 'Получатель не найден'})

    chat_id = get_or_create_chat(session['user_id'], recipient_user['id'])
    message = f"Пересылка поста: {post['content']}"
    if post['image_url']:
        message += f" [Изображение: {post['image_url']}]"
    msg_id = save_message(chat_id, session['username'], message)

    # Уведомить через socket
    socketio.emit('receive_message', {
        'msg': message,
        'sender': session['username'],
        'room': f"{min(session['username'], recipient)}_{max(session['username'], recipient)}"
    }, room=f"{min(session['username'], recipient)}_{max(session['username'], recipient)}")

    return jsonify({'success': True})


@app.route('/forward_message', methods=['POST'])
def forward_message_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    message_id = int(request.form.get('message_id'))
    recipient = request.form.get('recipient', '').strip()
    print(f"Forwarding message {message_id} to {recipient}")
    if not recipient:
        return jsonify({'success': False, 'error': 'Получатель обязателен'})

    # Получить сообщение
    with get_db_connection() as conn:
        msg = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone() or \
              conn.execute("SELECT * FROM group_messages WHERE id = ?", (message_id,)).fetchone() or \
              conn.execute("SELECT * FROM channel_messages WHERE id = ?", (message_id,)).fetchone()
        print(f"Retrieved message: {dict(msg) if msg else None}")
        if not msg:
            return jsonify({'success': False, 'error': 'Сообщение не найдено'})

        # Определить получателя
        user_recipient = conn.execute("SELECT id FROM users WHERE username = ?", (recipient,)).fetchone()
        group_recipient = conn.execute("SELECT id FROM groups WHERE name = ?", (recipient,)).fetchone()
        channel_recipient = conn.execute("SELECT id FROM channels WHERE name = ?", (recipient,)).fetchone()
        print(f"user_recipient: {dict(user_recipient) if user_recipient else None}, group_recipient: {dict(group_recipient) if group_recipient else None}, channel_recipient: {dict(channel_recipient) if channel_recipient else None}")

    if user_recipient:
        chat_id = get_or_create_chat(session['user_id'], user_recipient['id'])
        print(f"Created chat_id: {chat_id}")
        # Пересылаем как обычное сообщение с parent_message_id для отображения оригинального отправителя
        msg_id = save_message(chat_id, session['username'], msg['message'], parent_message_id=message_id)
        print(f"Forwarded to user chat {chat_id}, new msg_id {msg_id}")
        # Уведомить через socket с данными для отображения
        room = f"{min(session['username'], recipient)}_{max(session['username'], recipient)}"
        socketio.emit('receive_message', {
            'msg': msg['message'],
            'sender': session['username'],
            'room': room,
            'parent_message_id': message_id,
            'parent_sender': msg['sender'],
            'parent_message': msg['message'],
            'is_forward': True
        }, room=room)
    elif group_recipient:
        group_id = group_recipient['id']
        # Проверить членство
        with get_db_connection() as conn:
            member = conn.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, session['user_id'])).fetchone()
        print(f"Member check: {dict(member) if member else None}")
        if not member:
            return jsonify({'success': False, 'error': 'Вы не в этой группе'})
        # Пересылаем как обычное сообщение с parent_message_id
        msg_id = save_group_message(group_id, session['username'], msg['message'], parent_message_id=message_id)
        print(f"Forwarded to group {group_id}, new msg_id {msg_id}")
        # Уведомить через socket
        room = f"group_{recipient}"
        socketio.emit('receive_message', {
            'msg': msg['message'],
            'sender': session['username'],
            'room': room,
            'parent_message_id': message_id,
            'parent_sender': msg['sender'],
            'parent_message': msg['message'],
            'is_forward': True
        }, room=room)
    elif channel_recipient:
        channel_id = channel_recipient['id']
        # Проверить членство
        with get_db_connection() as conn:
            member = conn.execute("SELECT * FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel_id, session['user_id'])).fetchone()
        print(f"Channel member check: {dict(member) if member else None}")
        if not member:
            return jsonify({'success': False, 'error': 'Вы не в этом канале'})
        # Пересылаем как обычное сообщение с parent_message_id
        msg_id = save_channel_message(channel_id, session['username'], msg['message'], parent_message_id=message_id)
        print(f"Forwarded to channel {channel_id}, new msg_id {msg_id}")
        # Уведомить через socket
        room = f"channel_{recipient}"
        socketio.emit('receive_message', {
            'msg': msg['message'],
            'sender': session['username'],
            'room': room,
            'parent_message_id': message_id,
            'parent_sender': msg['sender'],
            'parent_message': msg['message'],
            'is_forward': True
        }, room=room)
    else:
        return jsonify({'success': False, 'error': 'Получатель не найден'})

    return jsonify({'success': True})


@app.route('/edit_post/<int:post_id>', methods=['POST'])
def edit_post_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Контент обязателен'})
    try:
        edit_post(post_id, session['user_id'], content=content)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post_route(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    try:
        delete_post(post_id, session['user_id'])
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/delete_chat/<int:chat_id>', methods=['POST'])
def delete_chat_route(chat_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    with get_db_connection() as conn:
        chat = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if not chat or (chat['user1_id'] != session['user_id'] and chat['user2_id'] != session['user_id']):
            return jsonify({'success': False, 'error': 'Нет доступа'})
    delete_chat(chat_id)
    other_user_id = chat['user2_id'] if session['user_id'] == chat['user1_id'] else chat['user1_id']
    with get_db_connection() as conn:
        other_username = conn.execute("SELECT username FROM users WHERE id = ?", (other_user_id,)).fetchone()['username']
    socketio.emit('chat_deleted', {'with': session['username']}, room=user_sids.get(other_username, None))
    return jsonify({'success': True})


@app.route('/delete_group/<group_name>', methods=['POST'])
def delete_group_route(group_name):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    group = get_group_by_name(group_name)
    if not group:
        return jsonify({'success': False, 'error': 'Группа не найдена'})
    with get_db_connection() as conn:
        member = conn.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group['id'], session['user_id'])).fetchone()
        if not member:
            return jsonify({'success': False, 'error': 'Не в группе'})
    delete_group(group['id'])
    return jsonify({'success': True})


@app.route('/chat_list')
def chat_list():
    if 'user_id' not in session:
        return jsonify({'user_chats': [], 'user_groups': [], 'user_channels': []})
    user_id = session['user_id']
    user_chats = get_user_chats(user_id)
    user_groups = get_groups_for_user(user_id)
    user_channels = get_channels_for_user(user_id)
    print(f"chat_list for user_id {user_id}: channels {user_channels}")
    return jsonify({'user_chats': user_chats, 'user_groups': user_groups, 'user_channels': user_channels})

@app.route('/create_group', methods=['POST'])
def create_group_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    group_name = request.form.get('group_name', '').strip()
    description = request.form.get('description', '').strip()
    if not group_name:
        return jsonify({'success': False, 'error': 'Название группы обязательно'})
    if get_group_by_name(group_name):
        return jsonify({'success': False, 'error': 'Группа с таким названием уже существует'})
    group_id = create_group(group_name, session['username'], description=description)
    add_user_to_group(group_id, session['user_id'])
    # Уведомить через socket
    socketio.emit('group_created', {'name': group_name}, broadcast=True)
    return jsonify({'success': True})

@app.route('/search')
def search():
    print(f"search called, session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("No session in search")
        return jsonify({'users': [], 'groups': [], 'channels': []})
    query = request.args.get('q', '').strip()
    print(f"Query: '{query}'")
    if not query:
        return jsonify({'users': [], 'groups': [], 'channels': []})
    try:
        with get_db_connection() as conn:
            users = conn.execute("SELECT id, username, avatar FROM users WHERE LOWER(username) LIKE LOWER(?) AND id != ?", (f'%{query}%', session['user_id'])).fetchall()
            groups = conn.execute("SELECT id, name FROM groups WHERE LOWER(name) LIKE LOWER(?)", (f'%{query}%',)).fetchall()
            channels = conn.execute("SELECT id, name FROM channels WHERE LOWER(name) LIKE LOWER(?)", (f'%{query}%',)).fetchall()
            print(f"Found users: {[dict(u) for u in users]}, groups: {[dict(g) for g in groups]}, channels: {[dict(c) for c in channels]}")
        return jsonify({'users': [dict(u) for u in users], 'groups': [dict(g) for g in groups], 'channels': [dict(c) for c in channels]})
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# === Каналы ===

@app.route('/create_channel', methods=['POST'])
def create_channel_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    description = request.form.get('description', '').strip()
    is_private = request.form.get('is_private', 'false').lower() == 'true'
    if not channel_name:
        return jsonify({'success': False, 'error': 'Название канала обязательно'})
    if get_channel_by_name(channel_name):
        return jsonify({'success': False, 'error': 'Канал с таким названием уже существует'})
    try:
        channel_id = create_channel(channel_name, session['username'], description, is_private)
        socketio.emit('channel_created', {'name': channel_name})
        return jsonify({'success': True, 'channel_id': channel_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/channels')
def get_channels():
    if 'user_id' not in session:
        return jsonify({'channels': []})
    channels = get_channels_for_user(session['user_id'])
    return jsonify({'channels': channels})


@app.route('/add_member_to_channel', methods=['POST'])
def add_member_to_channel_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    member_username = request.form.get('member_username', '').strip()
    if not channel_name or not member_username:
        return jsonify({'success': False, 'error': 'Название канала и имя участника обязательны'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'success': False, 'error': 'Канал не найден'})
    member = get_user_by_username(member_username)
    if not member:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    # Проверить, что пользователь имеет права (админ)
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        add_user_to_channel(channel['id'], member['id'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/remove_member_from_channel', methods=['POST'])
def remove_member_from_channel_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    member_username = request.form.get('member_username', '').strip()
    if not channel_name or not member_username:
        return jsonify({'success': False, 'error': 'Название канала и имя участника обязательны'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'success': False, 'error': 'Канал не найден'})
    member = get_user_by_username(member_username)
    if not member:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    # Проверить права
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        remove_user_from_channel(channel['id'], member['id'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/create_channel_role', methods=['POST'])
def create_channel_role_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    role_name = request.form.get('role_name', '').strip()
    permissions = request.form.get('permissions', '').strip()
    if not channel_name or not role_name:
        return jsonify({'success': False, 'error': 'Название канала и роль обязательны'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'success': False, 'error': 'Канал не найден'})
    # Проверить права
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        role_id = create_channel_role(channel['id'], role_name, permissions)
        return jsonify({'success': True, 'role_id': role_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/assign_role_to_member', methods=['POST'])
def assign_role_to_member_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    member_username = request.form.get('member_username', '').strip()
    role_name = request.form.get('role_name', '').strip()
    if not channel_name or not member_username or not role_name:
        return jsonify({'success': False, 'error': 'Все поля обязательны'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'success': False, 'error': 'Канал не найден'})
    member = get_user_by_username(member_username)
    if not member:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    # Проверить, что нельзя изменить роль создателя
    if member_username == channel['creator']:
        return jsonify({'success': False, 'error': 'Нельзя изменить роль создателя канала'})
    # Найти role_id по name
    with get_db_connection() as conn:
        role = conn.execute("SELECT id FROM channel_roles WHERE channel_id = ? AND role_name = ?", (channel['id'], role_name)).fetchone()
        if not role:
            return jsonify({'success': False, 'error': 'Роль не найдена'})
        # Проверить права
        user_role = conn.execute("SELECT role_id FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_id'] != 1:
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        # Обновить role_id для участника
        with get_db_connection() as conn:
            conn.execute("UPDATE channel_members SET role_id = ? WHERE channel_id = ? AND user_id = ?", (role['id'], channel['id'], member['id']))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/create_channel_invite', methods=['POST'])
def create_channel_invite_route():
    print("DEBUG: create_channel_invite called")
    print(f"DEBUG: Request method: {request.method}, form data: {dict(request.form)}")
    if 'user_id' not in session:
        print("DEBUG: No user_id in session")
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel_name = request.form.get('channel_name', '').strip()
    expires_days = request.form.get('expires_days')
    max_uses = request.form.get('max_uses')
    print(f"DEBUG: expires_days={expires_days}, max_uses={max_uses}")
    if not channel_name:
        return jsonify({'success': False, 'error': 'Название канала обязательно'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        print(f"DEBUG: Channel {channel_name} not found")
        return jsonify({'success': False, 'error': 'Канал не найден'})
    # Проверить права
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            print(f"DEBUG: No admin rights for user {session['user_id']}")
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        expires_at = None
        if expires_days:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=int(expires_days))
            print(f"DEBUG: Calculated expires_at: {expires_at}")
        invite_code = create_channel_invite(channel['id'], session['user_id'], expires_at, int(max_uses) if max_uses else None)
        # Получить новый инвайт для возврата
        with get_db_connection() as conn:
            new_invite = conn.execute("SELECT * FROM channel_invites WHERE invite_code = ?", (invite_code,)).fetchone()
            invite_data = dict(new_invite)
            invite_data['created_by_username'] = conn.execute("SELECT username FROM users WHERE id = ?", (invite_data['created_by'],)).fetchone()['username']
        print(f"DEBUG: Invite created successfully: {invite_code}, invite_data keys: {list(invite_data.keys())}")
        return jsonify({'success': True, 'invite_code': invite_code, 'invite': invite_data})
    except Exception as e:
        print(f"DEBUG: Exception in create_channel_invite: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/delete_channel_invite', methods=['POST'])
def delete_channel_invite_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    invite_id = request.form.get('invite_id')
    if not invite_id:
        return jsonify({'success': False, 'error': 'ID инвайта обязателен'})
    # Получить канал из инвайта для проверки прав
    with get_db_connection() as conn:
        invite = conn.execute("SELECT channel_id FROM channel_invites WHERE id = ?", (invite_id,)).fetchone()
        if not invite:
            return jsonify({'success': False, 'error': 'Инвайт не найден'})
        channel_id = invite['channel_id']
        # Проверить права админа
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel_id, session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            return jsonify({'success': False, 'error': 'Нет прав'})
    try:
        delete_channel_invite(int(invite_id))
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/join_channel_via_invite/<invite_code>')
def join_channel_via_invite_get(invite_code):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Проверить, что инвайт существует и валиден
    with get_db_connection() as conn:
        invite = conn.execute("SELECT * FROM channel_invites WHERE invite_code = ?", (invite_code,)).fetchone()
        if not invite:
            return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error='Инвайт не найден')
        # Проверить срок действия
        if invite['expires_at'] and datetime.datetime.now() > datetime.datetime.fromisoformat(invite['expires_at']):
            return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error='Инвайт истек')
        # Проверить максимум использований
        if invite['max_uses'] and invite['uses'] >= invite['max_uses']:
            return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error='Инвайт исчерпан')
        # Получить канал
        channel = conn.execute("SELECT * FROM channels WHERE id = ?", (invite['channel_id'],)).fetchone()
        if not channel:
            return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error='Канал не найден')
        # Проверить, что пользователь уже не в канале
        member = conn.execute("SELECT * FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if member:
            return render_template('join_channel_via_invite.html', channel=channel, invite_code=invite_code, error='Вы уже в этом канале', member_count=0)
        # Получить количество участников
        member_count = conn.execute("SELECT COUNT(*) FROM channel_members WHERE channel_id = ?", (channel['id'],)).fetchone()[0]
    return render_template('join_channel_via_invite.html', channel=channel, invite_code=invite_code, error=None, member_count=member_count)


@app.route('/join_channel_via_invite/<invite_code>', methods=['POST'])
def join_channel_via_invite_post(invite_code):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    try:
        success = use_channel_invite(invite_code, session['user_id'])
        if success:
            return redirect(url_for('index'))  # После успешного присоединения перенаправить на главную
        else:
            return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error='Инвайт недействителен', member_count=0)
    except Exception as e:
        return render_template('join_channel_via_invite.html', channel=None, invite_code=invite_code, error=str(e), member_count=0)


@app.route('/channel_members/<channel_name>')
def get_channel_members_route(channel_name):
    if 'user_id' not in session:
        return jsonify({'members': []})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'members': []})
    # Проверить, что пользователь участник
    with get_db_connection() as conn:
        member = conn.execute("SELECT * FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
    if not member:
        return jsonify({'members': []})
    members = get_channel_members(channel['id'])
    return jsonify({'members': members})


@app.route('/channel_invites/<channel_name>')
def get_channel_invites_route(channel_name):
    if 'user_id' not in session:
        return jsonify({'invites': []})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'invites': []})
    # Проверить права
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_name'] != 'Admin':
            return jsonify({'invites': []})
    invites = get_channel_invites(channel['id'])
    return jsonify({'invites': invites})


@app.route('/user_channel_role/<channel_name>')
def get_user_channel_role_route(channel_name):
    if 'user_id' not in session:
        return jsonify({'role': None})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'role': None})
    role = get_user_channel_role(session['user_id'], channel['id'])
    return jsonify({'role': role})


# === Страницы управления каналами ===

@app.route('/channel/<channel_name>/settings')
def channel_settings(channel_name):
    print(f"channel_settings called with channel_name: {repr(channel_name)}")
    print(f"channel_name type: {type(channel_name)}, len: {len(channel_name)}")
    if 'user_id' not in session:
        return redirect(url_for('login'))
    channel = get_channel_by_name(channel_name)
    print(f"get_channel_by_name returned: {channel}")
    if not channel:
        print(f"Channel not found for name: {repr(channel_name)}")
        return "Канал не найден", 404
    # Проверить, что пользователь участник и имеет права админа
    with get_db_connection() as conn:
        member_check = conn.execute("SELECT * FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
        print(f"Member check raw: {dict(member_check) if member_check else None}")
        member_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        print(f"Channel {channel_name} member role check: {dict(member_role) if member_role else None}")
        if not member_role or member_role['role_name'] != 'Admin':
            print(f"No access to {channel_name}: member_role={member_role}")
            return "Нет доступа", 403
    members = get_channel_members(channel['id'])
    invites = get_channel_invites(channel['id'])
    # Добавить имя создателя для каждого инвайта
    for invite in invites:
        with get_db_connection() as conn:
            user = conn.execute("SELECT username FROM users WHERE id = ?", (invite['created_by'],)).fetchone()
            invite['created_by_username'] = user['username'] if user else 'Неизвестен'
    return render_template('channel_management.html', channel=channel, members=members, invites=invites, type='settings')


@app.route('/channel/<channel_name>/members')
def channel_members(channel_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    channel = get_channel_by_name(channel_name)
    if not channel:
        return "Канал не найден", 404
    # Проверить, что пользователь участник и имеет права админа
    with get_db_connection() as conn:
        member_role = conn.execute("SELECT cr.role_name FROM channel_members cm JOIN channel_roles cr ON cm.role_id = cr.id WHERE cm.channel_id = ? AND cm.user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not member_role or member_role['role_name'] != 'Admin':
            return "Нет доступа", 403
    members = get_channel_members(channel['id'])
    print(f"channel_members: members = {members}")
    return render_template('channel_management.html', channel=channel, members=members, type='members')


@app.route('/channel/<channel_name>/invites')
def channel_invites(channel_name):
    print(f"DEBUG: Accessing invites for channel {channel_name}")
    if 'user_id' not in session:
        return redirect(url_for('login'))
    channel = get_channel_by_name(channel_name)
    if not channel:
        print(f"DEBUG: Channel {channel_name} not found")
        return "Канал не найден", 404
    # Проверить, что пользователь участник и имеет права админа
    with get_db_connection() as conn:
        member = conn.execute("SELECT role_id FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not member or member['role_id'] != 1:  # 1 - Admin
            print(f"DEBUG: No admin access for user {session['user_id']} in channel {channel_name}")
            return "Нет доступа", 403
    invites = get_channel_invites(channel['id'])
    print(f"DEBUG: Invites for render: {invites}")
    members = get_channel_members(channel['id'])
    # Добавить имя создателя для каждого инвайта
    for invite in invites:
        with get_db_connection() as conn:
            user = conn.execute("SELECT username FROM users WHERE id = ?", (invite['created_by'],)).fetchone()
            invite['created_by_username'] = user['username'] if user else 'Неизвестен'
    return render_template('channel_management.html', channel=channel, invites=invites, members=members, type='invites')


@app.route('/update_channel_settings/<channel_name>', methods=['POST'])
def update_channel_settings(channel_name):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    channel = get_channel_by_name(channel_name)
    if not channel:
        return jsonify({'success': False, 'error': 'Канал не найден'})
    # Проверить права
    with get_db_connection() as conn:
        user_role = conn.execute("SELECT role_id FROM channel_members WHERE channel_id = ? AND user_id = ?", (channel['id'], session['user_id'])).fetchone()
        if not user_role or user_role['role_id'] != 1:
            return jsonify({'success': False, 'error': 'Нет прав'})
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_private = request.form.get('is_private') == 'on'
    if not name:
        return jsonify({'success': False, 'error': 'Название обязательно'})
    # Проверить уникальность имени если изменилось
    if name != channel['name']:
        if get_channel_by_name(name):
            return jsonify({'success': False, 'error': 'Канал с таким названием уже существует'})
    with get_db_connection() as conn:
        conn.execute("UPDATE channels SET name = ?, description = ?, is_private = ? WHERE id = ?", (name, description, is_private, channel['id']))
        conn.commit()
    return redirect(url_for('channel_settings', channel_name=name))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)