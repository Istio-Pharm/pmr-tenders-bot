
import time
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from bs4 import BeautifulSoup

# Google Sheets setup
SPREADSHEET_ID = '1KJcufLBYkhfPh5gRSJkAT3fsiiJ_X28_itqq7Ijrf9g'
GOOGLE_DRIVE_FOLDER_ID = '1M0KnqX5bCvB33OTZDHoqu9CsJ8Nu0n9K'
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

# Авторизация
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
gc = gspread.authorize(creds)

gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

# Получение таблицы
worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Загрузка и логика
def fetch_pmr_tenders():
    url = "https://example.com/pmr_tenders"  # Поставить актуальную ссылку
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Пример поиска: заменить на актуальный парсинг
    tenders = soup.find_all('div', class_='tender')
    for tender in tenders:
        tender_id = tender.get('data-id')
        announce_date = tender.find('span', class_='announce').text
        close_date = tender.find('span', class_='close').text
        subject = tender.find('div', class_='subject').text
        lot = tender.find('div', class_='lot').text
        product = tender.find('div', class_='product').text
        unit = tender.find('div', class_='unit').text
        quantity = tender.find('div', class_='qty').text
        price = tender.find('div', class_='price').text
        rate = tender.find('div', class_='rate').text
        price_per_unit = tender.find('div', class_='ppu').text
        url = tender.find('a', class_='details').get('href')

        # Проверка на дублирование по ID
        existing_ids = [row[0] for row in worksheet.get_all_values()]
        if tender_id not in existing_ids:
            worksheet.append_row([
                tender_id, announce_date, close_date, subject,
                lot, product, unit, quantity, price,
                rate, price_per_unit, url
            ])
            print(f"Добавлено новое объявление: {tender_id}")

# Запуск
if __name__ == "__main__":
    while True:
        try:
            fetch_pmr_tenders()
        except Exception as e:
            print("Ошибка:", e)
        time.sleep(3600)
