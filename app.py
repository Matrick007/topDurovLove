# app.py
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from utils import (
    get_db_connection, init_db, hash_password, verify_password, get_user_by_username,
    get_or_create_chat, get_messages, get_active_users, create_user, save_message,
    mark_message_as_delivered, mark_message_as_read, get_unread_messages,
    create_group, get_group_by_name, get_groups_for_user, add_user_to_group,
    get_group_messages, save_group_message, delete_message, save_pinned_message,
    get_pinned_message, remove_pinned_message, delete_chat, delete_group, get_user_chats,
    follow_user, unfollow_user, is_following, get_followers, get_following,
    create_post, get_posts_for_user, get_feed, like_post, unlike_post, is_liked,
    add_comment, get_comments_for_post, repost, unrepost, is_reposted,
    update_group_message_read
)
import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False, async_mode='eventlet')

# Трекинг
online_users = {}
user_sids = {}
user_chat_context = {}

init_db()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session['username']
    user_chats = get_user_chats(user_id)
    user_groups = get_groups_for_user(user_id)
    return render_template('index.html', username=username, user_chats=user_chats, user_groups=user_groups)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = get_user_by_username(username)
        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
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

    emit('receive_message', {'msg': message, 'sender': sender, 'room': room}, room=room)

    if room.startswith('group_'):
        group_name = room.replace('group_', '')
        group = get_group_by_name(group_name)
        if group:
            msg_id = save_group_message(group['id'], sender, message)
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
                msg_id = save_message(chat_id, sender, message)
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
    else:
        parts = room.split('_')
        chat_id = get_or_create_chat(get_user_by_username(parts[0])['id'], get_user_by_username(parts[1])['id'])
        msg = next((m for m in get_messages(chat_id) if m['id'] == msg_id), None)

    if msg and msg['sender'] == sender:
        delete_message(msg_id, room.startswith('group_'))
        emit('message_deleted', {'msg_id': msg_id}, room=room)


@socketio.on('pin_message')
def handle_pin_message(data):
    group_name = data['group']
    msg_id = data['msg_id']
    sender = session.get('username')
    save_pinned_message(get_group_by_name(group_name)['id'], msg_id)
    emit('pinned_message', {'msg_id': msg_id, 'group': group_name}, broadcast=True)


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
    is_owner = True
    is_following_user = None
    followers = get_followers(session['user_id'])
    following = get_following(session['user_id'])
    posts = get_posts_for_user(session['user_id'])
    feed = get_feed(session['user_id'])
    return render_template('profile.html', user=user, is_owner=is_owner, is_following=is_following_user, followers=followers, following=following, posts=posts, feed=feed)


@app.route('/profile/<username>')
def user_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_username(username)
    if not user:
        return "Пользователь не найден", 404
    is_owner = user['id'] == session['user_id']
    is_following_user = is_following(session['user_id'], user['id']) if not is_owner else None
    followers = get_followers(user['id'])
    following = get_following(user['id'])
    posts = get_posts_for_user(user['id'])
    return render_template('profile.html', user=user, is_owner=is_owner, is_following=is_following_user, followers=followers, following=following, posts=posts)


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
    
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE users SET city = ?, bio_short = ?, country = ?, languages = ?, bio_full = ?, hobbies = ? WHERE id = ?
        """, (city, bio_short, country, languages, bio_full, hobbies, session['user_id']))
        conn.commit()
    
    return jsonify({'success': True})


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
    create_post(session['user_id'], content)
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
        return jsonify({'user_chats': [], 'user_groups': []})
    user_id = session['user_id']
    user_chats = get_user_chats(user_id)
    user_groups = get_groups_for_user(user_id)
    return jsonify({'user_chats': user_chats, 'user_groups': user_groups})

@app.route('/search_users')
def search_users():
    print(f"Session user_id: {session.get('user_id')}")
    if 'user_id' not in session:
        print("No session")
        return jsonify({'users': []})
    query = request.args.get('q', '').strip()
    print(f"Query: '{query}'")
    if not query:
        return jsonify({'users': []})
    with get_db_connection() as conn:
        users = conn.execute("SELECT id, LOWER(username) as username FROM users WHERE LOWER(username) LIKE LOWER(?) AND id != ?", (f'%{query}%', session['user_id'])).fetchall()
        print(f"Found users: {[dict(u) for u in users]}")
    return jsonify({'users': [dict(u) for u in users]})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)