
import os
import time
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import telebot

# Telegram
BOT_TOKEN = "8044532856:AAFAqtS9-lRodpBkKvochtoXioOxJCBWxWE"
CHAT_ID = "442183644"

bot = telebot.TeleBot(BOT_TOKEN)

# Google Sheets
SPREADSHEET_ID = '1KJcufLBYkhfPh5gRSJkAT3fsiiJ_X28_itqq7Ijrf9g'
CREDS_FILE = 'service_account.json'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
gc = gspread.authorize(creds)
worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1

def fetch_pmr_tenders():
    print("🔍 Проверка новых тендеров...")
    url = "https://zakupki.gospmr.org/zakupki/?num=&obj=&zid=&sbj=Министерство+здравоохранения&price_from=&price_to=&request_end_from=&request_end_to=&type=none&status=none&groupe=none"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')[1:]

    existing_ids = [row[0] for row in worksheet.get_all_values()]

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
            print(f"🆕 Новое объявление: {tender_id}")

            message = (
                f"📢 *Новое объявление*\n"
                f"ID: `{tender_id}`\n"
                f"📅 Дата: {announce_date}\n"
                f"🔹 Предмет: {subject}\n"
                f"💰 Сумма: {price}\n"
                f"[Открыть объявление]({full_url})"
            )
            bot.send_message(CHAT_ID, message, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    while True:
        try:
            fetch_pmr_tenders()
        except Exception as e:
            print("🚨 Ошибка:", e)
            bot.send_message(CHAT_ID, f"🚨 Ошибка при проверке тендеров:\n{e}")
        time.sleep(60)
