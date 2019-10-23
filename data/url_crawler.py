import apiclient

channel_name = 'hickok45'

api_key = 'AIzaSyBfIXBRlvWmnmOCJoiqgBDZICRnOEuhbK8'

youtube = apiclient.discovery.build('youtube', 'v3', developerKey=api_key)

res = youtube.search().list(q=channel_name, part='snippet', type='channel').execute()

for item in res['items']:

    if item['snippet']['title'] == channel_name:
        print(item['snippet'])
        print(item['id']['channelId'])
        print(item)
