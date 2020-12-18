import pandas as pd
import spotipy
import numpy as np
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
from time import sleep

SPOTIFY_CLIENT_ID = 'dc12d6a903334c1bbb4d620e80eaa29d'
SPOTIFY_CLIENT_SECRET = '16df91a2ac314e70aadca96ab74a2dff'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

data = pd.read_csv('data/song_data.csv')
data.drop(['song_id'], axis='columns', inplace=True)
data.columns = ['name', 'album', 'artist', 'year']

artistas = data.groupby(by='artist').agg(nro=('name','count')).reset_index().sort_values(by='nro', ascending=False).head(500)['artist'].tolist()
artistas = [x for x in artistas if 'feat.' not in x and '/' not in x]
artists_id_list = pd.DataFrame(columns=['Id','Name','Genres','Popularity','Img'])

for coso in tqdm(artistas):
    if coso.lower() not in artists_id_list.Name.str.lower().tolist():
        response = sp.search(q=coso.replace(' ', '+'), limit=2, type='artist')['artists']['items']
        if len(response) == 0:
            artists_id_list.loc[len(artists_id_list)] = [np.nan, coso, np.nan, np.nan, np.nan]
        else:
            artist_data = response[0]
        artists_id_list.loc[len(artists_id_list)] = [artist_data['id'],artist_data['name'],
                                                     artist_data['genres'], artist_data['popularity'], artist_data['images'][0]]
        sleep(2.5)

artists_id_list.dropna(inplace=True)
artists_id_list.to_csv('artists-dataset.csv')
pd.get_dummies(artists_id_list['Genres'].apply(pd.Series).stack()).sum(level=0).columns.tolist()
artists_id_list = pd.read_csv('artists-dataset.csv')
artist_list = artists_id_list['Id'].tolist()

tracks_list = pd.DataFrame(columns=['Id','Name','Artist','Album','Year','Danceability','Energy','Key',
                                    'Loudness','Mode','Speechiness','Acousticness','Instrumentalness',
                                    'Liveness','Valence','Tempo'])

for artist_id in tqdm(artist_list):
    albums = sp.artist_albums(artist_id,'album,single')['items']
    sleep(2)
    for album in albums:
        if album['name'].lower() not in tracks_list.Album.str.lower().unique() and album['name'].lower() not in ['homegrown']:
            album_tracks = sp.album_tracks(album['id'])['items']
            sleep(1)
            album_tracks_id = [track['id'] for track in album_tracks]
            sleep(1)
            tracks = sp.tracks(album_tracks_id)['tracks']
            sleep(1)
            features = sp.audio_features(album_tracks_id)
            sleep(1)
            print(album['name'])
            d = {'Id':[track['id'] for track in tracks],
                 'Name':[track['name'] for track in tracks],
                'Artist':[', '.join([artist['name'] for artist in track['artists']]) for track in tracks],
                 'Album':[track['album']['name'] for track in tracks],
                 'Year':[track['album']['release_date'][:4] for track in tracks],
                 'Danceability':[feature['danceability'] for feature in features],
                 'Energy':[feature['energy'] for feature in features],
                 'Key':[feature['key'] for feature in features],
                 'Loudness':[feature['loudness'] for feature in features],
                 'Mode':[feature['mode'] for feature in features],
                 'Speechiness':[feature['speechiness'] for feature in features],
                 'Acousticness':[feature['acousticness'] for feature in features],
                 'Instrumentalness':[feature['instrumentalness'] for feature in features],
                 'Liveness':[feature['liveness'] for feature in features],
                 'Valence':[feature['valence'] for feature in features],
                 'Tempo':[feature['tempo'] for feature in features]
                }
            tracks_list = tracks_list.append(pd.DataFrame(d),ignore_index=True)

#original_list = pd.read_csv('data/tracks-list.csv')
#tracks_list = original_list.copy()
#tracks_list.drop(['Name','Artist','Year','Album','Key','Mode'], axis='columns', inplace=True)
