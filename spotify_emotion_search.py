import json
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

import flask
from flask import Flask
from flask import request

from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)

SPOTIFY_CLIENT_ID = get_env_variable("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_env_variable("SPOTIFY_CLIENT_SECRET")

possible_emotions = ["happiness", "sadness", "excited", "angry", "calm"]

genres = ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'anime', 'black-metal', 'bluegrass', 'blues',
          'bossanova', 'brazil', 'breakbeat', 'british', 'cantopop', 'chicago-house', 'children', 'chill', 'classical',
          'club', 'comedy', 'country', 'dance', 'dancehall', 'death-metal', 'deep-house', 'detroit-techno', 'disco',
          'disney', 'drum-and-bass', 'dub', 'dubstep', 'edm', 'electro', 'electronic', 'emo', 'folk', 'forro', 'french',
          'funk', 'garage', 'german', 'gospel', 'goth', 'grindcore', 'groove', 'grunge', 'guitar', 'happy', 'hard-rock',
          'hardcore', 'hardstyle', 'heavy-metal', 'hip-hop', 'holidays', 'honky-tonk', 'house', 'idm', 'indian',
          'indie', 'indie-pop', 'industrial', 'iranian', 'j-dance', 'j-idol', 'j-pop', 'j-rock', 'jazz', 'k-pop',
          'kids', 'latin', 'latino', 'malay', 'mandopop', 'metal', 'metal-misc', 'metalcore', 'minimal-techno',
          'movies', 'mpb', 'new-age', 'new-release', 'opera', 'pagode', 'party', 'philippines-opm', 'piano', 'pop',
          'pop-film', 'post-dubstep', 'power-pop', 'progressive-house', 'psych-rock', 'punk', 'punk-rock', 'r-n-b',
          'rainy-day', 'reggae', 'reggaeton', 'road-trip', 'rock', 'rock-n-roll', 'rockabilly', 'romance', 'sad',
          'salsa', 'samba', 'sertanejo', 'show-tunes', 'singer-songwriter', 'ska', 'sleep', 'songwriter', 'soul',
          'soundtracks', 'spanish', 'study', 'summer', 'swedish', 'synth-pop', 'tango', 'techno', 'trance', 'trip-hop',
          'turkish', 'work-out', 'world-music']

# INPUT (can be changed by users)
# selected_emotion = 0  # (0 for happiness, 1 for sadness, 2 for excited, 3 for angry, 4 for calm)
# selected_genre = 2  # (from genres list above)
# How wide of range around the emotion center we should search. Could be changed by user?
variance = 0.1

happiness_point = (0.6356637143, 0.7387914286)
sadness_point = (0.3009232, 0.3649172)
excited_point = (0.4904556364, 0.6920690909)
angry_point = (0.498947, 0.66403)
calm_point = (0.2039461538, 0.03114037793)

def find_songs(selected_emotion, selected_genre):
    valence_min = 0.0
    valence_tar = 0.0
    valence_max = 0.0

    arousal_min = 0.0
    arousal_tar = 0.0
    arousal_max = 0.0

    if selected_emotion == 0:  # happy
        valence_tar = happiness_point[0]
        arousal_tar = happiness_point[1]
    elif selected_emotion == 1:  # sadness
        valence_tar = sadness_point[0]
        arousal_tar = sadness_point[1]
    elif selected_emotion == 2:  # excited
        valence_tar = excited_point[0]
        arousal_tar = excited_point[1]
    elif selected_emotion == 3:  # angry
        valence_tar = angry_point[0]
        arousal_tar = angry_point[1]
    elif selected_emotion == 4:  # calm
        valence_tar = calm_point[0]
        arousal_tar = calm_point[1]

    valence_max = valence_tar + variance
    valence_min = valence_tar - variance

    arousal_max = arousal_tar + variance
    arousal_min = arousal_tar - variance

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))

    my_kwargs = {
        "min_valence": valence_min,
        "max_valence": valence_max,
        "target_valence": valence_tar,
        "min_arousal": arousal_min,
        "max_arousal": arousal_max,
        "target_arousal": arousal_tar,
    }

    my_selected_genre = genres[selected_genre]

    this_result = spotify.recommendations(seed_genres=[my_selected_genre], kwargs=my_kwargs)

    my_tracks = this_result["tracks"]

    # for track in my_tracks:
    #     print(track["name"], track["uri"])

    return my_tracks

# "my_tracks" has the complete list of recommended tracks (default is return 20)
# In each "track" of "my_tracks", track["uri"] is the Spotify uri for that track, which can be used to reference the track.