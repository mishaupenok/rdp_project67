import psycopg2
from datetime import datetime
import os



class User:
    def __init__(self, user_id, first_name, last_name, login, password, department):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.login = login
        self.password = password
        self.department = department

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.login}, ID: {self.user_id})"


class Computer:
    def __init__(self, computer_id, ip_address, hostname, port):
        self.computer_id = computer_id
        self.ip_address = ip_address
        self.hostname = hostname
        self.port = port

    def __str__(self):
        return f"{self.hostname} (IP: {self.ip_address}, Port: {self.port}, ID: {self.computer_id})"


class Connection:
    def __init__(self, user_id, computer_id, public_ip, time):
        self.user_id = user_id
        self.computer_id = computer_id
        self.public_ip = public_ip
        self.time = time



class AuthSystem:
    def __init__(self, db_name, user, password, host="localhost", port="5432", schema_file="schema.sql"):
        self.db_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.conn = None
        self.cursor = None

        self._connect_to_db()
        self._initialize_db_schema(schema_file)

    def _connect_to_db(self):
        """Установка связи с базой данных"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            print("[БД] Успешное подключение к PostgreSQL.")
        except psycopg2.Error as e:
            print(f"[БД] Ошибка подключения: {e}")
            raise

    def _initialize_db_schema(self, schema_file):
        """Чтение SQL-файла и создание таблиц"""
        if not os.path.exists(schema_file):
            print(f"[ОШИБКА] Файл '{schema_file}' не найден!")
            return

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            self.cursor.execute(sql_script)
            self.conn.commit()
            print(f"[БД] Таблицы из файла '{schema_file}' проверены/созданы.")
        except psycopg2.Error as e:
            print(f"[БД] Ошибка создания таблиц: {e}")
            self.conn.rollback()

    def add_user(self, user: User):
        """Добавление пользователя в базу"""
        try:
            query = """
                    INSERT INTO users (user_id, first_name, last_name, login, password, department)
                    VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO \
                    UPDATE SET
                        first_name = EXCLUDED.first_name, \
                        last_name = EXCLUDED.last_name, \
                        login = EXCLUDED.login, \
                        password = EXCLUDED.password, \
                        department = EXCLUDED.department; \
                    """
            self.cursor.execute(query, (
                user.user_id, user.first_name, user.last_name,
                user.login, user.password, user.department
            ))
            self.conn.commit()
            print(f"[БД] Пользователь '{user.login}' сохранен.")
        except psycopg2.Error as e:
            print(f"[БД] Ошибка добавления пользователя: {e}")
            print(f"[БД] Ошибка добавления пользователя: {e}")
            self.conn.rollback()

    def add_computer(self, computer: Computer):
        """Добавление компьютера в базу"""
        try:
            query = """
                    INSERT INTO computers (computer_id, ip_address, hostname, port)
                    VALUES (%s, %s, %s, %s) ON CONFLICT (computer_id) DO \
                    UPDATE SET
                        ip_address = EXCLUDED.ip_address, \
                        hostname = EXCLUDED.hostname, \
                        port = EXCLUDED.port; \
                    """
            self.cursor.execute(query, (
                computer.computer_id, computer.ip_address, computer.hostname, computer.port
            ))
            self.conn.commit()
            print(f"[БД] Компьютер '{computer.hostname}' сохранен.")
        except psycopg2.Error as e:
            print(f"[БД] Ошибка добавления компьютера: {e}")
            self.conn.rollback()

    def check_access(self, login, password):
        """Проверка логина и пароля в базе"""
        query = "SELECT user_id, first_name, last_name, login, password, department FROM users WHERE login = %s"
        self.cursor.execute(query, (login,))
        result = self.cursor.fetchone()

        if result and result[4] == password:
            return User(result[0], result[1], result[2], result[3], result[4], result[5])
        return None

    def log_connection(self, connection_obj: Connection):
        """Сохранение лога входа в таблицу connections"""
        try:
            query = """
                    INSERT INTO connections (user_id, computer_id, public_ip, connect_time)
                    VALUES (%s, %s, %s, %s) \
                    """
            self.cursor.execute(query, (
                connection_obj.user_id,
                connection_obj.computer_id,
                connection_obj.public_ip,
                connection_obj.time
            ))
            self.conn.commit()
            print(f"[БД] Лог успешного входа сохранен для User ID: {connection_obj.user_id}")
        except psycopg2.Error as e:
            print(f"[БД] Ошибка записи лога: {e}")
            self.conn.rollback()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()



if __name__ == "__main__":
    DB_NAME = "rdp_security_db"
    DB_USER = "postgres"
    DB_PASSWORD = "123456"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    auth_system = None
    try:
        auth_system = AuthSystem(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

        test_user = User(101, "Алексей", "Смирнов", "admin", "pass123", "IT-Dept")
        auth_system.add_user(test_user)

        test_pc = Computer(1, "192.168.1.100", "WorkStation-01", 3389)
        auth_system.add_computer(test_pc)

        print("\n=== ВХОД В СИСТЕМУ RDP ===")
        input_login = input("Введите логин: ")
        input_password = input("Введите пароль: ")
        authenticated_user = auth_system.check_access(input_login, input_password)

        if authenticated_user:
            print(f"\n[УСПЕХ] Добро пожаловать, {authenticated_user.first_name}!")

            new_log = Connection(
                user_id=authenticated_user.user_id,
                computer_id=test_pc.computer_id,
                public_ip="178.45.20.11",
                time=datetime.now()
            )
            auth_system.log_connection(new_log)
        else:
            print("\n[ОТКАЗ] Неверный логин или пароль!")

    except Exception as e:
        print(f"Критическая ошибка работы программы: {e}")
    finally:
        if auth_system:
            auth_system.close()
            print("[СИСТЕМА] Сессия закрыта.")