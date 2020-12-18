import streamlit as st
import pandas as pd
import spotipy
from PIL import Image
from utils import parameters, session, recommender, data
from spotipy.oauth2 import SpotifyClientCredentials
import base64
import re
import matplotlib.pyplot as plt
import seaborn as sns

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=parameters.SPOTIFY_CLIENT_ID, client_secret=parameters.SPOTIFY_CLIENT_SECRET))

def search_track(query):
    search_dict = {}
    results = sp.search(q=query, limit=10, type='track')
    for track in results['tracks']['items']:
        search_dict[(track['name'], ' , '.join([artist['name'] for artist in track['artists']]), track['album']['name'], track['album']['release_date'][:4])] = track['id']
    return search_dict

def get_audio_features(id):
    features = sp.audio_features(id)[0]
    df = pd.DataFrame([(key, features[key]) for key in features.keys()])
    df.columns = ['Feature','Value']
    return df

banner = Image.open('img/banner.png')

file_ = open("img/loading.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

file_ = open("img/Spotify.png", "rb")
contents = file_.read()
spotify_url = base64.b64encode(contents).decode("utf-8")
file_.close()

def make_clickable(link):
    return f'<a href={link} target="_blank"><img width="50" height="50" border="0" align="center" src="data:image/png;base64,{spotify_url}"/></a>'

page = st.sidebar.selectbox(
    "Navigation",
    ("Recommender", "Track Dataset","About")
)

# Recommender Page
if page == 'Recommender':
    st.title('Music Recommender')
    st.image(banner,width=400)
    st.write('''You can search for songs on Spotify and I will recommend you similar songs based on its features. All you have to do
    is look for songs in Spotify, add them to the list, choose among the filters and click on "Recommend"''')
    st.markdown('## Input')
    query = st.text_input('Search for a music track in Spotify')

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
        track_table.dataframe(session.get_track_list().iloc[:,0:4])

        session.exclude_artists = st.checkbox('Exclude artists already in the list')

        session.less_popular_artists = st.checkbox("Don't show mainstream artists")

        session.only_in_genres = st.checkbox('Limit search to certain genres')

        genre_list = st.empty()

        if session.only_in_genres:
            session.genres = genre_list.multiselect(label='Select the desired genres', options=recommender.get_artists_genres())
        else:
            genre_list.empty()

        years = recommender.get_tracks_list_original().Year.unique().tolist()
        years.sort()
        session.from_year = st.selectbox(label='From year', options=years)
        session.to_year = st.selectbox(label='To year', options=years,index=len(years)-1)

        if st.button(label='Empty the track list'):
            session.empty_track_list()
            track_table.empty()
            track_table.dataframe(session.get_track_list().iloc[:,0:4])

        if st.button(label='Submit tracks for recommendation'):
            if len(session.get_track_list()) == 0:
                st.error('The track list is empty! Please add songs before submitting')
            else:
                if session.from_year > session.to_year:
                    st.error("The 'from year' can't be greater than the 'to year'!")
                else:
                    st.markdown('## Recommendations')
                    recommendations_df = pd.DataFrame(columns=['Track','Artist','Album','Year','Match','Link'])
                    loading = st.empty()
                    loading.markdown(f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">', unsafe_allow_html=True,)
                    recommendations_id_list = recommender.get_recommendation(sp.audio_features(session.get_track_list().Id.tolist()))
                    index = 0
                    for track in sp.tracks(recommendations_id_list[0])['tracks']:
                        col = []
                        col.append(track['name'])
                        col.append(', '.join([artist['name'] for artist in track['artists']]))
                        col.append(track['album']['name'])
                        col.append(track['album']['release_date'][:4])
                        col.append(f'{round(recommendations_id_list[1][index]*100,2)}%')
                        col.append('https://open.spotify.com/track/' + re.search('.+:(.+)', track['uri']).group(1))
                        index += 1
                        recommendations_df.loc[len(recommendations_df)] = col
                    loading.empty()
                    recommendations_df['Link'] = recommendations_df['Link'].apply(make_clickable)
                    recommendations_df = recommendations_df.to_html(escape=False)
                    st.write(recommendations_df, unsafe_allow_html=True)
                    #st.table(recommendations_df)

# Track Dataset Page
elif page == 'Track Dataset':
    st.title('The dataset')

    sns.set_context("paper", rc={"font.size":7,"axes.titlesize":7,"axes.labelsize":9})

    st.markdown('## Distributions')

    fig, ax = plt.subplots(figsize=(4,2))
    g = sns.histplot(recommender.get_tracks_list_original().groupby(by='Artist').agg(popularity = ('Popularity','mean')) ,ax=ax)
    ax.set(xlabel='Popularity count', ylabel='')
    g.legend_.remove()
    st.pyplot(fig)
    
    fig, ax = plt.subplots(figsize=(4,2))
    g = sns.histplot(recommender.get_tracks_list_original().groupby(by='Album').agg(year = ('Year','mean')), ax=ax)
    ax.set(xlabel='Albums by year', ylabel='')
    g.legend_.remove()
    st.pyplot(fig)

    st.markdown('## By artist')
    tracks = recommender.get_tracks_list_original()
    artist_list = tracks.Artist.unique()
    artist_list.sort()
    artist_selector = st.selectbox(label='Select artist', options=artist_list)
    st.write(tracks.loc[tracks.Artist == artist_selector, ['Danceability','Energy','Speechiness','Acousticness','Instrumentalness','Liveness','Valence','Tempo']].mean())

# Info Page
elif page == 'About':
    st.title('About')
    st.markdown('## Why?')
    st.markdown('''While Spotify has all our user data and can make really good guesses at what we may like, there isn't a specific search tool because
    they have an approach based on exploration and user history. This application aims to be a recommender based on a tracklist you input and filters you set, like genres,
    year range or artist popularity.''')
    st.markdown('## How does the recommender work?')
    st.markdown('''First, a dataset was created using the first 200 artists from the [Million Song Dataset](http://millionsongdataset.com/) and
    the [Spotify web API](https://developer.spotify.com/documentation/web-api/) (**1**) by getting all the albums from those artists and dumping
    them in the dataset. With the data ready, the user searches in Spotify for tracks and selects up to 10 tracks to use as input (**2**),
    then the recommender looks in the dataset the track that has most features in common (the "shortest distance" between them) and shows them
    in a list (**3**).
    ''')
    st.write('')
    diagram = Image.open('img/diagram.png')
    st.image(diagram,width=400)
    st.markdown('## Features')
    st.markdown('The features evaluated are the following ([according to spotify API documentation](https://developer.spotify.com/documentation/web-api/reference/tracks/get-several-audio-features/)):')
    st.markdown('''
    - **Acousticness**: the higher this value, a lower number of electrical amplified instruments are used
    - **Danceability**: how suitable for dancing according the tempo, rhythm stability, beat strength, and overall regularity
    - **Energy**: intensity and activity of the track, energetic tracks feel fast, loud and noisy
    - **Instrumentalness**: the higher this value, the less vocals the track has. Values above 0.5 are considered instrumental tracks, but confidence
    is higher as it approaches to 1.0
    - **Liveness**: represents the likelihood of the track being performed live. A value above 0.8 suggests the track is live.
    - **Speechiness**: presence of spoken words in the track as:
        - Above 0.66: track made entirely of spoken words (stand up show, podcast)
        - Between 0.33 and 0.66: track with both music and speech
        - Under 0.33: mostly instrumental tracks
    - **Tempo**: overall tempo of the track in beats per minute
    - **Valence**: musical positiveness of the track, the higher the value, the more positive (happy, cheerful) it sounds, the lower the value the more
    negative (sad, angry)
    ''')
    st.markdown('## Distance')
    st.markdown('### Explanation')
    st.markdown('''
    The general idea is to compare the difference between all the features of the inputted tracks against the features of each of
    the tracks in the dataset. To do this, we use [euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance):
    ''')
    st.markdown('### Examples')
    pythagoras = Image.open('img/pythagoras.png')
    st.image(pythagoras, width=400, caption='Pythagorean theorem to compute distance in 2 dimensions')
    euclidean_distance = Image.open('img/euclidean_distance.png')
    st.image(euclidean_distance, width=600, caption='Euclidean distance for n dimensions')

    st.markdown('Where *p* and *q* are the tracks and the subindexes (*1*, *2*, ..., *i*, ..., *n*) are the features (acousticness, danceability, etc.)')
    st.markdown('## Next steps')
    st.markdown('''This is only a prototype to test how well a recommender with euclidean distance works when using the features provided in the
    Spotify API, but it may be enhanced with the following ideas:''')
    st.markdown('''
    - Improve Exploratory Analysis
    - Add more artists to diversify
    - Feed it with data from the user's [Spotify account activity](https://developer.spotify.com/documentation/web-api/reference/personalization/) instead of an inputted tracklist
    - Store the track information in a database rather than using dataframes to store the tracks
    - Clusterize the tracks with [kmeans](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html) (by genre and the features with most variance)
    - Output the recommended songs to a [Spotify playlist](https://developer.spotify.com/documentation/web-api/reference/playlists/)
    ''')

else:
    st.error('This page does not exist!')