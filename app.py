import os
import json
import numpy as np
from datetime import datetime

from furl import furl
import requests

# Flask is a web framework, written in python that lets you develop web applications easily in absence of a web server 
from flask import Flask, make_response, render_template, jsonify, Response
from flask import redirect, request
from dotenv import load_dotenv
import pymongo

import contexts
import helpers
import database
import threading
import pathlib

import spotify_emotion_search

load_dotenv()  # reads your .env

# Flask-Login provides user session management for Flask. It handles the common tasks of logging in, logging out, and remembering your users’ sessions
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
)

# Create folder to store model weights
pathlib.Path("/tmp/weights/").mkdir(parents=True, exist_ok=True)


# Gets environments variable values
def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


# Copied from database.py file for outputting test user information
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


# Granting a user or application access permissions to Spotify data and features (e.g your application needs permission from a user to access their playlists)
# Spotify (Client Credentials) authorization process requires the following:
SPOTIFY_CLIENT_ID = get_env_variable("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_env_variable("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URL = get_env_variable("SPOTIFY_REDIRECT_URL")
MONGO_URI = get_env_variable("MONGO_URI")

TRAIN_THREAD_MOTIVATION = None
TRAIN_THREAD_STUDY = None
TRAIN_THREAD_WORKOUT = None
TRAIN_THREAD_GAMING = None
TRAIN_THREAD_SLEEP = None

# What previlege users should give to the app
# The app can make the following requests on behalf of the user
# Spotify API docs for other possible scopes -- Need to update scoprd
SPOTIFY_SCOPES = "user-read-private user-read-email user-read-playback-state user-read-currently-playing user-read-playback-position user-modify-playback-state app-remote-control streaming playlist-modify-public playlist-modify-private playlist-read-private ugc-image-upload user-top-read"

app = Flask(__name__)
login_manager = LoginManager(app)
app.secret_key = "super secret key"


# ORM - Mapping DB tables to Python object 
# user = UserDBObject({"name":"name", "email":email})
# user.name
# user.email
# user.get_id()
class UserDBObject:
    def __new__(cls, d=None, *args, **kwargs):
        obj = super().__new__(cls)
        obj._dict = d
        for k, v in d.items():
            # print (k, v)
            setattr(obj, k, v)
        obj.is_active = True  # Remove this later and maintain in DB
        return obj

    def to_dict(self):
        return self._dict

    def get_id(self):
        return self._id

    # user.id # because it is defined as a @property no need to call it
    @property
    def id(self):
        return self._id

    def __str__(self):
        return f"User({self.id}, auth={self.is_authenticated})"


# Interacts with mongoDB
class User:
    def __init__(self):
        print("mongodb url123", get_env_variable("MONGO_URI"))
        self.client = pymongo.MongoClient(get_env_variable("MONGO_URI"))
        self.db = self.client['users']['user_history']
        # self.db.delete_many({})

    def get_user_by_id(self, user_id):
        d = self.db.find_one({"_id": user_id})
        if not d:
            return None
        return UserDBObject(d)

    def update_user(self, _id, data):
        result = self.db.update_one(
            {'_id': _id},
            {'$setOnInsert': data},
            upsert=True
        )
        print(result)
        return self.get_user_by_id(_id)

    def add_song(self, _id, song_id):
        nowTime = np.datetime64(datetime.now()) - (np.timedelta64(0, 'ms') + int(np.floor(np.random.rand() * 500)))
        self.db.update_one({'_id': _id},
                           {'$set': {f'history.{song_id}': {'lastListened': to_datetime(nowTime)}}}, upsert=True)

    def add_rating(self, _id, song_id, rating, context):
        self.db.update_one({'_id': _id}, {
            '$set': {
                f'history.{song_id}.lastListened': getNow(),
                f'history.{song_id}.rating': rating,
                f'history.{song_id}.context': context
            }
        })


def getNow():
    return to_datetime(
        np.datetime64(datetime.now()) - (np.timedelta64(0, 'ms') + int(np.floor(np.random.rand() * 500))))


@login_manager.user_loader
def load_user(user_id):
    # when user enters the 1st time, this funciton returns None -> sets `current_user` to None
    # if user object is available then `current_user` is set to User object
    print(user_id)
    user = User().get_user_by_id(user_id)  # replace this to accomodate all users
    print(user)
    return user


def get_spotify_login_link():
    # https://developer.spotify.com/web-api/authorization-guide/#authorization-code-flow
    # constructing the URL for redirecting users on clicking login with spotify
    data = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URL,
        # "state": ,
        "scope": SPOTIFY_SCOPES,
    }
    url = "https://accounts.spotify.com/authorize"

    redirect_url = furl(url)
    redirect_url.args = data
    return redirect_url


