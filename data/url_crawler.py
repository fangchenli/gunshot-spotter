from datetime import datetime
import json
import apiclient


channel_name = 'hickok45'
api_key = 'AIzaSyBfIXBRlvWmnmOCJoiqgBDZICRnOEuhbK8'
year_bound = 2
curr_year = datetime.now().year

# init a youtube client
youtube = apiclient.discovery.build('youtube', 'v3', developerKey=api_key)

# get channel id
res = youtube.search().list(q=channel_name, part='snippet', type='channel').execute()
channelId = ''
for item in res['items']:
    if item['snippet']['title'] == channel_name and item['snippet']['description'] != '':
        channelId = item['id']['channelId']

# get playlist id (first)
res = youtube.channels().list(id=channelId, part='contentDetails').execute()
playlistId = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

# get videos in the playlist
videos = []
next_page_token = None
while True:
    res = youtube.playlistItems().list(playlistId=playlistId,
                                       part='snippet',
                                       maxResults=50,
                                       pageToken=next_page_token).execute()

    # get the year of the first video
    video_year = datetime.fromisoformat(res['items'][0]['snippet']['publishedAt'].replace('Z', '')).year

    # only get videos from recent year
    if curr_year - video_year >= year_bound:
        break

    videos += res['items']
    next_page_token = res.get('nextPageToken')

    # break if at the last page
    if next_page_token is None:
        break

# extract time, title, and id
videos = [{'time': video['snippet']['publishedAt'].replace('Z', ''),
           'title': video['snippet']['title'],
           'id': video['snippet']['resourceId']['videoId']} for video in videos]

# write to a json file
with open(channel_name + '.json', 'w') as file:
    json.dump(videos, file)
