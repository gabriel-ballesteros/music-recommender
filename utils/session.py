# special script used to store the session variables because streamlit re-runs the entire recommender.py script each time a web element updates

import pandas as pd

# session variables
track_list = pd.DataFrame(columns = ['Track','Artist','Album','Year','Id'])

exclude_artists = False
less_popular_artists = False
only_in_genres = False
genres = []
from_year = 0
to_year = 2020

# session methods (getters and setters-ish)
def add_track(track):
    error = False
    if track[4] in track_list.Id.unique():
        error = True
    else:
        track_list.loc[len(track_list)] = track
    return error

def get_track_list():
    return track_list

def empty_track_list():
    track_list.drop(track_list.index, inplace=True)