import redis
from datetime import timedelta

# Подключение к Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# TTL для разных типов данных
PROFILE_TTL = timedelta(hours=2)      # Профили пользователей
MESSAGES_TTL = timedelta(minutes=30)  # Сообщения чатов
MEMBERS_TTL = timedelta(hours=1)      # Участники каналов
FEED_TTL = timedelta(minutes=15)      # Лента постов

import redis
import json
from datetime import timedelta

# Подключение к Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# TTL для разных типов данных
PROFILE_TTL = timedelta(hours=2)      # Профили пользователей
MESSAGES_TTL = timedelta(minutes=30)  # Сообщения чатов
MEMBERS_TTL = timedelta(hours=1)      # Участники каналов
FEED_TTL = timedelta(minutes=15)      # Лента постов

def get_user_profile_cached(user_id):
    cache_key = f"user_profile:{user_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Загрузка из базы данных
    profile = get_user_profile_from_db(user_id)
    
    # Сохранение в кэш
    redis_client.setex(cache_key, int(PROFILE_TTL.total_seconds()), json.dumps(profile))
    return profile

def invalidate_user_profile_cache(user_id):
    cache_key = f"user_profile:{user_id}"
    redis_client.delete(cache_key)

def get_chat_messages_cached(chat_id, page=1, per_page=20):
    cache_key = f"chat_messages:{chat_id}:page_{page}_{per_page}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Загрузка из базы данных
    messages = get_chat_messages_from_db(chat_id, page, per_page)
    
    # Сохранение в кэш
    redis_client.setex(cache_key, int(MESSAGES_TTL.total_seconds()), json.dumps(messages))
    return messages

def invalidate_chat_messages_cache(chat_id):
    # Удаление всех страниц кэша для этого чата
    pattern = f"chat_messages:{chat_id}:page_*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

def get_channel_members_cached(channel_id):
    cache_key = f"channel_members:{channel_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Загрузка из базы данных
    members = get_channel_members_from_db(channel_id)
    
    # Сохранение в кэш
    redis_client.setex(cache_key, int(MEMBERS_TTL.total_seconds()), json.dumps(members))
    return members

def invalidate_channel_members_cache(channel_id):
    cache_key = f"channel_members:{channel_id}"
    redis_client.delete(cache_key)

def get_feed_cached(user_id, page=1, per_page=20):
    cache_key = f"feed:{user_id}:page_{page}_{per_page}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Загрузка из базы данных
    feed = get_feed_from_db(user_id, page, per_page)
    
    # Сохранение в кэш
    redis_client.setex(cache_key, int(FEED_TTL.total_seconds()), json.dumps(feed))
    return feed

def invalidate_feed_cache(user_id):
    # Удаление всех страниц кэша ленты для этого пользователя
    pattern = f"feed:{user_id}:page_*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)
