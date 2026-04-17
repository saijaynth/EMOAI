import httpx
token = __import__('app.services.recommender', fromlist=['_spotify_get_token'])._spotify_get_token()
headers = {'Authorization': 'Bearer ' + token}
search_resp = httpx.get('https://api.spotify.com/v1/search', headers=headers, params={'q': 'happy pop', 'type': 'playlist', 'limit': 2, 'market': 'US'})
print('Search:', search_resp.json())