def go_to_spotify():
    redirect_url = get_spotify_login_link()
    return redirect(redirect_url.url)


# A decorator used to tell the application which URL is associated function
@app.route("/logout/")
def logout():
    # set is_authenticated to false in DB
    # Remove current spotify token - placeholder for future code
    print("In logout === ", current_user)
    logout_user()
    User().update_user(current_user.id, {"spotify_token": None, "is_authenticated": False})

    return render_template("hello.html")


@app.route("/")
def start():
    print("current cuser ", current_user)
    print(" is authenticated", current_user.is_authenticated)
    if not (current_user and current_user.is_authenticated):
        return render_template("hello.html")
    else:
        # return redirect("https://open.spotify.com/")
        # return render_template("hello.html")
        # return redirect("/authorize")
        return redirect('/auth/login')


@app.route("/auth/token")
def authtoken():
    print("current cuser ", current_user)
    print(" is authenticated", current_user.is_authenticated)
    if not (current_user and current_user.is_authenticated):
        # return render_template("hello.html")
        # return json
        # return {
        #     "is_authenticated": False,
        # }
        access_token = current_user.spotify_token
        d = get_data(current_user.spotify_token)
        return jsonify({
            "is_authenticated": True,
            'access_token': access_token
        })
    else:
        # return redirect("https://open.spotify.com/")
        return redirect("/authorize")
        # return json object
        # return {
        #     "is_authenticated": True,
        #     "token": current_user.spotify_token,
        # }


# A decorator used to tell the application which URL is associated function
@app.route("/login")
def login():
    # The start of the application

    if not (current_user and current_user.is_authenticated):
        # If the user is not authenticated
        d = {}
        redirect_url = get_spotify_login_link()
        d["spotify_link"] = redirect_url.url
        print(redirect_url.url)
        return go_to_spotify()

    else:
        print("user already authenticated")
        d = get_data(current_user.spotify_token)

        # if the user doesn't have a spotify token redirect them to spotify again
        if d == None:
            print("redurecting to spotify")
            return go_to_spotify()
        else:
            return redirect("/authorize")
            # return redirect("https://open.spotify.com/")

    return "Something went wrong"


@app.route("/rate", methods=['POST'])
def rate():
    track_id = request.form.get("track_id")
    rate = int(request.form.get("rate"))
    context = request.form.get("context")

    # track_id rate
    user = User()

    user.add_rating(current_user.spotify_id, track_id, rate, context)
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/auth/login")
def authlogin():
    # The start of the application

    if not (current_user and current_user.is_authenticated):
        # If the user is not authenticated
        d = {}
        redirect_url = get_spotify_login_link()
        d["spotify_link"] = redirect_url.url
        print(redirect_url.url)
        return go_to_spotify()

    else:

        return go_to_spotify()
        #
        # print("user already authenticated")
        # d = get_data(current_user.spotify_token)
        #
        # # if the user doesn't have a spotify token redirect them to spotify again
        # if d is None:
        #     print("redurecting to spotify")
        #
        # else:
        #     return redirect("/authorize")
        # return redirect("https://open.spotify.com/")

    return "Something went wrong"


# A decorator used to tell the application which URL is associated function
@app.route("/current/")
def current_playing():
    # Get details of currently logged in user
    d = get_data(current_user.spotify_token)
    if d == None:
        return json.dumps({"error": "relogin"})

    return d


def get_data(spotify_token):
    # Not tested

    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {"Authorization": "Bearer {}".format(spotify_token)}
    r = requests.get(url, headers=headers)
    # TODO: the above can return a 204, and I'm not handling that
    # --> caching previous responses is a good idea?

    if r.status_code == 204:
        return {"error": "nothing_playing", "nothing_playing": True}

    parsed = r.json()

    # check if the token is still valid
    if parsed.get("item", None) == None:
        return None

    img_src = parsed["item"]["album"]["images"][0]["url"]

    # Spotify API documentation for the structure of the result
    return {
        "img_src": img_src,
        "artists": list(
            map(lambda x: {"name": x["name"], "id": x["id"]}, parsed["item"]["artists"])
        ),
        "album_name": parsed["item"]["album"]["name"],
        "track_name": parsed["item"]["name"],
        "track_ms_total": parsed["item"]["duration_ms"],
        "track_ms_progress": parsed["progress_ms"],
        "track_is_playing": parsed["is_playing"],
        "track_uri": parsed["item"]["uri"],
    }


