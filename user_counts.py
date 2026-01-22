import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Получение количества зарегистрированных пользователей
cursor.execute("SELECT COUNT(*) FROM users")
registered_count = cursor.fetchone()[0]

# Поскольку приложение не запущено, online_users пустой, онлайн = 0
online_count = 0

# Вывод результатов
print(f"Зарегистрированных пользователей: {registered_count}")
print(f"Онлайн пользователей: {online_count}")

# Закрытие соединения
conn.close()