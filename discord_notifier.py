import math
import logging
import requests
import os
from datetime import datetime

log = logging.getLogger(__name__)

def send_discord_notification(tracks_info):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        log.warning("⚠️ DISCORD_WEBHOOK_URL not set. Skipping Discord notification.")
        return False

    if not tracks_info:
        log.info("No tracks to notify about.")
        return False

    batch_size = 10
    total_batches = math.ceil(len(tracks_info) / batch_size)

    log.info(f"🎶 Sending {len(tracks_info)} tracks to Discord ({total_batches} message{'s' if total_batches > 1 else ''})")

    success = True

    for batch_index in range(total_batches):
        start = batch_index * batch_size
        end = start + batch_size
        batch_tracks = tracks_info[start:end]

        embeds = []
        for idx, track in enumerate(batch_tracks, start + 1):
            log.info(f"🎧 {idx}. {track['name']} - {track['artists']}")

            embed = {
                "title": track["name"],
                "url": track["uri"].replace("spotify:track:", "https://open.spotify.com/track/"),
                "description": f"**Artists:** {track['artists']}\n**Released:** {track['release_date']}",
                "color": 1947988,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "Spotify Auto Playlist"},
            }
            if track.get("image_url"):
                embed["thumbnail"] = {"url": track["image_url"]}  # album cover

            embeds.append(embed)

        payload = {
            "username": "Spotify Upfront UK Hardcore Release Radar",
            "embeds": embeds
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code not in [200, 204]:
                log.error(f"❌ Discord webhook failed (batch {batch_index+1}/{total_batches}): {response.status_code} {response.text}")
                success = False
            else:
                log.info(f"✅ Sent batch {batch_index+1}/{total_batches} ({len(batch_tracks)} tracks)")
        except Exception as e:
            log.error(f"❌ Error sending Discord notification (batch {batch_index+1}): {e}")
            success = False

    return success
    
