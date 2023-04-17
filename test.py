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

client_id='7d3228177cf84c9c92e7a1c11ba1cd11'
client_secret='8e7201b1f8114ff2b0005bb731a46bb1'

user = database.User(client_id, client_secret,
                     connxn_string="mongodb://admin:password@0.0.0.0:27017/admin?retryWrites=true&w=majority")
                     #'mongodb://127.0.0.1:27017/')
user.add_song('4AOPgMrdBlaLFF5dxzIhdx')
user.add_song('2eLDUK7EkpENZkDL9O5yhz')
user.add_song('7mYrw8DN9vDg1c5qqpDboC')

user.add_rating('4AOPgMrdBlaLFF5dxzIhdx', 8)
user.add_rating('2eLDUK7EkpENZkDL9O5yhz', 7)
user.add_rating('7mYrw8DN9vDg1c5qqpDboC', 9)

# print(user.get_history_song_features())

ucb = bayesucb.BayesUCBTrainer(user)
ucb.train()

sp = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id ,client_secret))

predictor = bayesucb.BayesUCBPredictor(user, sp)
print(predictor.recommend())

# token stored in a user session - look at document information for basic user information