import logging
from auth_setup import get_spotify_manager
from discord_notifier import send_discord_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

PLAYLIST_URL = 'https://open.spotify.com/playlist/30k2noaMn8Uq9OYoY4esfI?si=720d843579744389'
LAST_TRACK_FILE = 'last_playlist_track.txt'


def extract_playlist_id(playlist_url):
    """Extract playlist ID from Spotify URL."""
    if 'playlist/' in playlist_url:
        playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        return playlist_id
    return playlist_url


def load_last_track_id():
    """Load the last tracked track ID from file."""
    try:
        with open(LAST_TRACK_FILE, 'r') as f:
            track_id = f.read().strip()
            log.info(f"📝 Loaded last track ID: {track_id[:20]}...")
            return track_id
    except FileNotFoundError:
        log.info(f"📝 {LAST_TRACK_FILE} not found (first run)")
        return None


def save_last_track_id(track_id):
    """Save the last track ID to file."""
    with open(LAST_TRACK_FILE, 'w') as f:
        f.write(track_id)
    log.info(f"💾 Saved last track ID: {track_id[:20]}...")


def get_playlist_tracks(sp, playlist_id):
    """
    Get all tracks from a playlist in order (newest first).
    Returns list of track dictionaries.
    """
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    
    while results:
        for item in results['items']:
            if item['track'] and item['track']['id']:
                track = item['track']
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artists': ', '.join(a['name'] for a in track['artists']),
                    'uri': track['uri'],
                    'added_at': item['added_at']
                })
        
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    return tracks


def monitor_playlist():
    """
    Monitor a playlist for new tracks.
    Checks if new tracks were added since last run and sends Discord notification.
    """
    log.info("🎵 Starting playlist monitor...")
    
    playlist_id = extract_playlist_id(PLAYLIST_URL)
    log.info(f"📋 Monitoring playlist: {playlist_id}")
    
    spotify_manager = get_spotify_manager()
    sp = spotify_manager.get_client()
    
    last_tracked_id = load_last_track_id()
    
    log.info("🔍 Fetching current playlist tracks...")
    all_tracks = get_playlist_tracks(sp, playlist_id)
    
    if not all_tracks:
        log.warning("⚠️ Playlist is empty or couldn't fetch tracks")
        return
    
    current_first_track_id = all_tracks[0]['id']
    log.info(f"🎵 Current first track: {all_tracks[0]['name']} by {all_tracks[0]['artists']}")
    
    if last_tracked_id is None:
        log.info("🆕 First run - saving current first track as baseline")
        save_last_track_id(current_first_track_id)
        log.info("✅ Baseline set. Future runs will detect new additions.")
        return
    
    if current_first_track_id == last_tracked_id:
        log.info("✨ No new tracks added since last check")
        return
    
    log.info("🎉 New tracks detected! Finding all new additions...")
    new_tracks = []
    
    for track in all_tracks:
        if track['id'] == last_tracked_id:
            log.info(f"🛑 Found last tracked track: {track['name']}")
            break
        new_tracks.append(track)
    
    if new_tracks:
        log.info(f"📊 Found {len(new_tracks)} new track(s)")
        
        tracks_info = []
        for track in new_tracks:
            log.info(f"   🎵 {track['name']} - {track['artists']}")
            tracks_info.append({
                'name': track['name'],
                'artists': track['artists'],
                'release_date': track['added_at'].split('T')[0] if 'T' in track['added_at'] else track['added_at'],
                'uri': track['uri'],
                'days_old': 0
            })
        
        save_last_track_id(current_first_track_id)
        
        send_discord_notification(tracks_info)
        log.info("✅ Playlist monitoring complete!")
    else:
        log.warning("⚠️ Couldn't find last tracked track in playlist (it may have been removed)")
        log.info("🔄 Updating baseline to current first track")
        save_last_track_id(current_first_track_id)
