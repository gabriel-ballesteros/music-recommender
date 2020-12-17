import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
import itertools

tracks_list = pd.read_csv('data/tracks-list.csv')
tracks_list.drop(['Name','Artist','Year','Album','Key','Mode'], axis='columns', inplace=True)
tracks_list.set_index('Id', inplace=True)
tracks_list.drop('Unnamed: 0',axis='columns',inplace=True)
cols = tracks_list.columns.str.lower()
indx = tracks_list.index
scaler = StandardScaler()
tracks_list = scaler.fit_transform(tracks_list)
tracks_list = pd.DataFrame(tracks_list,index=indx,columns=cols)

def create_similarity(song, dataframe):
    distance_vector = cdist(XA=song,XB=dataframe)
    similarities = 1 / (1 + distance_vector)    
    similarity_index = pd.DataFrame(similarities, columns=dataframe.index)
    return similarity_index

def get_recommendation(features_list):
    result_list = []
    for features in features_list:
        features = dict(itertools.islice(features.items(), 11))
        features.pop('key', None)
        features.pop('mode', None)
        song = pd.DataFrame(columns=['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo'])
        song = song.append(features, ignore_index=True)
        song = scaler.transform(song)
        results = create_similarity(song,tracks_list).T[0].sort_values(ascending=False).reset_index()
        result_list.append(results[results[0]<1].loc[0,'Id'])
    return result_list