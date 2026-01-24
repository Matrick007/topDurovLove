# Технические рекомендации для проекта SMS

## 1. Архитектурные улучшения

### 1.1. Разделение приложения на модули

Текущая архитектура хранит весь код в файле [`app.py`](../app.py:1), что затрудняет поддержку и расширение. Рекомендуется разделить приложение следующим образом:

```
sms_app/
├── app.py
├── config.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── message.py
│   ├── group.py
│   └── channel.py
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py
│   ├── messaging_routes.py
│   ├── social_routes.py
│   └── api_routes.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── messaging_service.py
│   └── notification_service.py
├── utils/
│   ├── __init__.py
│   ├── security.py
│   └── validators.py
└── static/
    └── ...
```

### 1.2. Рефакторинг [`utils.py`](../utils.py:1)

Файл [`utils.py`](../utils.py:1) содержит слишком много ответственностей. Рекомендуется разбить его на несколько модулей:

- `database.py` - работа с базой данных
- `security.py` - хеширование и проверка паролей
- `validators.py` - валидация данных
- `messaging.py` - логика работы с сообщениями
- `social.py` - логика социальной сети

## 2. Безопасность

### 2.1. Улучшение хеширования паролей

Текущая реализация использует простой SHA256. Рекомендуется использовать bcrypt:

```python
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=12)

def verify_password(password, hashed):
    return check_password_hash(hashed, password)
```

### 2.2. Валидация входных данных

Необходимо добавить валидацию всех входных данных:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
```

## 3. Масштабируемость

### 3.1. Переход на PostgreSQL

Для масштабирования рекомендуется перейти с SQLite на PostgreSQL:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### 3.2. Кэширование

Внедрение Redis для кэширования часто запрашиваемых данных:

```python
import redis
from flask import Flask

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_user(user_id):
    cached = redis_client.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    # получить из базы данных
    user = get_user_by_id(user_id)
    redis_client.setex(f"user:{user_id}", 3600, json.dumps(user))  # кэш на 1 час
    return user
```

## 4. Производительность

### 4.1. Оптимизация запросов к базе данных

Добавление индексов к часто используемым полям:

```sql
-- Индексы для таблицы пользователей
CREATE INDEX idx_users_username ON users(username);

-- Индексы для сообщений
CREATE INDEX idx_messages_chat_timestamp ON messages(chat_id, timestamp);
CREATE INDEX idx_messages_sender ON messages(sender);

-- Индексы для групп
CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_user ON group_members(user_id);
```

### 4.2. Пагинация

Добавление пагинации для списков сообщений и постов:

```python
def get_messages_paginated(chat_id, page=1, per_page=50):
    offset = (page - 1) * per_page
    with get_db_connection() as conn:
        messages = conn.execute("""
            SELECT m.id, m.sender, m.message, m.timestamp, m.status
            FROM messages m
            WHERE m.chat_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ? OFFSET ?
        """, (chat_id, per_page, offset)).fetchall()
    return [dict(m) for m in messages]
```

## 5. Асинхронные задачи

Для выполнения длительных операций (например, отправка уведомлений, обработка изображений) рекомендуется использовать Celery:

```python
from celery import Celery

celery_app = Celery('sms_app', broker='redis://localhost:6379')

@celery_app.task
def send_push_notification(user_id, message):
    # отправить push-уведомление пользователю
    pass

@celery_app.task
def process_image_upload(image_path):
    # обработать и оптимизировать изображение
    pass
```

## 6. Логирование

Настройка полноценной системы логирования:

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/sms_app.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SMS App startup')
```

## 7. Тестирование

Добавление unit-тестов для основных компонентов:

```python
import unittest
from app import app

class MessageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_send_message(self):
        # тестирование отправки сообщения
        response = self.app.post('/send_message', data={
            'to': 'user2',
            'message': 'Test message'
        })
        self.assertEqual(response.status_code, 200)
```

## 8. Документация API

Для REST API рекомендуется использовать Swagger/OpenAPI:

```python
from flask import Flask
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """
    Получение списка сообщений
    ---
    parameters:
      - name: chat_id
        in: query
        type: integer
        required: true
    responses:
      200:
        description: Список сообщений
    """
    pass
```

## 9. CI/CD Pipeline

Пример конфигурации GitHub Actions:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        python -m pytest tests/
        
    - name: Security scan
      run: |
        bandit -r .
```

## 10. Мониторинг и метрики

Добавление системы мониторинга с использованием Prometheus:

```python
from prometheus_client import Counter, Histogram, generate_latest
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
REQUEST_TIME = Histogram('http_request_duration_seconds', 'HTTP Request Duration')

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    REQUEST_TIME.observe(time.time() - request.start_time)
    return response