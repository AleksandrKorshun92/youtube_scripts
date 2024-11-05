""" Этот код представляет собой пример использования Python для взаимодействия с YouTube Data API
и Google Drive API. Основная цель программы заключается в поиске видео на YouTube по заданному 
ключевому слову, сборе информации о найденных видео и сохранении этих данных в CSV-файл.
Кроме того, программа также может загружать данные в Google Диск при наличии соответствующих 
прав доступа.

Импортированные модули:
- google.oauth2: Модуль для доступа к API Google работы с аутентификацией и авторизацией через протокол OAuth 2.0
- googleapiclient: Модуль для взаимодействия с API Google.
- asyncio: Асинхронная библиотека Python.
- csv: Модуль для работы с файлами формата CSV (запись, чтение).
- aiohttp: Библиотека для асинхронного HTTP-клиента (для отправки Api запросов)
- requests: Модуль для для выполнения HTTP-запросов.
- logging: Модуль для логирования. 
"""


from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import asyncio
import csv
import aiohttp
import requests
import logging


# Настройки констант для YouTube Data API 
YOUTUBE_API_KEY = 'our_youtube_api_key'  # заменить на Ваш API_KEY
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = 'https://www.googleapis.com/youtube/v3/videos'

# Настройки констант для Google Drive
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'  # заменить на путь к файлу с данными 
SCOPES = ['https://www.googleapis.com/auth/drive.file'] 


# Настройка логгирования. Данные хранятся в файле youtube.log с уровнем логирования INFO. 
logging.basicConfig(
    filename = 'youtube.log',  
    level = logging.INFO,  
    format = '%(asctime)s - %(levelname)s - %(message)s', 
)


def search_youtube(query: str, maxResults: int = 50) -> dict:
    """Функция ищет видео на YouTube по ключевому слову.
    
    :param query: ключевое слово для поиска видео.
    :param maxResults: максимальное количество видео установлено по умолчанию 50.
    :return: словарь с информацией о найденных видео.
    """
    
    logging.info(f'start search - {query}')
    
    # основные параметр для получения ланных о видео
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': YOUTUBE_API_KEY,
        'maxResults': maxResults
    }
    try: 
        response = requests.get(YOUTUBE_API_URL, params=params)
        return response.json()
    except Exception as e:
        logging.exception("Error executing request: %s", e)
        return {}


async def fetch_video_details(video_id: str) -> dict:
    """Асинкронная функция, которая получает детали видео по его ID.
    
    :param video_id: id видео для получения данных по данному видео.
    :return: словарь с расширенной информацией о видео.
    """
    
    logging.info(f'start function fetch_video_details')
    video_details_url = f'{VIDEO_URL}?part=statistics,snippet&id={video_id}&key={YOUTUBE_API_KEY}'
    try: 
        async with aiohttp.ClientSession() as session:
            async with session.get(video_details_url) as response:
                return await response.json()
    except aiohttp.ClientError as e:
        logging.error(f"Error executing request: {e}")
        return {}


async def gather_video_info(video_data: dict) -> dict:
    """Асинкронная функция которая собирает информацию о каждом видео для дальнейшей записи.
    В цикле прохлдит по каждому видео, находит id и через функцию fetch_video_details получает
    расширинные данные необходимые для дальнейшей записи (обработки)
    
    :param video_data: словарь найденных видео
    :return: словарь с расширенной информацией о видео.
    """
    logging.info('start gather_video_info')
    
    tasks = []
    for item in video_data['items']:
        video_id = item['id']['videoId']
        tasks.append(fetch_video_details(video_id))
    try:
        video_details = await asyncio.gather(*tasks)
        return video_details
    except Exception as e:
        logging.error(f"Error executing request: {e}")
        return {}


def save_to_csv(video_details: dict, filename: str) -> str:
    """Сохраняет информацию о видео в CSV файл.
    
    :param video_details: словарь данных о видео
    :param filename: названия файла, куда будет сохранятся информация
    :return: информацию, что данные сохранены в файл.
    """
    logging.info(f'save_to_csv filename - {filename}') 
    
    # проверка на правильный формат для сохранения файла. Если формата нет или другой, 
    # то будет изменен формат
    if 'csv' not in filename.split('.'):
        filename = filename + '.csv'
    #открытие менеджера для записи с указанием кодировки utf-8.
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title (Название видео)', 
                         'Channel (Название канала)',
                         'Views (Количество просмотров)', 
                         'Likes (Количество лайков)', 
                         'Comments (Количество комментариев)'])
        for details in video_details:
            if details['items']:
                snippet = details['items'][0]['snippet']
                statistics = details['items'][0]['statistics']
                writer.writerow([
                    snippet['title'],
                    snippet['channelTitle'],
                    statistics.get('viewCount', 0),
                    statistics.get('likeCount', 0),
                    statistics.get('commentCount', 0)
                ])
    return f'Данные о видео сохранены в {filename}'



def upload_to_drive(filename: csv) -> str:
    """Загружает файл в c данными о видео в Google Drive.
    
    :param filename: названия файла, который необходимо сохранить в Google Drive
    :return: информацию, что данные сохранены в файл.
    """
    
    logging.info(f'upload_to_drive in Google Drive - {filename}')
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': filename}
    media = MediaFileUpload(filename, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return f'Файл загружен в Google Drive с ID: {file.get("id")}'


async def main():
    """ Основная асинхронная функция которая получает информацию о данных для поиска видео,
    после чего вызывает функцию search_youtube, осуществляет поиск, если все успешно вызывает функцию
    gather_video_info для получения необходиых данных о видео.
    После чего производиться запиьс данных в функции save_to_csv в файл формата csv
    """
    
    query = input("Введите ключевое слово для поиска: ")
    video_data = search_youtube(query)
    try:
        if video_data:
            video_info = await gather_video_info(video_data)
            print(save_to_csv(video_info, filename ='youtube_videos.csv'))
            logging.info(f'Video data is saved in youtube_videos.csv')
            print(upload_to_drive('youtube_videos.csv'))
            logging.info(f'File is saved in Google Drive')
    except Exception as e:
            logging.error(f'error when searching and writing data: {e}')
        

if __name__ == "__main__":
    asyncio.run(main())

