# сделать try/ex + описание проекта

import asyncio
import csv
import os
import requests
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

 
# Настройки YouTube Data API  our_youtube_api_key
YOUTUBE_API_KEY = 'Ar_youtube_api_key'  # заменить на Ваш API_KEY
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = 'https://www.googleapis.com/youtube/v3/videos'

# Настройки Google Drive
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'  # заменить на путь к файлу с данными SERVICE_ACCOUNT_FILE
SCOPES = ['https://www.googleapis.com/auth/drive.file'] # права доступа 


# Настройка логгирования. Данные хранятся в файле api.log с уровнем логирования INFO. 
logging.basicConfig(
    filename = 'youtube.log',  
    level = logging.INFO,  
    format = '%(asctime)s - %(levelname)s - %(message)s', 
)


def search_youtube(query: str, maxResults: int = 50) -> dict:
    """Ищет видео на YouTube по ключевому слову."""
    
    logging.info(f'start search - {query}')
    
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
        logging.error(e)

async def fetch_video_details(video_id: str) -> dict:
    """Получает детали видео по его ID."""
    logging.info(f'start function fetch_video_details')
    video_details_url = f'{VIDEO_URL}?part=statistics,snippet&id={video_id}&key={YOUTUBE_API_KEY}'
    try: 
        response = requests.get(video_details_url)
        return response.json()
    except Exception as e:
        logging.error(e)

async def gather_video_info(video_data: dict) -> dict:
    """Собирает информацию о каждом видео."""
    logging.info('start gather_video_info')
    
    tasks = []
    for item in video_data['items']:
        video_id = item['id']['videoId']
        tasks.append(fetch_video_details(video_id))
    try:
        video_details = await asyncio.gather(*tasks)
        return video_details
    except Exception as e:
        logging.error(e)

def save_to_csv(video_details: dict, filename: str):
    """Сохраняет информацию о видео в CSV файл."""
    logging.info(f'save_to_csv filename - {filename}')
    
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


async def main():
    """Основная функция."""
    
    query = input("Введите ключевое слово для поиска: ")
    video_data = search_youtube(query)
    try:
        if video_data:
            video_info = await gather_video_info(video_data)
    
            save_to_csv(video_info, filename ='youtube_videos.csv')
   
            logging.info(f'Video data is saved in youtube_videos.csv')
            print(f'Данные о видео сохранены в youtube_videos.csv')
    except Exception as e:
            logging.error(e)

        

def upload_to_drive(filename):
    """Загружает файл в Google Drive."""
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': filename}
    media = MediaFileUpload(filename, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f'Файл загружен в Google Drive с ID: {file.get("id")}')


if __name__ == "__main__":
    asyncio.run(main())

    upload_to_drive('youtube_videos.csv')