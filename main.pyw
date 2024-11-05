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

# Initialize Discord Rich Presence
rpc = Presence(client_id)
rpc.connect()


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
        if (len(artist) + len(track_name)) > 127:
            artist = artist[:60]
            artist = track_name[:60]
        return {
            "artist": artist,
            "track_name": track_name,
            "album": album,
            # Add the large image URL to the return data
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
            large_image=track['large_image_url'],  # Use the extralarge image URL
            large_text=track['album']
        )
        # print(f"Updated Discord status: {track['track_name']} by {track['artist']}")
    else:
        rpc.clear()
        # print("No track currently scrobbling.")


try:
    while True:
        update_presence()
        time.sleep(interval)
except KeyboardInterrupt:
    # print("Rich Presence integration stopped.")
    rpc.clear()
