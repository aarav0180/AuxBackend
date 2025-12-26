"""
JioSaavn API Service for fetching song data.
"""

import httpx
from typing import Optional
import logging

from src.core.config import settings
from src.core.exceptions import ExternalAPIError
from src.models.schemas import SongBase, SongDetail, SongQuality, Thumbnail, ArtistSimplified, ArtistDetailed

logger = logging.getLogger(__name__)


class JioSaavnService:
    """Service for interacting with JioSaavn API."""
    
    def __init__(self):
        self.base_url = settings.JIOSAAVN_API_BASE_URL
        self.timeout = settings.EXTERNAL_API_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _parse_song_data(self, song_data: dict) -> SongBase:
        """Parse raw song data from API response."""
        # Extract all image/thumbnail URLs (all sizes)
        thumbnails = []
        images = song_data.get("image", [])
        if isinstance(images, list):
            for idx, img in enumerate(images):
                if isinstance(img, dict):
                    url = img.get("url", "")
                    quality = img.get("quality", f"quality_{idx}")
                    thumbnails.append(Thumbnail(
                        url=url,
                        quality=quality,
                        width=None,
                        height=None,
                    ))
                elif isinstance(img, str):
                    thumbnails.append(Thumbnail(
                        url=img,
                        quality=f"quality_{idx}",
                        width=None,
                        height=None,
                    ))
        elif isinstance(images, str):
            thumbnails.append(Thumbnail(
                url=images,
                quality="default",
                width=None,
                height=None,
            ))
        
        # Fallback to default image_url
        image_url = None
        if thumbnails:
            image_url = thumbnails[-1].url  # Use highest quality as default
        
        # Extract all download URLs (all qualities)
        download_urls_list = []
        download_urls = song_data.get("downloadUrl", [])
        if isinstance(download_urls, list):
            for dl in download_urls:
                if isinstance(dl, dict):
                    url = dl.get("url", "")
                    quality = dl.get("quality", "")
                    bitrate = dl.get("bitrate")
                    if url:
                        download_urls_list.append(SongQuality(
                            quality=quality,
                            url=url,
                            bitrate=bitrate,
                        ))
                elif isinstance(dl, str):
                    download_urls_list.append(SongQuality(
                        quality="unknown",
                        url=dl,
                        bitrate=None,
                    ))
        elif isinstance(download_urls, str):
            download_urls_list.append(SongQuality(
                quality="default",
                url=download_urls,
                bitrate=None,
            ))
        
        # Fallback to single download_url
        download_url = None
        if download_urls_list:
            download_url = download_urls_list[-1].url  # Use highest quality as default
        
        # Extract artist information (simplified and detailed)
        artists_simplified = []
        artists_detailed = []
        artists_str = ""
        
        artists_data = song_data.get("artists", {})
        if isinstance(artists_data, dict):
            primary = artists_data.get("primary", [])
            featured = artists_data.get("featured", [])
            
            # Process primary artists
            for artist in primary:
                if isinstance(artist, dict):
                    artist_id = artist.get("id", "")
                    artist_name = artist.get("name", "")
                    artist_image = None
                    
                    # Extract artist image
                    artist_images = artist.get("image", [])
                    if isinstance(artist_images, list) and artist_images:
                        artist_image = artist_images[-1].get("url") if isinstance(artist_images[-1], dict) else artist_images[-1]
                    elif isinstance(artist_images, str):
                        artist_image = artist_images
                    
                    artists_simplified.append(ArtistSimplified(
                        id=artist_id,
                        name=artist_name,
                        role="primary",
                        image_url=artist_image,
                    ))
                    
                    # Create detailed artist info
                    artists_detailed.append(ArtistDetailed(
                        id=artist_id,
                        name=artist_name,
                        role="primary",
                        image_url=artist_image,
                        bio=artist.get("bio"),
                        follower_count=artist.get("followerCount"),
                        is_verified=artist.get("isVerified"),
                        url=artist.get("url"),
                    ))
            
            # Process featured artists
            for artist in featured:
                if isinstance(artist, dict):
                    artist_id = artist.get("id", "")
                    artist_name = artist.get("name", "")
                    artist_image = None
                    
                    artist_images = artist.get("image", [])
                    if isinstance(artist_images, list) and artist_images:
                        artist_image = artist_images[-1].get("url") if isinstance(artist_images[-1], dict) else artist_images[-1]
                    elif isinstance(artist_images, str):
                        artist_image = artist_images
                    
                    artists_simplified.append(ArtistSimplified(
                        id=artist_id,
                        name=artist_name,
                        role="featured",
                        image_url=artist_image,
                    ))
                    
                    artists_detailed.append(ArtistDetailed(
                        id=artist_id,
                        name=artist_name,
                        role="featured",
                        image_url=artist_image,
                        bio=artist.get("bio"),
                        follower_count=artist.get("followerCount"),
                        is_verified=artist.get("isVerified"),
                        url=artist.get("url"),
                    ))
            
            # Create comma-separated string
            all_names = [a.name for a in artists_simplified]
            artists_str = ", ".join(all_names)
            
        elif isinstance(artists_data, str):
            artists_str = artists_data
        
        # Fallback to primaryArtists field
        if not artists_str:
            artists_str = song_data.get("primaryArtists", "")
        
        # Extract album info
        album = ""
        if isinstance(song_data.get("album"), dict):
            album = song_data.get("album", {}).get("name", "")
        else:
            album = song_data.get("album", "")
        
        return SongBase(
            id=song_data.get("id", ""),
            name=song_data.get("name", song_data.get("title", "Unknown")),
            download_urls=download_urls_list,
            thumbnails=thumbnails,
            artists_simplified=artists_simplified,
            artists_detailed=artists_detailed,
            artists=artists_str,
            album=album,
            image_url=image_url,
            duration=int(song_data.get("duration", 0)),
            download_url=download_url,
        )
    
    async def search_songs(self, query: str, limit: int = 10) -> list[SongBase]:
        """
        Search for songs by query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching songs
        """
        try:
            response = await self.client.get(
                "/api/search/songs",
                params={"query": query, "limit": limit},
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response structures
            results = []
            if isinstance(data, dict):
                # Check for data.results or data.data.results
                if "data" in data:
                    inner_data = data["data"]
                    if isinstance(inner_data, dict) and "results" in inner_data:
                        results = inner_data["results"]
                    elif isinstance(inner_data, list):
                        results = inner_data
                elif "results" in data:
                    results = data["results"]
            elif isinstance(data, list):
                results = data
            
            songs = []
            for song_data in results:
                try:
                    songs.append(self._parse_song_data(song_data))
                except Exception as e:
                    logger.warning(f"Failed to parse song data: {e}")
                    continue
            
            return songs
            
        except httpx.HTTPStatusError as e:
            logger.error(f"JioSaavn API error: {e.response.status_code} - {e.response.text}")
            raise ExternalAPIError("JioSaavn", f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"JioSaavn API request failed: {e}")
            raise ExternalAPIError("JioSaavn", "Service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error in search_songs: {e}")
            raise ExternalAPIError("JioSaavn", str(e))
    
    async def get_song_details(self, song_id: str) -> Optional[SongDetail]:
        """
        Get detailed information about a song.
        
        Args:
            song_id: JioSaavn song ID
            
        Returns:
            Song details or None if not found
        """
        try:
            response = await self.client.get(f"/api/songs/{song_id}")
            response.raise_for_status()
            
            data = response.json()
            
            # Handle nested response structure
            song_data = data
            if isinstance(data, dict):
                if "data" in data:
                    inner_data = data["data"]
                    if isinstance(inner_data, list) and inner_data:
                        song_data = inner_data[0]
                    elif isinstance(inner_data, dict):
                        song_data = inner_data
            
            base_song = self._parse_song_data(song_data)
            
            return SongDetail(
                **base_song.model_dump(),
                language=song_data.get("language"),
                year=song_data.get("year"),
                play_count=song_data.get("playCount"),
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Song not found: {song_id}")
                return None
            logger.error(f"JioSaavn API error: {e.response.status_code}")
            raise ExternalAPIError("JioSaavn", f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"JioSaavn API request failed: {e}")
            raise ExternalAPIError("JioSaavn", "Service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error in get_song_details: {e}")
            raise ExternalAPIError("JioSaavn", str(e))
    
    async def get_song_suggestions(self, song_id: str, limit: int = 10) -> list[SongBase]:
        """
        Get song suggestions based on a song.
        
        Args:
            song_id: JioSaavn song ID to base suggestions on
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested songs
        """
        try:
            response = await self.client.get(
                f"/api/songs/{song_id}/suggestions",
                params={"limit": limit},
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response structures
            results = []
            if isinstance(data, dict):
                if "data" in data:
                    results = data["data"] if isinstance(data["data"], list) else []
                elif "results" in data:
                    results = data["results"]
            elif isinstance(data, list):
                results = data
            
            songs = []
            for song_data in results[:limit]:
                try:
                    songs.append(self._parse_song_data(song_data))
                except Exception as e:
                    logger.warning(f"Failed to parse suggestion: {e}")
                    continue
            
            return songs
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to get suggestions for {song_id}: {e.response.status_code}")
            return []
        except Exception as e:
            logger.warning(f"Failed to get suggestions: {e}")
            return []


# Global singleton instance
jiosaavn_service = JioSaavnService()
