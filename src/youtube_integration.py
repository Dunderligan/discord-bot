import json
from datetime import datetime

import requests

YOUTUBE_LINK = "https://youtu.be/ID"
last_time_checked = datetime.now().astimezone(None)

class YoutubeIntegration:
    def __init__(self, api_key):
        self.api_key = api_key
        self.monitored_channels = []
        self.callbacks = []
        # Initialize YouTube API client here

    def monitor_channel(self, channel_id):
        # Code to monitor the specified YouTube channel for new videos
        self.monitored_channels.append(channel_id)


    def add_new_video_callback(self, callback):
        # Code to set a callback function that will be called when a new video is detected
        self.callbacks.append(callback)


    def fetch_latest_videos(self, channel_id):
        # Code to fetch the latest videos from the specified channel using YouTube API
        # This should return a list of YoutubeVideo objects
        response = requests.get(f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=8")
        if response.ok:
            with open("response.json", "+wb") as file:
                # log content of response
                file.write(response.content)

            print("Request was successful")
            # load bytes of response to json
            return json.loads(response.content.decode('utf-8'))
        print("Request unsuccessful")


    async def check_for_new_videos(self):
        # Code to check for new videos on the monitored channel
        latest_videos = await self.fetch_latest_videos(self.monitored_channels[0])  # Assuming monitoring one channel for simplicity
        new_videos: list[YoutubeVideo] = []
        global last_time_checked

        for video in latest_videos.get('items'):
            video_snippet = video.get('snippet')
            video_datetime: datetime = datetime.fromisoformat(video_snippet.get('publishedAt')).astimezone(None)
            # if video is newer than last time it was checked
            if video_datetime > last_time_checked:
                # save dictionary with id and title
                new_video = YoutubeVideo(
                    video.get('id').get('videoId'), 
                    video_snippet.get('title'), 
                    video_snippet.get('description'), 
                    YOUTUBE_LINK.replace("ID", video.get('id').get('videoId')))
                new_videos.append(new_video)
        
        last_time_checked = datetime.now().astimezone(None)
        for callback in self.callbacks:
            await callback(new_videos)


class YoutubeVideo:
    def __init__(self, video_id, title, description, url):
        self.video_id = video_id
        self.title = title
        self.description = description
        self.url = url

    def __str__(self):
        return f"{self.title} ({self.url})"