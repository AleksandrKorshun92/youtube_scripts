import unittest
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import requests
from aiohttp import ClientResponseError
from aiohttp.helpers import BasicAuth
import asyncio


from youtube import search_youtube, fetch_video_details, gather_video_info, save_to_csv, upload_to_drive

class TestYoutubeFunctions(unittest.TestCase):

    @patch('requests.get')
    def test_search_youtube_success(self, mock_get):
        # Настроим mock-ответ
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [{'id': {'videoId': '12345'}}]
        }
        mock_get.return_value = mock_response

        # Вызов функции
        result = search_youtube('test_query')

        # Assert
        self.assertEqual(result, {'items': [{'id': {'videoId': '12345'}}]})
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_search_youtube_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP error")

        result = search_youtube('test_query')

        # Assert
        self.assertEqual(result, {})
        mock_get.assert_called_once()

    @patch('aiohttp.ClientSession.get', new_callable=AsyncMock)
    @patch('aiohttp.ClientSession.__aenter__', new_callable=AsyncMock)
    @patch('aiohttp.ClientSession.__aexit__', new_callable=AsyncMock)
    def test_fetch_video_details_success(self, mock_aexit, mock_aenter, mock_get):
        mock_aenter.return_value = MagicMock()
        mock_aenter.return_value.get.return_value.__aenter__.return_value.json.return_value = {
            'id': '12345',
            'snippet': {'title': 'Sample Video'},
            'statistics': {'viewCount': '1000'}
        }

        # Вызов функции
        result = asyncio.run(fetch_video_details('12345'))

        # Assert
        self.assertEqual(result['id'], '12345')
        self.assertEqual(result['snippet']['title'], 'Sample Video')

    @patch('aiohttp.ClientSession.get', new_callable=AsyncMock)
    @patch('aiohttp.ClientSession.__aenter__', new_callable=AsyncMock)
    @patch('aiohttp.ClientSession.__aexit__', new_callable=AsyncMock)
    def test_fetch_video_details_failure(self, mock_aexit, mock_aenter, mock_get):
        mock_aenter.return_value = MagicMock()
        mock_get.side_effect = ClientResponseError(
            request_info=MagicMock(),  # Создаем фиктивный объект для request_info
            history=[]  # Пустой список истории
        )

        result = asyncio.run(fetch_video_details('12345'))

        # Assert
        self.assertEqual(result, {})

    @patch('youtube.fetch_video_details', new_callable=AsyncMock)
    def test_gather_video_info_success(self, mock_fetch_video_details):
        mock_fetch_video_details.side_effect = [{
            'id': '12345',
            'snippet': {'title': 'Sample Video'},
            'statistics': {'viewCount': '1000'}
        }] * 2

        video_data = {
            'items': [
                {'id': {'videoId': '12345'}},
                {'id': {'videoId': '67890'}}
            ]
        }

        result = asyncio.run(gather_video_info(video_data))
        
        # Assert
        self.assertEqual(result['12345']['id'], '12345')
        self.assertEqual(result['67890']['id'], '67890')

    @patch('youtube.fetch_video_details', new_callable=AsyncMock)
    def test_gather_video_info_with_error(self, mock_fetch_video_details):
        # Задаём ошибку для одного из вызовов
        mock_fetch_video_details.side_effect = [Exception("Error"), 
            {'id': '67890', 'snippet': {'title': 'Sample Video'}, 'statistics': {'viewCount': '1000'}}]

        video_data = {
            'items': [
                {'id': {'videoId': '12345'}},
                {'id': {'videoId': '67890'}}
            ]
        }

        result = asyncio.run(gather_video_info(video_data))

        # Assert
        self.assertEqual(result['67890']['id'], '67890')
        self.assertNotIn('12345', result)


    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_save_to_csv_success(self, mock_csv_writer, mock_open):
        # Подготовка данных
        video_details = [
            {
                'items': [
                    {
                        'snippet': {'title': 'Test Video', 'channelTitle': 'Test Channel'},
                        'statistics': {'viewCount': '1000', 'likeCount': '100', 'commentCount': '10'}
                    }
                ]
            }
        ]

        # Вызов функции
        result = save_to_csv(video_details, 'testfile')

        # Assert
        self.assertEqual(result, 'Video data is saved in testfile.csv')
        mock_open.assert_called_once_with('testfile.csv', mode='w', newline='', encoding='utf-8')
        mock_csv_writer.return_value.writerow.assert_called_with(['Title (Название видео)', 
                                                                  'Channel (Название канала)',
                                                                  'Views (Количество просмотров)', 
                                                                  'Likes (Количество лайков)', 
                                                                  'Comments (Количество комментариев)'])

        # Проверить, что была вызвана запись строки с деталями
        mock_csv_writer.return_value.writerow.assert_any_call(['Test Video', 
                                                               'Test Channel', 
                                                               '1000', 
                                                               '100', 
                                                               '10'])

    @patch('builtins.open', new_callable=mock_open)
    def test_save_to_csv_no_data(self, mock_open):
        # Без данных
        video_details = []
        
        # Вызов функции
        result = save_to_csv(video_details, 'testfile')

        # Assert
        self.assertEqual(result, 'No video data to save in testfile.csv')
        mock_open.assert_not_called()  # Убедитесь, что open не был вызван

    @patch('os.path.isfile', return_value=True)
    @patch('googleapiclient.discovery.build')
    @patch('googleapiclient.http.MediaFileUpload')
    @patch('your_module.service_account.Credentials.from_service_account_file')
    def test_upload_to_drive_success(self, mock_creds, mock_media_file_upload, mock_build, mock_isfile):
        # Предоставляем mock для сервиса google drive
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.files.return_value.create.return_value.execute.return_value = {'id': '12345'}

        # Вызов функции
        result = upload_to_drive('testfile.csv')

        # Assertions
        self.assertEqual(result, 'The file is uploaded to Google Drive with ID: 12345')
        mock_isfile.assert_called_once_with('testfile.csv')
        mock_creds.assert_called_once_with(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        mock_service.files.return_value.create.assert_called_once()
        
    @patch('os.path.isfile', return_value=False)
    def test_upload_to_drive_file_not_exist(self, mock_isfile):
        result = upload_to_drive('non_existing_file.csv')
        self.assertEqual(result, 'Error: File not found - non_existing_file.csv')

if __name__ == '__main__':
    unittest.main()