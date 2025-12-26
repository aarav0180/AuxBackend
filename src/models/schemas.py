"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
from collections import deque


# ============== Song Models ==============

class SongQuality(BaseModel):
    """Song quality/bitrate with download URL."""
    quality: str  # '128kbps', '320kbps', 'lossless', etc.
    url: str
    bitrate: Optional[int] = None  # Bitrate in kbps
    
    class Config:
        from_attributes = True


class Thumbnail(BaseModel):
    """Image thumbnail with size info."""
    url: str
    quality: str  # '50x50', '150x150', '500x500', etc.
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        from_attributes = True


class ArtistSimplified(BaseModel):
    """Simplified artist information."""
    id: str
    name: str
    role: Optional[str] = None  # 'primary', 'featured', etc.
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ArtistDetailed(ArtistSimplified):
    """Detailed artist information."""
    bio: Optional[str] = None
    follower_count: Optional[int] = None
    is_verified: Optional[bool] = None
    url: Optional[str] = None
    
    class Config:
        from_attributes = True


class SongBase(BaseModel):
    """Base song information from JioSaavn."""
    id: str
    name: str
    
    # Multiple quality URLs
    download_urls: list[SongQuality] = Field(default_factory=list)
    
    # Multiple thumbnail sizes
    thumbnails: list[Thumbnail] = Field(default_factory=list)
    
    # Artist information
    artists_simplified: list[ArtistSimplified] = Field(default_factory=list)
    artists_detailed: list[ArtistDetailed] = Field(default_factory=list)
    
    # Legacy fields for backward compatibility
    artists: str = ""  # Comma-separated artist names
    album: str = ""
    image_url: Optional[str] = None  # Default/primary image
    download_url: Optional[str] = None  # Default/primary quality
    
    duration: int = 0  # Duration in seconds
    
    class Config:
        from_attributes = True


class SongDetail(SongBase):
    """Detailed song information."""
    language: Optional[str] = None
    year: Optional[str] = None
    play_count: Optional[int] = None
    

class QueuedSong(SongBase):
    """Song in the room queue with metadata."""
    queue_id: str  # Unique ID for this queue entry
    added_by_user_id: str
    added_by_username: str
    added_at: datetime = Field(default_factory=datetime.utcnow)
    

# ============== Room Models ==============

class PlaybackState(str, Enum):
    """Playback state enum."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"


class Room(BaseModel):
    """Room model for internal storage."""
    room_code: str
    host_user_id: str
    host_username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Playback state
    current_song: Optional[QueuedSong] = None
    song_start_time: Optional[datetime] = None  # When the current song started
    is_paused: bool = False
    pause_position: float = 0.0  # Position in seconds when paused
    
    # Queue
    queue: list[QueuedSong] = Field(default_factory=list)
    
    # Room members (for future use)
    members: dict[str, str] = Field(default_factory=dict)  # user_id: username
    
    # Moderation features
    recently_played: list[QueuedSong] = Field(default_factory=list)  # Last 10 played songs
    user_pending_counts: dict[str, int] = Field(default_factory=dict)  # user_id: count
    
    class Config:
        arbitrary_types_allowed = True


class RoomState(BaseModel):
    """Public room state for API response."""
    room_code: str
    host_user_id: str
    host_username: str
    created_at: datetime
    
    current_song: Optional[QueuedSong] = None
    song_start_time: Optional[datetime] = None
    is_paused: bool = False
    
    queue: list[QueuedSong] = []
    queue_length: int = 0
    member_count: int = 0


class SyncState(BaseModel):
    """Synchronization state for clients."""
    current_song: Optional[QueuedSong] = None
    server_time: datetime
    song_start_time: Optional[datetime] = None
    is_paused: bool = False
    
    # Calculated seek position (for convenience)
    seek_position_seconds: float = 0.0
    
    # All songs in queue (upcoming songs)
    next_songs: list[QueuedSong] = Field(default_factory=list)
    
    # Queue info
    queue_length: int = 0
    
    # Current member count in the room
    member_count: int = 0


# ============== Request Models ==============

class CreateRoomRequest(BaseModel):
    """Request to create a new room."""
    user_id: str = Field(..., min_length=1, description="Host user ID")
    username: str = Field(..., min_length=1, description="Host username")


class AddSongRequest(BaseModel):
    """Request to add a song to the queue."""
    jiosaavn_song_id: str = Field(..., min_length=1, description="JioSaavn song ID")
    user_id: str = Field(..., min_length=1, description="User ID adding the song")
    username: str = Field(..., min_length=1, description="Username adding the song")


class RemoveSongRequest(BaseModel):
    """Request to remove a song from queue."""
    requesting_user_id: str = Field(..., min_length=1, description="User requesting removal")


# ============== Response Models ==============

class CreateRoomResponse(BaseModel):
    """Response after creating a room."""
    success: bool = True
    room_code: str
    message: str = "Room created successfully"


class AddSongResponse(BaseModel):
    """Response after adding a song."""
    success: bool = True
    message: str = "Song added to queue"
    song: QueuedSong
    queue_position: int


class SearchSongsResponse(BaseModel):
    """Response from song search."""
    success: bool = True
    query: str
    results: list[SongBase] = []
    total: int = 0


class SongSuggestion(BaseModel):
    """Song suggestion response."""
    success: bool = True
    suggestions: list[SongBase] = []


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
