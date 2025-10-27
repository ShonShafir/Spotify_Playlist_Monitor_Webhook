import logging
from datetime import datetime, timezone
from auth_setup import get_spotify_manager
from discord_notifier import send_discord_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

PLAYLIST_URL = 'https://open.spotify.com/playlist/30k2noaMn8Uq9OYoY4esfI?si=dec8e41d1e764543'
LAST_CHECK_FILE = 'last_check_timestamp.txt'


def extract_playlist_id(playlist_url):
    """Extract playlist ID from Spotify URL."""
    if 'playlist/' in playlist_url:
        playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
        return playlist_id
    return playlist_url


def load_last_check_timestamp():
    """Load the last check timestamp from file."""
    try:
        with open(LAST_CHECK_FILE, 'r') as f:
            timestamp = f.read().strip()
            log.info(f"📝 Last check timestamp: {timestamp}")
            return timestamp
    except FileNotFoundError:
        log.info(f"📝 {LAST_CHECK_FILE} not found (first run)")
        return None


def save_check_timestamp(timestamp):
    """Save the current check timestamp to file."""
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(timestamp)
    log.info(f"💾 Saved check timestamp: {timestamp}")


def get_playlist_tracks(sp, playlist_id):
    """
    Get all tracks from a playlist with their added_at timestamps.
    Returns list of track dictionaries sorted by added_at (newest first).
    """
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    
    while results:
        for item in results['items']:
            if item['track'] and item['track']['id']:
                track = item['track']
                tracks.append({
                    'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
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
    
    tracks.sort(key=lambda x: x['added_at'], reverse=True)
    
    return tracks


def monitor_playlist():
    """
    Monitor a playlist for new tracks based on added_at timestamp.
    Detects tracks added anywhere in the playlist since last check.
    """
    log.info("🎵 Starting playlist monitor...")
    
    playlist_id = extract_playlist_id(PLAYLIST_URL)
    log.info(f"📋 Monitoring playlist: {playlist_id}")
    
    spotify_manager = get_spotify_manager()
    sp = spotify_manager.get_client()
    
    last_check = load_last_check_timestamp()
    
    log.info("🔍 Fetching current playlist tracks...")
    all_tracks = get_playlist_tracks(sp, playlist_id)
    
    if not all_tracks:
        log.warning("⚠️ Playlist is empty or couldn't fetch tracks")
        return
    
    current_time = datetime.now(timezone.utc).isoformat()
    
    if last_check is None:
        log.info("🆕 First run - establishing baseline")
        log.info(f"📊 Playlist currently has {len(all_tracks)} tracks")
        save_check_timestamp(current_time)
        log.info("✅ Baseline set. Future runs will detect new additions.")
        return
    
    log.info(f"🔍 Looking for tracks added after: {last_check}")
    new_tracks = []
    
    for track in all_tracks:
        if track['added_at'] > last_check:
            new_tracks.append(track)
            log.info(f"   🎵 {track['name']} - {track['artists']} (added: {track['added_at']})")
    
    if new_tracks:
        log.info(f"📊 Found {len(new_tracks)} new track(s)")
        
        tracks_info = []
        for track in new_tracks:
            tracks_info.append({
                'name': track['name'],
                'artists': track['artists'],
                'release_date': track['added_at'].split('T')[0] if 'T' in track['added_at'] else track['added_at'],
                'uri': track['uri'],
                'days_old': 0,
                'image_url': track.get('image_url')
            })
        
        save_check_timestamp(current_time)
        
        send_discord_notification(tracks_info)
        log.info("✅ Playlist monitoring complete!")
    else:
        log.info("✨ No new tracks added since last check")
        save_check_timestamp(current_time)
