
import requests
from bs4 import BeautifulSoup
import time
import json
import datetime
import logging

# --- НАСТРОЙКИ ---
URL = "https://zakupki.gospmr.org/zakupki/?sbj=Министерство+здравоохранения"
ID_THRESHOLD = 9338  # отслеживаем ID выше этого значения
TELEGRAM_BOT_TOKEN = "8044532856:AAFAqtS9-lRodpBkKvochtoXioOxJCBWxWE"
TELEGRAM_CHAT_ID = "442183644"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- ЛОГИ ---
logging.basicConfig(
    filename='monitor_log.txt',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_tender_info():
    """Парсим таблицу закупок на сайте и извлекаем ID, предмет и цену"""
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("table.table tr")[1:]  # пропускаем заголовок
        tenders = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 6:
                continue
            try:
                tender_id = int(cols[0].text.strip())
                subject = cols[2].text.strip()
                price = cols[-1].text.strip()
                tenders.append({
                    "id": tender_id,
                    "subject": subject,
                    "price": price
                })
            except:
                continue
        return tenders
    except Exception as exc:
        logging.error("Ошибка при получении тендеров: %s", exc)
        return []

def load_last_seen_ids():
    """Загружаем уже увиденные ID из файла"""
    try:
        with open("last_seen_ids.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_last_seen_ids(ids):
    """Сохраняем ID, которые уже обработаны"""
    with open("last_seen_ids.json", "w") as f:
        json.dump(ids, f)

def send_telegram_message(text):
    """Отправляем сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            logging.error("Ошибка Telegram: %s", r.text)
    except Exception as exc:
        logging.error("Telegram исключение: %s", exc)

def is_working_time():
    """Проверяем: сейчас рабочее время или нет"""
    now = datetime.datetime.now()
    return now.weekday() < 5 and 8 <= now.hour < 19

def main():
    print("📦 Запущен мониторинг тендеров Минздрава ПМР...")
    logging.info("Скрипт стартовал.")
    tenders = get_tender_info()
    if not is_working_time():
        print("⏳ Вне рабочего времени (8:00–19:00, Пн–Пт). Ничего не проверяем.")
        logging.info("Пропуск — вне рабочего времени.")
        return

    last_seen_ids = load_last_seen_ids()
    new_tenders = [t for t in tenders if t["id"] > ID_THRESHOLD and t["id"] not in last_seen_ids]

    if new_tenders:
        for tender in new_tenders:
            message = f"🆕 Новая закупка от Минздрава ПМР\n"                       f"🆔 ID: {tender['id']}\n"                       f"📄 Предмет: {tender['subject']}\n"                       f"💰 Цена: {tender['price']}\n"                       f"🔗 https://zakupki.gospmr.org/purchase/?id={tender['id']}"
            print(f"📨 Отправка уведомления: ID {tender['id']}")
            send_telegram_message(message)
            logging.info("Отправлено уведомление об ID %s", tender['id'])
        save_last_seen_ids(last_seen_ids + [t["id"] for t in new_tenders])
    else:
        print("ℹ️ Новых закупок нет.")
        logging.info("Новых закупок не найдено.")

if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")
