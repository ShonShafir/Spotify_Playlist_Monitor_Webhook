import os
import logging
import requests
from datetime import datetime

log = logging.getLogger(__name__)

def send_discord_notification(tracks_info):
    """
    Send a Discord webhook notification with newly added tracks.
    
    Args:
        tracks_info: List of dictionaries containing track information:
            [
                {
                    'name': 'Track Name',
                    'artists': 'Artist 1, Artist 2',
                    'release_date': '2025-10-25',
                    'uri': 'spotify:track:...',
                    'days_old': 0
                },
                ...
            ]
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        log.warning("⚠️ DISCORD_WEBHOOK_URL not set. Skipping Discord notification.")
        return False
    
    if not tracks_info:
        log.info("No tracks to notify about.")
        return False
    
    try:
        track_count = len(tracks_info)
        
        embed = {
            "title": f"🎵 {track_count} New Track{'s' if track_count != 1 else ''} Added to Playlist!",
            "description": f"Found {track_count} new release{'s' if track_count != 1 else ''} from your followed artists.",
            "color": 1947988,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Spotify Auto Playlist"
            },
            "fields": []
        }
        
        for idx, track in enumerate(tracks_info[:25], 1):
            track_name = track['name']
            artists = track['artists']
            release_date = track['release_date']
            days_old = track.get('days_old', 'N/A')
            
            days_text = "today" if days_old == 0 else f"{days_old}d ago"
            
            field_value = f"**Artists:** {artists}\n**Released:** {release_date} ({days_text})"
            
            embed['fields'].append({
                "name": f"{idx}. {track_name}",
                "value": field_value,
                "inline": False
            })
        
        if track_count > 25:
            embed['fields'].append({
                "name": "➕ More tracks",
                "value": f"...and {track_count - 25} more tracks!",
                "inline": False
            })
        
        payload = {
            "username": "Spotify Bot",
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            log.info(f"✅ Discord notification sent successfully! ({track_count} tracks)")
            return True
        else:
            log.error(f"❌ Discord webhook failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"❌ Failed to send Discord notification: {e}")
        return False
    except Exception as e:
        log.error(f"❌ Unexpected error sending Discord notification: {e}")
        return False


def send_simple_notification(message):
    """
    Send a simple text message to Discord (fallback/utility function).
    
    Args:
        message (str): Plain text message to send
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        log.warning("⚠️ DISCORD_WEBHOOK_URL not set. Skipping Discord notification.")
        return False
    
    try:
        payload = {
            "username": "Spotify Bot",
            "content": message
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            log.info("✅ Discord notification sent successfully!")
            return True
        else:
            log.error(f"❌ Discord webhook failed with status {response.status_code}")
            return False
            
    except Exception as e:
        log.error(f"❌ Failed to send Discord notification: {e}")
        return False
