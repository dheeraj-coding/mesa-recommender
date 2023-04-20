import requests
import random
import database
import spotipy
from models import bayesucb
from dotenv import load_dotenv
from google.cloud import storage
import os


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


MIN_SONGS = 2
MONGO_URI = get_env_variable("MONGO_URI")
BUCKET_NAME = get_env_variable("BUCKET_NAME")


def get_playlist_id(playlist_context, token):
    headers = {"Authorization": f"Bearer {token}"}
    get_playlists_url = "https://api.spotify.com/v1/me/playlists?limit=50"
    resp = requests.get(get_playlists_url, headers=headers)
    resp_parsed = resp.json()

    for playlist in resp_parsed["items"]:
        if "MESA" in playlist["name"]:
            if playlist_context in playlist["name"].lower():
                return playlist["id"]
    return None


def get_markets(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_markets_url = "https://api.spotify.com/v1/markets"
    resp = requests.get(get_markets_url, headers=headers)
    resp_parsed = resp.json()
    return resp_parsed["markets"]


def get_top_artists(token, limit=5):
    headers = {"Authorization": f"Bearer {token}"}
    get_top_artists_url = "https://api.spotify.com/v1/me/top/artists?limit={}".format(limit * 2)
    resp = requests.get(get_top_artists_url, headers=headers)
    resp_parsed = resp.json()
    top_artists = []
    for artist in resp_parsed["items"]:
        top_artists.append(artist["id"])
    if len(top_artists) > limit:
        top_artists = random.sample(top_artists, limit)
    return top_artists


def get_top_tracks(token, limit=20):
    headers = {"Authorization": f"Bearer {token}"}
    get_top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?limit={limit}"
    resp = requests.get(get_top_tracks_url, headers=headers)
    resp_parsed = resp.json()
    top_tracks = []
    for artist in resp_parsed["items"]:
        top_tracks.append(artist["id"])
    top_tracks = random.sample(top_tracks, limit)
    return top_tracks


def get_seed_genres(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_genres_url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
    resp = requests.get(get_genres_url, headers=headers)
    resp_parsed = resp.json()
    return resp_parsed["genres"]


def get_plain_recommendations_by_artists(token, seed_artists, N=30):
    headers = {"Authorization": f"Bearer {token}"}
    seed_genres = get_seed_genres(token)
    if len(seed_genres) > 5:
        seed_genres = random.sample(seed_genres, 5)
    seed_genres = ",".join(seed_genres)
    toss = random.randint(0, 1)
    if toss == 0:
        get_recs_url = f"https://api.spotify.com/v1/recommendations?limit={2 * N}&seed_genres={seed_genres}"
    else:
        get_recs_url = f"https://api.spotify.com/v1/recommendations?limit={2 * N}&seed_artists={seed_artists}"
    resp = requests.get(get_recs_url, headers=headers)
    resp_parsed = resp.json()
    output_tracks = []
    for track in resp_parsed["tracks"]:
        tobj = {}
        tobj["id"] = track["id"]
        tobj["name"] = track["name"].replace("\"", "\\\"")
        tobj["img_url"] = track['album']['images'][0]['url'] if len(
            track['album']['images']) > 0 else "/static/assets/Tim.png"
        tobj["uri"] = track["uri"]
        output_tracks.append(tobj)
    output_tracks = random.sample(output_tracks, N)
    return output_tracks


def get_plain_recommendations_by_tracks(token, seed_tracks, N=30):
    headers = {"Authorization": f"Bearer {token}"}
    seed_genres = get_seed_genres(token)
    if len(seed_genres) > 5:
        seed_genres = random.sample(seed_genres, 5)
    seed_genres = ",".join(seed_genres)
    toss = random.randint(0, 1)
    if toss == 0:
        get_recs_url = f"https://api.spotify.com/v1/recommendations?limit={2 * N}&seed_tracks={seed_tracks}"
    else:
        get_recs_url = f"https://api.spotify.com/v1/recommendations?limit={2 * N}&seed_genres={seed_genres}"
    resp = requests.get(get_recs_url, headers=headers)
    resp_parsed = resp.json()
    output_tracks = []
    for track in resp_parsed["tracks"]:
        tobj = {}
        tobj["id"] = track["id"]
        tobj["name"] = track["name"].replace("\"", "\\\"")
        tobj["img_url"] = track['album']['images'][0]['url'] if len(
            track['album']['images']) > 0 else "/static/assets/Tim.png"
        tobj["uri"] = track["uri"]
        output_tracks.append(tobj)
    output_tracks = random.sample(output_tracks, N)
    return output_tracks


def load_context_and_recommend(user_id, client_id, client_secret, context, token):
    user = database.User(client_id, client_secret,
                         connxn_string=MONGO_URI, user_id=user_id)
    sp = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id, client_secret))
    predictor = bayesucb.BayesUCBPredictor(user, sp, context, token)
    recs = predictor.recommend(10)
    print("context recs:", recs)
    return recs


def get_tracks_from_id(token, ids):
    tracks = []
    headers = {"Authorization": f"Bearer {token}"}
    get_tracks_url = "https://api.spotify.com/v1/tracks/"
    for id in ids:
        resp = requests.get(get_tracks_url + id, headers=headers)
        resp_parsed = resp.json()
        track = {}
        track["id"] = resp_parsed["id"]
        track["name"] = resp_parsed["name"].replace("\"", "\\\"")
        track["img_url"] = resp_parsed['album']['images'][0]['url'] if len(
            resp_parsed['album']['images']) > 0 else "/static/assets/Tim.png"
        track["uri"] = resp_parsed["uri"]
        tracks.append(track)
    return tracks


def train_context(user_id, context, client_id, client_secret):
    user = database.User(client_id, client_secret,
                         connxn_string=MONGO_URI, user_id=user_id)
    ids = user.get_history_song_ids(context)
    if len(ids) >= MIN_SONGS:
        ucb = bayesucb.BayesUCBTrainer(user, context)
        ucb.train()
    return


def get_user_info(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_user_url = "https://api.spotify.com/v1/me"
    resp = requests.get(get_user_url, headers=headers)
    resp_parsed = resp.json()
    return resp_parsed


def upload_blob(source_file_name, dest_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(dest_file_name)

    blob.upload_from_filename(source_file_name)


def download_blob(source_file_name, dest_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(source_file_name)
    open(dest_file_name, 'w+').close()
    blob.download_to_filename(dest_file_name)


def check_if_exists_on_bucket(file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    return blob.exists()


def get_contextual_playlist(token, context, user_id, client_id, client_secret):
    user = database.User(client_id, client_secret, connxn_string=MONGO_URI, user_id=user_id)
    hist_ids = user.get_history_song_ids(context)
    print(context)
    print(len(hist_ids))
    rec_tracks = []
    if len(hist_ids) < MIN_SONGS:
        top_artists = get_top_artists(token)
        rec_tracks = get_plain_recommendations_by_artists(token, ','.join(top_artists), N=20)
    else:
        recs = load_context_and_recommend(user_id, client_id, client_secret, context, token)
        rec_tracks = get_tracks_from_id(token, recs)
    return rec_tracks
