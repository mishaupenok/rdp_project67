import os
import routeros_api
from dotenv import load_dotenv

load_dotenv()


class IpListAddress:

    def __init__(self, ip, comment, db_id=None):
        self.ip = ip
        self.comment = comment
        self.db_id = db_id

    def __str__(self):
        return f"IP: {self.ip} | Комментарий: {self.comment} (ID: {self.db_id})"


class MikrotikManager:

    def __init__(self):
        self.host = os.getenv("MIKROTIK_HOST")
        self.user = os.getenv("MIKROTIK_USER")
        self.password = os.getenv("MIKROTIK_PASSWORD")
        self.connection = None
        self.api = None

    def connect(self):
        """Установка соединения с API MikroTik."""
        try:
            self.connection = routeros_api.RouterOsApiPool(
                self.host,
                username=self.user,
                password=self.password,
                plaintext_login=True,
            )
            self.api = self.connection.get_api()
            print(f"[MikroTik] Успешно подключено к {self.host}")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось подключиться к роутеру: {e}")
            raise

    def disconnect(self):
        """Закрытие соединения."""
        if self.connection:
            self.connection.disconnect()
            print("[MikroTik] Соединение закрыто.")

    def get_rdp_address_list(self) -> list[IpListAddress]:
        """Возвращает список объектов класса IpListAddress с именем списка

        'rdp'.
        """
        if not self.api:
            print("[ОШИБКА] Нет активного соединения с API.")
            return []

        address_list_resource = self.api.get_resource(
            "/ip/firewall/address-list"
        )

        raw_addresses = address_list_resource.get(list="rdp")

        processed_list = []
        for item in raw_addresses:
            ip_obj = IpListAddress(
                ip=item.get("address"),
                comment=item.get("comment", "Без комментария"),
                db_id=item.get("id"),
            )
            processed_list.append(ip_obj)

        return processed_list

    def add_rdp_address(self, ip_address, comment="Добавлено через Python"):
        """Добавляет IP в список 'rdp' с таймаутом 12 часов."""
        if not self.api:
            return False

        address_list_resource = self.api.get_resource(
            "/ip/firewall/address-list"
        )

        try:
            address_list_resource.add(
                address=ip_address,
                list="rdp",
                timeout="12:00:00",
                comment=comment,
            )
            print(
                f"[MikroTik] IP {ip_address} успешно добавлен в список 'rdp' на 12 часов."
            )
            return True
        except Exception as e:
            print(f"[ОШИБКА] Не удалось добавить IP {ip_address}: {e}")
            return False

    def remove_rdp_address(self, db_id):
        """Безопасное удаление записи по её уникальному внутреннему ID."""
        if not self.api:
            return False

        address_list_resource = self.api.get_resource(
            "/ip/firewall/address-list"
        )

        try:
            address_list_resource.remove(id=db_id)
            print(f"[MikroTik] Запись с ID {db_id} успешно удалена.")
            return True
        except Exception as e:
            print(f"[ОШИБКА] Не удалось удалить запись с ID {db_id}: {e}")
            return False

    def upsert_rdp_address(self, input_ip, comment="RDP Access"):
        """Ищет IP.

        Если нашел — удаляет старый и записывает заново (обновляя таймаут). Если
        не нашел — просто записывает.
        """
        print(f"\n[Умный вход] Проверка адреса {input_ip}...")

        current_list = self.get_rdp_address_list()

        found_address = None
        for item in current_list:
            if item.ip == input_ip:
                found_address = item
                break

        if found_address:
            print(
                f"[Умный вход] IP {input_ip} найден в базе (ID: {found_address.db_id}). Удаляем старый доступ..."
            )
            self.remove_rdp_address(found_address.db_id)
        else:
            print(f"[Умный вход] IP {input_ip} не найден в списке.")

        self.add_rdp_address(input_ip, comment=comment)


if __name__ == "__main__":
    manager = MikrotikManager()

    try:
        manager.connect()

        test_ip = "111.111.111.111"

        manager.upsert_rdp_address(test_ip, comment="Mikhail Home PC")

        print("\n=== ТЕКУЩИЙ СПИСОК АДРЕСОВ В MIKROTIK ===")
        addresses = manager.get_rdp_address_list()
        for addr in addresses:
            print(addr)

    except Exception as e:
        print(f"Ошибка в процессе работы: {e}")
    finally:
        manager.disconnect()