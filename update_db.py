#!/usr/bin/env python3
# update_db.py
# Скрипт для обновления базы данных: добавление таблиц каналов

import sys
import os

# Добавляем текущую директорию в путь для импорта utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import init_db

if __name__ == '__main__':
    print("Обновление базы данных...")
    init_db()
    print("База данных успешно обновлена!")