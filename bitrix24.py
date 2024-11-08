""" Этот код представляет собой пример использования Python для взаимодействия с YouTube Data API
и Google Drive API. Основная цель программы заключается в поиске видео на YouTube по заданному 
ключевому слову, сборе информации о найденных видео и сохранении этих данных в CSV-файл.
Кроме того, программа также может загружать данные в Google Диск при наличии соответствующих 
прав доступа.

Импортированные модули:
- openpyxl: Модуль для работы с файлами Excel (.xlsx). 
- requests: Модуль для для выполнения HTTP-запросов.
- datetime: Модуль предоставляет классы для работы с датами и временем.
- json: Модуль для преобразования между форматом JSON (JavaScript Object Notation) и объектами Python.
- logging: Модуль для логирования. 
"""


import openpyxl
from openpyxl.styles import Font, Alignment
import requests
from datetime import datetime
import json
import logging


# Настройка логгирования. Данные хранятся в файле youtube.log с уровнем логирования INFO. 
logging.basicConfig(
    filename = 'bitrix24.log',  
    level = logging.INFO,  
    format = '%(asctime)s - %(levelname)s - %(message)s', 
)


# Настройки констант для Bitrix24 API 
# (WEBHOOK - должен предоставлять доступ к определенным модулям)
BITRIX_WEBHOOK_URL = 'https://b24-7a3vo8.bitrix24.ru/rest/1/6r6melu78ms34zhq/'    


def get_candidate_data(candidate_id):
    """Получает данные кандидата из Bitrix24.
    Функция get_candidate_data получает данные кандидата из системы Bitrix24
    по уникальному идентификатору (candidate_id).add()
    
    :param candidate_id: уникальный идентификатор кандидата.
    :return: словарь с информацией о кандидате.
    """
    url = f"{BITRIX_WEBHOOK_URL}crm.lead.get" 
    params = {
        "id": candidate_id
    }
    response = requests.get(url, params=params)
    try:
        return response.json()  # Возвращаем данные кандидата в формате JSON
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    except ValueError:
        print("Error decoding JSON. Response:", response.text)
        return None



def save_candidate_to_excel(candidate_data, filename='candidates.xlsx'):
    """Создает Excel-файл с данными кандидата."""

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Кандидаты'
    
    # Стили заголовков
    header_font = Font(bold=True)
    align_center = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = ['ID', 'Имя', 'Фамилия', 'Телефон', 'Email', 'Дата создания']
    sheet.append(headers)
    for col, value in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=col)
        cell.value = value
        cell.font = header_font
        cell.alignment = align_center
    
    # Заполнение данных
    row_num = 2
    sheet.cell(row=row_num, column=1).value = candidate_data['result']['ID']
    sheet.cell(row=row_num, column=2).value = candidate_data['result']['NAME']
    sheet.cell(row=row_num, column=3).value = candidate_data['result']['LAST_NAME']
    sheet.cell(row=row_num, column=4).value = candidate_data['result']['HAS_PHONE'] if len(candidate_data['result']['HAS_PHONE']) > 0 else ''
    sheet.cell(row=row_num, column=5).value = candidate_data['result']['HAS_EMAIL'] if len(candidate_data['result']['HAS_EMAIL']) > 0 else ''
    sheet.cell(row=row_num, column=6).value = datetime.strptime(candidate_data['result']['DATE_CREATE'], '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y')
    row_num += 1

    
    filename = f"candidate_{candidate_data['result']['ID']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    workbook.save(filename)
    return f"Данные кандидата сохранены в {filename}"
        