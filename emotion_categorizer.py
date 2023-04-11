def dist_sqr(x1, x2, y1, y2):
    return ((abs(x1 - x2))**2) + ((abs(y1 - y2))**2)

def sort_criteria(input_tuple):
    return input_tuple[1]

happiness_point = (0.6356637143,0.7387914286)
sadness_point = (0.3009232,0.3649172)
excited_point = (0.4904556364,0.6920690909)
angry_point = (0.498947,0.66403)
calm_point = (0.2039461538,0.03114037793)
#Input spotify url (also works for Spotify ID or Spotify URI)
input_url = "https://open.spotify.com/track/5xTtaWoae3wi06K5WfVUUH?si=1469ed50bde04077"

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

this_result = spotify.audio_features(tracks=[input_url])

valence_score = this_result[0]["valence"]
arousal_score = this_result[0]["energy"]

happiness_dist = dist_sqr(happiness_point[0], valence_score, happiness_point[1], arousal_score)
sadness_dist = dist_sqr(sadness_point[0], valence_score, sadness_point[1], arousal_score)
excited_dist = dist_sqr(excited_point[0], valence_score, excited_point[1], arousal_score)
angry_dist = dist_sqr(angry_point[0], valence_score, angry_point[1], arousal_score)
calm_dist = dist_sqr(calm_point[0], valence_score, calm_point[1], arousal_score)

emotion_list = [("happiness", happiness_dist), ("saddness", sadness_dist), ("exited", excited_dist), ("angry", angry_dist), ("calm", calm_dist)]

emotion_list.sort(key=sort_criteria)

# Prints out emotions from most likely emotion to least likely emotion
for this_emotion in emotion_list:
    print(this_emotion[0])