@app.route("/back")
def go_back():
    global TRAIN_THREAD_MOTIVATION, TRAIN_THREAD_GAMING, TRAIN_THREAD_WORKOUT, TRAIN_THREAD_SLEEP, TRAIN_THREAD_STUDY
    context = request.args.get("context")
    context = context.lower()
    if context == contexts.MOTIVATION_CONTEXT:
        TRAIN_THREAD_MOTIVATION = threading.Thread(target=helpers.train_context,
                                                   args=(current_user.spotify_id, context, SPOTIFY_CLIENT_ID,
                                                         SPOTIFY_CLIENT_SECRET))
        TRAIN_THREAD_MOTIVATION.start()
    elif context == contexts.GAMING_CONTEXT:
        TRAIN_THREAD_GAMING = threading.Thread(target=helpers.train_context,
                                               args=(current_user.spotify_id, context, SPOTIFY_CLIENT_ID,
                                                     SPOTIFY_CLIENT_SECRET))
        TRAIN_THREAD_GAMING.start()
    elif context == contexts.WORKOUT_CONTEXT:
        TRAIN_THREAD_WORKOUT = threading.Thread(target=helpers.train_context,
                                                args=(current_user.spotify_id, context, SPOTIFY_CLIENT_ID,
                                                      SPOTIFY_CLIENT_SECRET))
        TRAIN_THREAD_WORKOUT.start()
    elif context == contexts.SLEEP_CONTEXT:
        TRAIN_THREAD_SLEEP = threading.Thread(target=helpers.train_context,
                                              args=(current_user.spotify_id, context, SPOTIFY_CLIENT_ID,
                                                    SPOTIFY_CLIENT_SECRET))
        TRAIN_THREAD_SLEEP.start()
    elif context == contexts.STUDY_CONTEXT:
        TRAIN_THREAD_STUDY = threading.Thread(target=helpers.train_context,
                                              args=(current_user.spotify_id, context, SPOTIFY_CLIENT_ID,
                                                    SPOTIFY_CLIENT_SECRET))
        TRAIN_THREAD_STUDY.start()
    resp = Response(status=200, mimetype='application/json')
    return resp


