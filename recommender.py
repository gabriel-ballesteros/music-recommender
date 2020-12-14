import streamlit as st
import numpy as np
import pandas as pd
import spotipy
import re
from PIL import Image
from utils import parameters
from spotipy.oauth2 import SpotifyClientCredentials
from scipy.spatial.distance import pdist, squareform

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=parameters.SPOTIFY_CLIENT_ID, client_secret=parameters.SPOTIFY_CLIENT_SECRET))

def search_track(query):
    combo_list = {}
    # Query the DB for the song if null go to the API and add it to the DB
    results = sp.search(q=query, limit=10, type='track')
    for track in results['tracks']['items']:
        combo_list[(track['name'], ' , '.join([artist['name'] for artist in track['artists']]), track['album']['name'])] = track['id']
    return combo_list

def audio_features(id):
    results = sp.audio_features(id)[0]
    df = pd.DataFrame([(key, results[key]) for key in results.keys()])
    df.columns = ['Feature','Value']
    return df

image = Image.open('img/jukebox.jpg')
st.title('Music Recommender')
st.image(image,width=400)
st.write('You can search for songs on Spotify and I will recommend you similar songs based on its features (energy, danceability, acousticness, key, etc)')
st.markdown('## Input')
query = st.text_input('Search for a music track: ')
if query != '':
    search = search_track(query)
    st.dataframe(audio_features(search[st.selectbox('Choose from the result list',list(search.keys()))])[0:11])
    st.markdown('## Recommendations')
    # Load a dataframe with music features
    # Look for recommendations