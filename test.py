import time

import database
from models import bayesucb
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=',
# client_secret =))
#
# db = database.DBInterface('mongodb://127.0.0.1:27017/', '12345', sp)
# db.add_recommendation('7mYrw8DN9vDg1c5qqpDboC')
# db.add_recommendation('4AOPgMrdBlaLFF5dxzIhdx')
#
# db.add_rating('7mYrw8DN9vDg1c5qqpDboC', 8)
# db.add_rating('4AOPgMrdBlaLFF5dxzIhdx', 7)
# db.get_history()

# db = database.DBInterface('mongodb://127.0.0.1:27017/', '98765')
# db.add_recommendation('abcde')
# db.get_history()

user = database.User(client_id='d3e0dfeb24424090bf02738a8954b759', client_secret='412c10abb6424d5cb389ef3a85344d50',
                     connxn_string='mongodb://127.0.0.1:27017/')
user.add_song('4AOPgMrdBlaLFF5dxzIhdx')
user.add_song('2eLDUK7EkpENZkDL9O5yhz')
user.add_song('7mYrw8DN9vDg1c5qqpDboC')

user.add_rating('4AOPgMrdBlaLFF5dxzIhdx', 8)
user.add_rating('2eLDUK7EkpENZkDL9O5yhz', 7)
user.add_rating('7mYrw8DN9vDg1c5qqpDboC', 9)

# print(user.get_history_song_features())

# ucb = bayesucb.BayesUCBTrainer(user)
# ucb.train()

sp = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id='d3e0dfeb24424090bf02738a8954b759',
                                                                   client_secret='412c10abb6424d5cb389ef3a85344d50'))

predictor = bayesucb.BayesUCBPredictor(user, sp)
print(predictor.recommend())
