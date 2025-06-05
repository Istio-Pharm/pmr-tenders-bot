import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- НАСТРОЙКИ ---
URL = "https://zakupki.gospmr.org/zakupki/?sbj=Министерство+здравоохранения"
ID_THRESHOLD = 9338
TELEGRAM_BOT_TOKEN = "8044532856:AAFAqtS9-lRodpBkKvochtoXioOxJCBWxWE"
TELEGRAM_CHAT_ID = "442183644"
HEADERS = {"User-Agent": "Mozilla/5.0"}
GOOGLE_SHEET_ID = "1KJcufLBYkhfPh5gRSJkAT3fsiiJ_X28_itqq7Ijrf9g"
GOOGLE_CREDENTIALS = "pmr-tenders-bot-ca187369504f.json"

# --- ЛОГИ ---
logging.basicConfig(
    filename='monitor_log.txt',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- ФУНКЦИИ ---
def get_tender_info():
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
            except Exception:
                continue
        return tenders
    except Exception as exc:
        logging.error("Ошибка при получении тендеров: %s", exc)
        return []

def load_last_seen_ids():
    try:
        with open("last_seen_ids.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_last_seen_ids(ids):
    with open("last_seen_ids.json", "w") as f:
        json.dump(ids, f)

def send_telegram_message(text):
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
    now = datetime.now()
    return now.weekday() < 5 and 8 <= now.hour < 19

def log_to_sheets(tender_id, subject, price):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        url = f"https://zakupki.gospmr.org/purchase/?id={tender_id}"
        sheet.append_row([str(tender_id), subject, price, datetime.now().strftime("%Y-%m-%d %H:%M"), url])
    except Exception as e:
        logging.error(f"Ошибка при записи в Google Sheets: {e}")

# --- ОСНОВНОЙ ЦИКЛ ---
def main():
    print("📦 Запущен мониторинг тендеров Минздрава ПМР...")
    logging.info("Скрипт стартовал.")
    
    if not is_working_time():
        print("⏳ Вне рабочего времени (8:00–19:00, Пн–Пт). Пропускаем.")
        logging.info("Пропуск — вне рабочего времени.")
        return

    tenders = get_tender_info()
    last_seen_ids = load_last_seen_ids()
    new_tenders = [t for t in tenders if t["id"] > ID_THRESHOLD and t["id"] not in last_seen_ids]

    if new_tenders:
        for tender in new_tenders:
            message = (
                f"🆕 Новая закупка от Минздрава ПМР\n"
                f"🆔 ID: {tender['id']}\n"
                f"📄 Предмет: {tender['subject']}\n"
                f"💰 Цена: {tender['price']}\n"
                f"🔗 https://zakupki.gospmr.org/purchase/?id={tender['id']}"
            )
            print(f"📨 Отправка уведомления: ID {tender['id']}")
            send_telegram_message(message)
            log_to_sheets(tender['id'], tender['subject'], tender['price'])
            logging.info("Отправлено уведомление об ID %s", tender['id'])
        save_last_seen_ids(last_seen_ids + [t["id"] for t in new_tenders])
    else:
        print("ℹ️ Новых закупок нет.")
        logging.info("Новых закупок не найдено.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    while True:
        main()
        time.sleep(1200)  # 20 минут
