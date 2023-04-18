import pymongo
import numpy as np
from datetime import datetime

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_FEATURES = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness',
                    'tempo', 'valence']


def to_datetime(date):
    """
    Converts a numpy datetime64 object to a python datetime object
    Input:
      date - a np.datetime64 object
    Output:
      DATE - a python datetime object
    """
    timestamp = ((date - np.datetime64('1970-01-01T00:00:00'))
                 / np.timedelta64(1, 's'))
    return datetime.utcfromtimestamp(timestamp)


def to_npdatetime(date):
    return np.datetime64(date)


def extract_necessary_features(features):
    result = np.array([])
    for i in SPOTIFY_FEATURES:
        result = np.append(result, features[i])
    return result

class User:
    def __init__(self, client_id, client_secret, connxn_string):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        self.client = pymongo.MongoClient(connxn_string)
        self.db = self.client['users']['user_history']
        print(self.db)
        self.userID = client_id

        self.db.update_one(
            {'userID': self.userID},
            {'$setOnInsert': {'startTime': datetime.now()}},
            upsert=True,
        )

    def timedelta_to_minute(self, delta):
        return delta.astype('timedelta64[ms]').astype('int')

    def add_song(self, song_id):
        nowTime = np.datetime64(datetime.now()) - (np.timedelta64(0, 'ms') + int(np.floor(np.random.rand() * 500)))
        self.db.update_one({'userID': self.userID},
                           {'$set': {f'history.{song_id}': {'lastListened': to_datetime(nowTime)}}}, upsert=True)

    def add_rating(self, song_id, rating):
        self.db.update_one({'userID': self.userID}, {'$set': {f'history.{song_id}.rating': rating}})

    def get_history_song_ids(self):
        user = self.db.find_one({'userID': self.userID})
        ids = user['history'].keys()
        ids = sorted(ids, key=lambda k: user['history'][k]['lastListened'])
        return ids

    def filter_required_features(self, features):
        result = np.array([])
        for i in SPOTIFY_FEATURES:
            result = np.append(result, features[i])
        return result

    def get_history_song_features(self):
        ids = self.get_history_song_ids()
        features = np.array([])

        for song_id in ids:
            result = self.sp.audio_features(song_id)[0]
            filtered = self.filter_required_features(result)
            if len(features) == 0:
                features = filtered
            else:
                features = np.vstack((features, filtered))
        return features

    def get_history_times(self):
        ids = self.get_history_song_ids()
        user = self.db.find_one({'userID': self.userID})
        times = np.array([])
        for song_id in ids:
            lastTime = user['history'][song_id]['lastListened']
            deltatime = self.timedelta_to_minute(np.datetime64(datetime.now()) - to_npdatetime(lastTime))
            times = np.append(times, deltatime)
        return times

    def get_history_ratings(self):
        ids = self.get_history_song_ids()
        user = self.db.find_one({'userID': self.userID})
        ratings = np.array([])
        for song_id in ids:
            rating = user['history'][song_id]['rating']
            ratings = np.append(ratings, rating)
        return ratings

    def merge_times(self, song_ids, times):
        user = self.db.find_one({'userID': self.userID})
        listened = user['history'].keys()
        for i, id in enumerate(song_ids):
            if id in listened:
                times[i] = user['history'][id]['lastListened']

        return times
