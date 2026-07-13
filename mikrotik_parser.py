import os
import routeros_api
from dotenv import load_dotenv

load_dotenv()


def get_rdp_address_list():
    HOST = os.getenv("MIKROTIK_HOST")
    USER = os.getenv("MIKROTIK_USER")
    PASSWORD = os.getenv("MIKROTIK_PASSWORD")

    if not all([HOST, USER, PASSWORD]):
        print(
            "[ОШИБКА] Настройки MikroTik не найдены в файле .env! Проверь его заполнение."
        )
        return

    print(f"[MikroTik] Подключение к API роутера {HOST}...")

    try:
        connection = routeros_api.RouterOsApiPool(
            HOST, username=USER, password=PASSWORD, plaintext_login=True
        )

        api = connection.get_api()

        address_list_resource = api.get_resource("/ip/firewall/address-list")
        rdp_addresses = address_list_resource.get(list="rdp")

        print(
            f"[MikroTik] Соединение установлено. Найдено записей в списке 'rdp': {len(rdp_addresses)}\n"
        )

        print(f"{'IP Адрес':<20} | {'Комментарий':<30}")
        print("-" * 55)

        for item in rdp_addresses:
            ip = item.get("address", "Неизвестно")
            comment = item.get("comment", "Без комментария")
            print(f"{ip:<20} | {comment:<30}")

        connection.disconnect()
        print("\n[MikroTik] Сессия успешно закрыта.")

    except Exception as e:
        print(
            f"\n[ОШИБКА] Не удалось получить данные. Проверь настройки сети или учетные данные."
        )
        print(f"Детали ошибки: {e}")


if __name__ == "__main__":
    get_rdp_address_list()