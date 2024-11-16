""" 
The script allows you to search for videos on YouTube according to a given 
keyword, collects information and saves the data in a CSV file.
There is also a function for uploading data to Google Drive if appropriate 
access rights.

Imported modules:
- google.oauth2: Module for accessing the Google API for working with authentication and authorization via the OAuth 2.0 protocol
- googleapiclient: A module for interacting with the Google API.
- asyncio: Python asynchronous library.
- csv: Module for working with CSV files (writing, reading).
- aiohttp: Library for an asynchronous HTTP client (for sending Api requests)
- requests: Module for making HTTP requests.
- logging: Module for logging.
- os: Module for working with files.
"""


from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import asyncio
import csv
import aiohttp
import requests
import logging
import os


# Constant settings for YouTube Data API
YOUTUBE_API_KEY = 'our_youtube_api_key'  # replace with your API_KEY
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = 'https://www.googleapis.com/youtube/v3/videos'

# Constant settings for Google Drive
# SERVICE_ACCOUNT_FILE - replace with the path to the data file (downloaded Google account in json format)
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'  # example with title - project_google_api.json
SCOPES = ['https://www.googleapis.com/auth/drive.file'] 


# Setting up logging. The data is stored in the youtube.log file with INFO logging level.
logging.basicConfig(
    filename = 'youtube.log',  
    level = logging.INFO,  
    format = '%(asctime)s - %(levelname)s - %(message)s', 
)


def search_youtube(query: str, maxResults: int = 50) -> dict:
    """The function searches YouTube videos by keyword.
    
    :param query: keyword for video search.
    :param maxResults: The maximum number of videos is set to 50 by default.
    :return: dictionary with information about found videos.
    """
    
    logging.info(f'start search - {query}')
    
    # basic parameters for receiving data about the video
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
    except requests.exceptions.HTTPError as http_err:
        logging.error("HTTP error occurred: %s", http_err)
    except requests.exceptions.ConnectionError as conn_err:
        logging.error("Connection error occurred: %s", conn_err)
    except requests.exceptions.Timeout as timeout_err:
        logging.error("Request timed out: %s", timeout_err)
    except requests.exceptions.RequestException as req_err:
        logging.error("An error occurred: %s", req_err)
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)     
    return {}


async def fetch_video_details(video_id: str) -> dict:
    """An asynchronous function that gets video details by its ID.
    
    :param video_id: video id for obtaining data for this video.
    :return: dictionary with extended information about the video.
    """
    
    logging.info(f'start function fetch_video_details')
    video_details_url = f'{VIDEO_URL}?part=statistics,snippet&id={video_id}&key={YOUTUBE_API_KEY}'
    try: 
        async with aiohttp.ClientSession() as session:
            async with session.get(video_details_url) as response:
                return await response.json()
    except aiohttp.ClientResponseError as http_err:
        logging.error("HTTP error occurred: %s", http_err)
    except aiohttp.ClientConnectionError as conn_err:
        logging.error("Connection error occurred: %s", conn_err)
    except aiohttp.ClientTimeout as timeout_err:
        logging.error("Request timed out: %s", timeout_err)
    except aiohttp.ClientError as client_err:
        logging.error("A client error occurred: %s", client_err)
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)
    
    return {}


async def gather_video_info(video_data: dict) -> dict:
    """An asynchronous function that collects information about each video for further recording.
    It loops through each video, finds the id and gets it through the fetch_video_details function
    extended data necessary for further recording (processing)
    
    :param video_data: dictionary of found videos
    :return: dictionary with extended information about the video.
    """
    logging.info('Start gather_video_info')
    
    tasks = []
    for item in video_data.get('items', []):
        video_id = item.get('id', {}).get('videoId')
        if video_id:
            tasks.append(fetch_video_details(video_id))
        else:
            logging.warning("No video ID found for item: %s", item)

    try:
        video_details = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out any exceptions and log them
        for detail in video_details:
            if isinstance(detail, Exception):
                logging.error("Error fetching video details: %s", detail)
        return {video['id']: detail for video, detail in zip(video_data['items'], video_details) if not isinstance(detail, Exception)}

    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        return {}


