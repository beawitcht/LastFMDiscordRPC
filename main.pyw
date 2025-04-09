import time
import os
import requests
from pypresence import Presence
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("DISCORD_CLIENT_ID")
lfm_api_key = os.getenv("LASTFM_API_KEY")
lfm_username = os.getenv("LASTFM_USERNAME")
interval = int(os.getenv("UPDATE_INTERVAL"))
censored = int(os.getenv("PROFANITY_CENSOR"))

# Initialize Discord Rich Presence
rpc = Presence(client_id)
rpc.connect()

# censor profanities
if censored == 1:
    from profanityfilter import ProfanityFilter
    pf = ProfanityFilter()


def get_current_track(username, api_key):
    """
    Get the current track scrobbled by a user on Last.fm.
    """
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": username,
        "api_key": api_key,
        "format": "json",
        "limit": 1
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'recenttracks' not in data or 'track' not in data['recenttracks']:
        return None  # No track data available

    track_info = data['recenttracks']['track'][0]

    # Check if the track is currently playing
    if '@attr' in track_info and 'nowplaying' in track_info['@attr']:
        if censored == 1:
            artist = pf.censor(track_info['artist']['#text'])
            track_name = pf.censor(track_info['name'])
            album = pf.censor(track_info['album']['#text'])
        else:
            artist = track_info['artist']['#text']
            track_name = track_info['name']
            album = track_info['album']['#text']

        # Extract the extralarge image URL
        image_data = track_info['image']
        large_image_url = None
        for image in image_data:
            if image['size'] == 'large':
                large_image_url = image['#text']
                break

        # use placeholders if no data available
        if len(large_image_url) == 0:
            large_image_url = "https://community.mp3tag.de/uploads/default/original/2X/a/acf3edeb055e7b77114f9e393d1edeeda37e50c9.png"
        if len(artist) == 0:
            artist = "Unknown Artist"
        if len(track_name) == 0:
            track_name = "Untitled Track"
        if len(album) == 0:
            album = "Unknown Album"

        if (len(artist) + len(album)) > 120:
            artist = artist[:60]
            album = album[:60]

        if len(track_name) > 127:
            track_name = track_name[:120]

        return {
            "artist": artist,
            "track_name": track_name,
            "album": album,
            "large_image_url": large_image_url
        }
    return None  # Not currently playing a track


def update_presence():
    """
    Update the Discord Rich Presence status based on the currently playing track.
    """
    track = get_current_track(lfm_username, lfm_api_key)

    if track:
        # Set Discord RPC with track name, artist, album, and extralarge image
        rpc.update(
            details=track['track_name'],
            state=f"{track['artist']} - {track['album']}",
            large_image=track['large_image_url'],  # Use the large image URL
            large_text=track['album']
        )
        # print(f"Updated Discord status: {track['track_name']} by {track['artist']}")
    else:
        rpc.clear()
        # print("No track currently scrobbling.")


while True:
    try:
        update_presence()
        time.sleep(interval)
    except Exception:
        time.sleep(30)
    continue
