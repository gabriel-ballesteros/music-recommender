import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
import itertools
import ast
from utils import session

tracks_list_original = pd.read_csv('data/tracklist.csv')
tracks_list = tracks_list_original.copy()

def get_tracks_list_original():
    return tracks_list_original

def get_tracks_list():
    return tracks_list

def get_artists_genres():
    flat_list = []
    for genres in tracks_list_original.Genres.unique():
        sublist = ast.literal_eval(genres)
        for item in sublist:
            flat_list.append(item)
    genres = list(dict.fromkeys(flat_list))
    genres.sort()
    return genres

def create_similarity(song, dataframe):
    distance_vector = cdist(XA=song,XB=dataframe,metric='euclidean')
    similarities = 1 / (1 + distance_vector)    
    similarity_index = pd.DataFrame(similarities, columns=dataframe.index)
    return similarity_index

def get_recommendation(features_list):
    tracks_list = tracks_list_original.copy()
    result_list = []
    match_list = []

    tracks_list = tracks_list.loc[(tracks_list.Year >= session.from_year) & (tracks_list.Year <= session.to_year)]

    if session.exclude_artists:
        pattern = '|'.join(session.get_track_list().Artist.tolist())
        tracks_list = tracks_list.loc[~tracks_list.Artist.str.contains(pattern)]

    if session.less_popular_artists:
        tracks_list = tracks_list.loc[tracks_list.Popularity < 50]

    if session.only_in_genres:
        pattern = '|'.join(session.genres)
        tracks_list = tracks_list.loc[tracks_list.Genres.str.contains(pattern)]

    tracks_list.drop(['Name','Artist','Year','Album','Key','Mode','Loudness','Genres','Popularity','Img', 'Unnamed: 0'], axis='columns', inplace=True) #add genres
    tracks_list.set_index('Id', inplace=True)
    cols = tracks_list.columns.str.lower()
    indx = tracks_list.index
    scaler = StandardScaler()
    tracks_list = scaler.fit_transform(tracks_list)
    tracks_list = pd.DataFrame(tracks_list,index=indx,columns=cols)

    for features in features_list:
        features = dict(itertools.islice(features.items(), 11))
        features.pop('key', None)
        features.pop('mode', None)
        features.pop('loudness', None)
        song = pd.DataFrame(columns=['danceability','energy','speechiness','acousticness','instrumentalness','liveness','valence','tempo'])
        song = song.append(features, ignore_index=True)
        song = scaler.transform(song)
        results = create_similarity(song,tracks_list).T[0].sort_values(ascending=False).reset_index()
        result_list.append(results.loc[results[0]<0.95, 'Id'].reset_index(drop=True)[0])
        match_list.append(results.loc[results[0]<0.95, 0].reset_index(drop=True)[0])
    return [result_list, match_list]