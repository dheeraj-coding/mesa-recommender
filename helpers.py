import requests
import random


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


def get_top_artists(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_top_artists_url = "https://api.spotify.com/v1/me/top/artists?limit=20"
    resp = requests.get(get_top_artists_url, headers=headers)
    resp_parsed = resp.json()
    top_artists = []
    for artist in resp_parsed["items"]:
        top_artists.append(artist["id"])
    top_artists = random.sample(top_artists, 5)
    return top_artists


def get_top_tracks(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_top_tracks_url = "https://api.spotify.com/v1/me/top/tracks?limit=20"
    resp = requests.get(get_top_tracks_url, headers=headers)
    resp_parsed = resp.json()
    top_tracks = []
    for artist in resp_parsed["items"]:
        top_tracks.append(artist["id"])
    top_tracks = random.sample(top_tracks, 5)
    return top_tracks


def get_seed_genres(token):
    headers = {"Authorization": f"Bearer {token}"}
    get_genres_url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
    resp = requests.get(get_genres_url, headers=headers)
    resp_parsed = resp.json()
    return resp_parsed["genres"]


def get_plain_recommendations_by_artists(token, seed_artists):
    headers = {"Authorization": f"Bearer {token}"}
    get_recs_url = "https://api.spotify.com/v1/recommendations?limit=30&seed_artists={}"
    resp = requests.get(get_recs_url.format(seed_artists), headers=headers)
    resp_parsed = resp.json()
    output_tracks = []
    for track in resp_parsed["tracks"]:
        tobj = {}
        tobj["id"] = track["id"]
        tobj["name"] = track["name"].replace("\"", "\\\"")
        tobj["img_url"] = track['album']['images'][0]['url']
        tobj["uri"] = track["uri"]
        output_tracks.append(tobj)
    return output_tracks