def save_to_csv(video_details: dict, filename: str) -> str:
    """ Saves video information to a CSV file.
    
    :param video_details: video data dictionary
    :param filename: name of the file where the information will be saved
    :return: information that the data is saved to the file.
    """
    logging.info(f'save_to_csv filename - {filename}')

    # Checks for the correct format to save the file.
    if not filename.endswith('.csv'):
        filename += '.csv'

    try:
        # Opening a manager for a record indicating the utf-8 encoding
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title (Название видео)', 
                             'Channel (Название канала)',
                             'Views (Количество просмотров)', 
                             'Likes (Количество лайков)', 
                             'Comments (Количество комментариев)'])
            
            # Checking for data in video_details
            if not isinstance(video_details, list) or not video_details:
                logging.warning("No video details provided or video_details is not a list.")
                return f'No video data to save in {filename}.'

            for details in video_details:
                if 'items' in details and details['items']:
                    snippet = details['items'][0].get('snippet', {})
                    statistics = details['items'][0].get('statistics', {})
                    writer.writerow([
                        snippet.get('title', 'N/A'),  # We use N/A if there is no data
                        snippet.get('channelTitle', 'N/A'),
                        statistics.get('viewCount', 0),
                        statistics.get('likeCount', 0),
                        statistics.get('commentCount', 0)
                    ])
    except (IOError, OSError) as file_err:
        logging.error(f"Error writing to file {filename}: {file_err}")
        return f"Error saving data to {filename}"
    except Exception as e:
        logging.exception("An unexpected error occurred while saving to CSV.")
        return "An unexpected error occurred when saving the data."

    return f'Video data is saved in {filename}'



def upload_to_drive(filename: csv) -> str:
    """Uploads a file with video data to Google Drive.
    
    :param filename: name of the file to be saved to Google Drive
    :return: information that the data is saved to the file.
    """
    
    logging.info(f'Uploading to Google Drive: {filename}')
    
    # Checking for file existence
    if not os.path.isfile(filename):
        logging.error(f'File not found: {filename}')
        return f'Error: File not found - {filename}'
    
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {'name': os.path.basename(filename)}  # We only get the file name
        media = MediaFileUpload(filename, mimetype='text/csv')
        
        # Making a file download request
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logging.info(f'File uploaded successfully with ID: {file.get("id")}')
        
        return f'The file is uploaded to Google Drive with ID: {file.get("id")}'
    
    except FileNotFoundError as fnf_error:
        logging.error(f'File not found: {fnf_error}')
        return f'Error: File not found - {fnf_error}'
    except HttpError as http_err:
        logging.error(f'An HTTP error occurred: {http_err}')
        return f'Error: HTTP error occurred - {http_err}'
    except Exception as e:
        logging.exception('An unexpected error occurred while uploading to Google Drive.')
        return 'An unexpected error occurred while uploading the file to Google Drive.'


async def main():
    """ The main asynchronous function that receives information about the video search data,
    after which it calls the search_youtube function, searches if everything calls the function successfully
    gather_video_info to get the necessary video data.
    Afterwards, the data is written in the save_to_csv function to a .csv file
    """
    
    query = input("Введите ключевое слово для поиска: ")
    
    try:
        video_data = search_youtube(query)
        
        if not video_data:
            logging.warning("No video data found for the query: %s", query)
            return f'There are no video data available for your request.'
        
        video_info = await gather_video_info(video_data)
        if not video_info:
            logging.warning("No video info retrieved.")
            return f"Unable to retrieve video information."
        
        csv_filename = 'youtube_videos.csv'
        save_message = save_to_csv(video_info, filename=csv_filename)
        logging.info('Video data has been saved in %s', csv_filename)
        print(save_message)

        upload_message = upload_to_drive(csv_filename)
        logging.info('File has been uploaded to Google Drive')
        print(upload_message)

    except Exception as e:
        logging.exception('An error occurred during the main process: %s', e)


if __name__ == "__main__":
    asyncio.run(main())