@app.route("/refresh_playlist")
def refresh_playlists():
    context = request.args.get("context").lower()
    token = request.args.get("token")
    user_id = request.args.get("user_id")
    print("Refresh playlists")
    print(user_id)

    rec_tracks = helpers.get_contextual_playlist(token, context, user_id, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    return json.dumps(rec_tracks)


@app.route("/playlists/<context>")
def playlists_page(context):
    token = request.args.get("token")
    user_id = request.args.get("user_id")
    data = dict()
    data['token'] = token

    rec_tracks = helpers.get_contextual_playlist(token, context, user_id, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    user_info = helpers.get_user_info(token)
    return render_template("playlist.html", name=user_info["display_name"], data=data,
                           context=context.capitalize().strip("'"),
                           tracks=rec_tracks, user_id=user_id)


@app.route("/error500")
def error500():
    return render_template("error500.html")


# A decorator used to tell the application which URL is associated function
@app.route("/authorize")
def login_callback():
    # This URL is called by spotify, depending on what's defined
    # There will be error if there is a mismatch between the URLs
    code = request.args.get("code")
    error = request.args.get("error")
    state = request.args.get("state")  # Spotfiy API docs for what are all the possible states
    # TODO: handle error cases?

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URL,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    url = "https://accounts.spotify.com/api/token"  # calling token API with `code`, client_id, client_secret

    r = requests.post(url, data=data)
    parsed = r.json()
    try:
        token = parsed[
            "access_token"]  # access_token/spotify_token for that specific user. This token should be later used for all user related activites
    except KeyError:
        print({"data": parsed, "status": "error"})
        return redirect("/")

    # get spotify user id
    url = "https://api.spotify.com/v1/me"  # accessing user profile to get displayname, email and other user indo

    print("=========url=", url, token)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        return redirect("/error500")

    # response from Spotify when we ask for user profile
    print(r.reason, r.status_code, r.text)
    parsed = r.json()

    spotify_id = parsed.pop("id")  # renaming spotfiy id to id

    data = {"spotify_id": spotify_id, "spotify_token": token, "is_active": True, "is_authenticated": True, **parsed}
    user = User()
    # get the UserDBObject for the currently logged in spotify user
    try:
        curr_user = user.update_user(current_user._id, data)
    except AttributeError:
        curr_user = user.update_user(data["spotify_id"], data)

    # user.add_song(spotify_id, '4AOPgMrdBlaLFF5dxzIhdx')
    # user.add_song(spotify_id, '2eLDUK7EkpENZkDL9O5yhz')
    # user.add_song(spotify_id, '7mYrw8DN9vDg1c5qqpDboC')

    # user.add_rating(spotify_id, '4AOPgMrdBlaLFF5dxzIhdx', 8)
    # user.add_rating(spotify_id, '2eLDUK7EkpENZkDL9O5yhz', 7)
    # user.add_rating(spotify_id,'7mYrw8DN9vDg1c5qqpDboC', 9)

    print("=========login_user==========", curr_user)

    login_user(curr_user)  # set UserDBObject to the login_manager(flask)
    print('login_user=======')
    log_info = {
        "user_id": current_user.id,
        "spotify_id": current_user.spotify_id,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "login",
        'token': token
    }
    print('log_info', log_info)

    # url2 = "https://open.spotify.com/?"
    # user_homepage = furl(url2)
    # user_homepage.args = log_info

    #  return user.get_user_by_id(spotify_id).to_dict()
    print("redirect from authorize")
    print("token", token)
    data = log_info

    # Code to create playlists for users
    # playlist_ids = check_and_create_playlists(token, curr_user._id)
    # print(playlist_ids)

    user_info = helpers.get_user_info(token)

    # Download models and keep ready
    for ctx in contexts.CONTEXTS_ARRAY:
        fname = f"{curr_user._id}_{ctx.lower()}_model.npz"

        if helpers.check_if_exists_on_bucket(fname):
            print("Bucket file exists: ", fname)
            helpers.download_blob(fname, f"/tmp/weights/{fname}")

    return render_template("profile.html", name=user_info["display_name"], is_authed=curr_user.is_authenticated,
                           data=data)
    # return redirect("https://open.spotify.com/?")


def check_and_create_playlists(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    get_playlists = "https://api.spotify.com/v1/me/playlists?limit=50"
    get_resp = requests.get(get_playlists, headers=headers)
    get_parsed = get_resp.json()
    playlists = {}
    for playlist in get_parsed["items"]:
        if "MESA" in playlist["name"]:
            if "Motivation" in playlist["name"]:
                playlists["motivation"] = playlist["id"]
            elif "Studying" in playlist["name"]:
                playlists["studying"] = playlist["id"]
    if len(playlists) == 0:
        playlist_create_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        data_list = {
            "name": "MESA - Motivation",
            "description": "A playlist of songs that will motivate you to get up and get moving!",
            "public": False,
        }
        playlist_res = requests.post(playlist_create_url, headers=headers, json=data_list)
        playlists["motivation"] = playlist_res.json()["id"]
        data_list = {
            "name": "MESA - Studying",
            "description": "A playlist of songs that will motivate you to get up and get moving!",
            "public": False,
        }
        playlist_res = requests.post(playlist_create_url, headers=headers, json=data_list)
        playlists["studying"] = playlist_res.json()["id"]
    return playlists


@app.route('/search_emotions', methods=["GET"])
def search_emotions():
    this_genre = request.args.get('genre-selection')
    this_emotion = request.args.get("emotion-selection")

    print(this_emotion, this_genre)

    my_tracks = spotify_emotion_search.find_songs(int(this_emotion), int(this_genre))

    first_ten_tracks = my_tracks[0:10]
    out_tracks = []
    for track in first_ten_tracks:
        trck = {}
        trck["name"] = track["name"].replace("\"", "\\\"")
        trck["img_url"] = track['album']['images'][0]['url'] if len(
            track['album']['images']) > 0 else "/static/assets/Tim.png"
        trck["uri"] = track["external_urls"]["spotify"]
        out_tracks.append(trck)

    return render_template("emotion_playlist.html", tracks=out_tracks)


if __name__ == "__main__":
    # app.secret_key = 'super secret key'
    # app.config['SESSION_TYPE'] = 'filesystem'
    # user = User()
    # app.debug = True
    # app.run()
    app.run(host='127.0.0.1', port=8080, debug=True)
