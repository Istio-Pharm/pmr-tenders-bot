
import os
import time
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import telebot
import traceback

# Telegram
BOT_TOKEN = "8044532856:AAFAqtS9-lRodpBkKvochtoXioOxJCBWxWE"
CHAT_ID = "442183644"

print("[Запуск] Скрипт стартовал успешно — начинается мониторинг...")

try:
    bot = telebot.TeleBot(BOT_TOKEN)
    bot.send_message(CHAT_ID, "[Бот] Бот стартовал и проверяет тендеры (v2)")
except Exception as e:
    print("[Ошибка] Ошибка при инициализации Telegram:", e)

# Google Sheets
SPREADSHEET_ID = '1KJcufLBYkhfPh5gRSJkAT3fsiiJ_X28_itqq7Ijrf9g'
CREDS_FILE = 'service_account.json'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

try:
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1
except Exception as e:
    print("[Ошибка] Ошибка при подключении к Google Sheets:", e)
    bot.send_message(CHAT_ID, f"[Ошибка] Ошибка при подключении к Google Sheets: {e}")

def fetch_pmr_tenders():
    print("[Проверка] Запуск fetch_pmr_tenders...")
    url = "https://zakupki.gospmr.org/zakupki/?num=&obj=&zid=&sbj=Министерство+здравоохранения&price_from=&price_to=&request_end_from=&request_end_to=&type=none&status=none&groupe=none"

    try:
        response = requests.get(url, timeout=10)
        print("[Запрос] Страница загружена")
    except Exception as e:
        print("[Ошибка] Ошибка загрузки страницы:", e)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')[1:]
    print(f"[Строки] Найдено строк (тендеров): {len(rows)}")

    try:
        existing_ids = [row[0] for row in worksheet.get_all_values()]
        print(f"[Таблица] Считано ID из таблицы: {len(existing_ids)}")
    except Exception as e:
        print("[Ошибка] Ошибка чтения таблицы:", e)
        bot.send_message(CHAT_ID, f"[Ошибка] Ошибка чтения таблицы: {e}")
        return

    new_counter = 0

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 7:
            continue

        tender_id = cols[0].text.strip()
        announce_date = cols[5].text.strip()
        subject = cols[2].text.strip()
        price = cols[6].text.strip().replace('\xa0', ' ')
        url_suffix = cols[0].find('a')['href']
        full_url = f"https://zakupki.gospmr.org{url_suffix}"

        if tender_id not in existing_ids:
            worksheet.append_row([
                tender_id, announce_date, '', subject,
                '', '', '', '', price,
                '', '', full_url
            ])
            new_counter += 1
            print(f"[Новое] Новое объявление: {tender_id}")

            message = (
                f"[Новое объявление] *Новое объявление*\n"
                f"ID: `{tender_id}`\n"
                f"Дата: {announce_date}\n"
                f"Предмет: {subject}\n"
                f"Сумма: {price}\n"
                f"[Открыть объявление]({full_url})"
            )
            bot.send_message(CHAT_ID, message, parse_mode="Markdown", disable_web_page_preview=True)

    print(f"[ОК] Обработка завершена. Добавлено новых записей: {new_counter}")

if __name__ == "__main__":
    print("[Цикл] Вошёл в цикл while True — стартуем fetch_pmr_tenders()...")
    while True:
        try:
            fetch_pmr_tenders()
        except Exception as e:
            print("[Ошибка] Ошибка в цикле мониторинга:")
            print(traceback.format_exc())
            bot.send_message(CHAT_ID, f"[Ошибка] Ошибка при проверке тендеров: {traceback.format_exc()}")
        time.sleep(10)
