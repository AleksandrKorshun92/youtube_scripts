# YouTube Data & Google Drive API Integration
Этот скрипт позволяет искать видео на YouTube по ключевым словам, собирать информацию о них и сохранять результаты в формате CSV.
Также предусмотрена возможность загрузки данных в Google Drive.

## Импортируемые модули
- `google.oauth2`: Для работы с аутентификацией и авторизацией через OAuth 2.0.
- `googleapiclient`: Для взаимодействия с API Google.
- `asyncio`: Асинхронная библиотека Python.
- `csv`: Для работы с файлами формата CSV.
- `aiohttp`: Асинхронный HTTP-клиент для отправки API-запросов.
- `requests`: Для выполнения HTTP-запросов.
- `logging`: Для ведения логов.

## Функции
### search_youtube
Поиск видео на YouTube по ключевому слову. Возвращает иформацию о найденных видео.

### fetch_video_details
Получение деталей видео по его идентификатору. Возвращает подробную информацию о видео.

### gather_video_info
Сбор информации о каждом видео для последующей обработки. 

### save_to_csv
Сохранение информации о видео в CSV-файл.

### upload_to_drive
Загрузка файла с данными о видео в Google Drive.

## Установка
1. Склонируйте на свой репезиторий.
2. Установите модули
3. Создайте учетную запись разработчика на платформе Google и получите OAuth-ключи для доступа к API.
4. Следуйте инструкциям на экране для ввода необходимых параметров.

