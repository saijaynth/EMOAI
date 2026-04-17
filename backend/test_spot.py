import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()
try:
    cid = os.getenv('SPOTIFY_CLIENT_ID')
    csec = os.getenv('SPOTIFY_CLIENT_SECRET')
    if not cid:
        print('No cid')
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=csec))
    res = sp.search(q='happy', type='track', limit=5)
    for t in res['tracks']['items']:
        print(t['name'], t['artists'][0]['name'], 'pop:', t['popularity'])
except Exception as e:
    print('Error:', e)
