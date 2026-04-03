import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging

log = logging.getLogger(__name__)

class SpotifyClientManager:
    """
    Manages Spotify client with automatic token refresh for long-running processes.
    Tokens are refreshed automatically before they expire (default Spotify tokens last 1 hour).
    """
    
    def __init__(self):
        self.client_id = self._get_env_var("SPOTIFY_CLIENT_ID")
        self.client_secret = self._get_env_var("SPOTIFY_CLIENT_SECRET")
        self.refresh_token = self._get_env_var("SPOTIFY_REFRESH_TOKEN")
        
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="playlist-modify-public playlist-modify-private user-library-read",
            cache_path=".spotify_cache",
            show_dialog=False
        )
        
        self.token_info = None
        self.token_refresh_time = 0
        self._refresh_access_token()
    
    def _get_env_var(self, var_name):
        """Get environment variable or raise error if missing."""
        value = os.environ.get(var_name)
        if not value:
            raise ValueError(f"Missing required environment variable: {var_name}")
        return value
    
    def _refresh_access_token(self):
        """Refresh the access token and update the client."""
        try:
            self.token_info = self.sp_oauth.refresh_access_token(self.refresh_token)
            self.token_refresh_time = time.time()
            log.info("✅ Spotify access token refreshed successfully")
        except Exception as e:
            log.error(f"❌ Failed to refresh access token: {e}")
            raise
    
    def _check_token_expiry(self):
        """Check if token needs refresh (refresh 5 minutes before expiry)."""
        if not self.token_info:
            return True
        
        # Spotify tokens typically expire after 3600 seconds (1 hour)
        # Refresh 5 minutes (300 seconds) before expiry to be safe
        expires_in = self.token_info.get('expires_in', 3600)
        time_since_refresh = time.time() - self.token_refresh_time
        
        # Refresh if we're within 5 minutes of expiry
        if time_since_refresh >= (expires_in - 300):
            log.info(f"⏰ Token expiring soon (refreshed {int(time_since_refresh)}s ago), refreshing now...")
            return True
        
        return False
    
    def get_client(self):
        """
        Get Spotify client, automatically refreshing token if needed.
        Call this method each time before making Spotify API calls in long-running processes.
        """
        if self._check_token_expiry():
            self._refresh_access_token()
        
        return spotipy.Spotify(auth=self.token_info['access_token'])


# Global instance for easy access
_spotify_manager = None

def get_spotify_client():
    """
    Returns a Spotify client with automatic token refresh support.
    Safe to call multiple times - will reuse the same manager instance.
    """
    global _spotify_manager
    
    if _spotify_manager is None:
        _spotify_manager = SpotifyClientManager()
    
    return _spotify_manager.get_client()

def get_spotify_manager():
    """
    Returns the SpotifyClientManager instance for advanced usage.
    """
    global _spotify_manager
    
    if _spotify_manager is None:
        _spotify_manager = SpotifyClientManager()
    
    return _spotify_manager
