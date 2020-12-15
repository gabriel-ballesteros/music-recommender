import streamlit as st
import pandas as pd
import spotipy
from PIL import Image
from utils import parameters, session, data
from spotipy.oauth2 import SpotifyClientCredentials
from scipy.spatial.distance import pdist, squareform

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=parameters.SPOTIFY_CLIENT_ID, client_secret=parameters.SPOTIFY_CLIENT_SECRET))

def search_track(query):
    search_dict = {}
    # Query the DB for the song if null go to the API and add it to the DB
    results = sp.search(q=query, limit=10, type='track')
    for track in results['tracks']['items']:
        search_dict[(track['name'], ' , '.join([artist['name'] for artist in track['artists']]), track['album']['name'], track['album']['release_date'][:4])] = track['id']
    return search_dict

def get_audio_features(id):
    features = sp.audio_features(id)[0]
    df = pd.DataFrame([(key, features[key]) for key in features.keys()])
    df.columns = ['Feature','Value']
    return df

image = Image.open('img/jukebox.jpg')
st.title('Music Recommender')
st.image(image,width=400)
st.write('You can search for songs on Spotify and I will recommend you similar songs based on its features. All you have to do is add songs to the list and click on "Recommend"')
st.markdown('## Input')
query = st.text_input('Search for a music track: ')

if query != '':
    results = search_track(query)
    selection = st.selectbox('Choose from the result list',list(results.keys()))
    track_id = results[selection]
    row = list(selection)
    row.append(track_id)

    if st.button(label='Add to list'):
        if len(session.get_track_list()) > 10:
            st.error('Too many tracks! Maximum of 10 tracks permitted')
        else:
            if session.add_track(row):
                st.error('The track is already in the list!')

    track_table = st.empty()
    track_table.dataframe(session.get_track_list())

    session.artists_in_list = st.checkbox('Exclude artists already in the list')
    session.genres = st.multiselect(label='Select the desired genres', options=data.tracks.Genre.unique())

    if st.button(label='Empty the track list'):
        session.empty_track_list()
        track_table.empty()
        track_table.dataframe(session.get_track_list())

    if st.button(label='Submit tracks for recommendation'):
        if len(session.get_track_list()) == 0:
            st.error('The track list is empty! Please add songs before submitting')
        else:
            st.markdown('## Recommendations')
            # Look for recommendations
            pass