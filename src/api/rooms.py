"""
Room Management API endpoints.
"""

from fastapi import APIRouter, Query, status
from typing import Optional

from src.models.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    RoomState,
    AddSongRequest,
    AddSongResponse,
    SyncState,
    APIResponse,
    SongSuggestion,
)
from src.services.room_manager import room_manager
from src.services.jiosaavn_service import jiosaavn_service
from src.core.exceptions import ExternalAPIError, SongNotFoundError

router = APIRouter(prefix="/rooms", tags=["Rooms"])


# ==================== Room Management ====================

@router.post(
    "",
    response_model=CreateRoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Create a new listening room. The creator becomes the host.",
)
async def create_room(request: CreateRoomRequest) -> CreateRoomResponse:
    """Create a new room and return the room code."""
    room = room_manager.create_room(
        user_id=request.user_id,
        username=request.username,
    )
    
    return CreateRoomResponse(
        success=True,
        room_code=room.room_code,
        message=f"Room {room.room_code} created successfully",
    )


@router.get(
    "/{room_code}",
    response_model=RoomState,
    summary="Get room state",
    description="Get the current state of a room including queue and now playing.",
)
async def get_room(room_code: str) -> RoomState:
    """Get current room state."""
    return room_manager.get_room_state(room_code)


@router.delete(
    "/{room_code}",
    response_model=APIResponse,
    summary="Close a room",
    description="Delete/close a room. All members will be disconnected.",
)
async def delete_room(room_code: str) -> APIResponse:
    """Close and delete a room."""
    deleted = room_manager.delete_room(room_code)
    
    if deleted:
        return APIResponse(
            success=True,
            message=f"Room {room_code} closed successfully",
        )
    else:
        return APIResponse(
            success=False,
            message=f"Room {room_code} not found",
        )


# ==================== Queue Operations ====================

@router.post(
    "/{room_code}/queue",
    response_model=AddSongResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add song to queue",
    description="Add a song to the room's queue by JioSaavn song ID.",
)
async def add_to_queue(room_code: str, request: AddSongRequest) -> AddSongResponse:
    """
    Add a song to the room's queue.
    
    The song details are fetched from JioSaavn API using the provided ID.
    """
    # Fetch song details from JioSaavn
    song = await jiosaavn_service.get_song_details(request.jiosaavn_song_id)
    
    if song is None:
        raise SongNotFoundError(request.jiosaavn_song_id)
    
    # Add to queue
    queued_song, position = room_manager.add_to_queue(
        room_code=room_code,
        song=song,
        user_id=request.user_id,
        username=request.username,
    )
    
    return AddSongResponse(
        success=True,
        message=f"'{song.name}' added to queue at position {position}",
        song=queued_song,
        queue_position=position,
    )


@router.delete(
    "/{room_code}/queue/{queue_id}",
    response_model=APIResponse,
    summary="Remove song from queue",
    description="Remove a song from the queue. Only the adder or host can remove.",
)
async def remove_from_queue(
    room_code: str,
    queue_id: str,
    requesting_user_id: str = Query(..., description="User ID requesting removal"),
) -> APIResponse:
    """Remove a song from the queue."""
    removed_song = room_manager.remove_from_queue(
        room_code=room_code,
        queue_id=queue_id,
        requesting_user_id=requesting_user_id,
    )
    
    return APIResponse(
        success=True,
        message=f"'{removed_song.name}' removed from queue",
        data={"removed_song": removed_song.model_dump()},
    )


# ==================== Playback Control ====================

@router.get(
    "/{room_code}/sync",
    response_model=SyncState,
    summary="Get sync state",
    description="Get current playback sync state for synchronizing clients.",
)
async def get_sync_state(room_code: str) -> SyncState:
    """
    Get the current sync state.
    
    Frontend should calculate: seek_position = server_time - song_start_time
    This endpoint also auto-advances to next song when current song ends.
    """
    return room_manager.get_sync_state(room_code)


@router.post(
    "/{room_code}/skip",
    response_model=APIResponse,
    summary="Skip current song",
    description="Skip to the next song in queue. Host only.",
)
async def skip_song(
    room_code: str,
    requesting_user_id: str = Query(..., description="User ID requesting skip"),
) -> APIResponse:
    """Skip to the next song."""
    next_song = room_manager.skip_current(room_code, requesting_user_id)
    
    if next_song:
        return APIResponse(
            success=True,
            message=f"Now playing: {next_song.name}",
            data={"current_song": next_song.model_dump()},
        )
    else:
        return APIResponse(
            success=True,
            message="Queue is empty. Add songs to continue.",
            data={"current_song": None},
        )


@router.post(
    "/{room_code}/pause",
    response_model=APIResponse,
    summary="Toggle pause",
    description="Toggle play/pause state. Host only.",
)
async def toggle_pause(
    room_code: str,
    requesting_user_id: str = Query(..., description="User ID requesting toggle"),
) -> APIResponse:
    """Toggle pause/play state."""
    is_paused = room_manager.toggle_pause(room_code, requesting_user_id)
    
    return APIResponse(
        success=True,
        message="Paused" if is_paused else "Playing",
        data={"is_paused": is_paused},
    )


# ==================== Suggestions ====================

@router.get(
    "/{room_code}/suggestions",
    response_model=SongSuggestion,
    summary="Get song suggestions",
    description="Get song suggestions based on current/last played song.",
)
async def get_suggestions(
    room_code: str,
    limit: int = Query(default=10, ge=1, le=50),
) -> SongSuggestion:
    """
    Get song suggestions for the room.
    
    Uses the current song (or last song in queue) to generate suggestions.
    """
    room = room_manager.get_room(room_code)
    
    # Find a song to base suggestions on
    base_song_id = None
    if room.current_song:
        base_song_id = room.current_song.id
    elif room.queue:
        base_song_id = room.queue[-1].id
    
    if not base_song_id:
        return SongSuggestion(success=True, suggestions=[])
    
    try:
        suggestions = await jiosaavn_service.get_song_suggestions(base_song_id, limit)
        return SongSuggestion(success=True, suggestions=suggestions)
    except Exception:
        return SongSuggestion(success=False, suggestions=[])


# ==================== Member Management ====================

@router.post(
    "/{room_code}/join",
    response_model=APIResponse,
    summary="Join a room",
    description="Join an existing room as a listener. Returns full playback state to start streaming immediately.",
)
async def join_room(
    room_code: str,
    user_id: str = Query(..., description="User ID"),
    username: str = Query(..., description="Username"),
) -> APIResponse:
    """
    Join a room and get full playback state.
    
    Returns everything needed to start streaming:
    - current_song with all qualities, thumbnails, and artist info
    - all_stream_urls with quality options
    - seek_position_seconds (where to start playing)
    - next_songs (next 3-5 songs for preloading)
    - queue (upcoming songs)
    """
    room = room_manager.join_room(room_code, user_id, username)
    sync_state = room_manager.get_sync_state(room_code)
    
    # Prepare current song data with all details
    current_song_data = None
    if sync_state.current_song:
        current_song_data = {
            "id": sync_state.current_song.id,
            "name": sync_state.current_song.name,
            "artists": sync_state.current_song.artists,
            "album": sync_state.current_song.album,
            "duration": sync_state.current_song.duration,
            
            # Legacy fields
            "image_url": sync_state.current_song.image_url,
            "download_url": sync_state.current_song.download_url,
            
            # Enhanced fields
            "thumbnails": [t.model_dump() for t in sync_state.current_song.thumbnails],
            "download_urls": [q.model_dump() for q in sync_state.current_song.download_urls],
            "artists_simplified": [a.model_dump() for a in sync_state.current_song.artists_simplified],
            "artists_detailed": [a.model_dump() for a in sync_state.current_song.artists_detailed],
            
            "added_by": sync_state.current_song.added_by_username,
        }
    
    return APIResponse(
        success=True,
        message=f"Joined room {room_code}",
        data={
            "room_code": room.room_code,
            "host_user_id": room.host_user_id,
            "host_username": room.host_username,
            "member_count": len(room.members),
            
            # Playback state for immediate streaming
            "current_song": current_song_data,
            
            # All quality options
            "all_stream_urls": [q.model_dump() for q in sync_state.current_song.download_urls] if sync_state.current_song else [],
            
            # Primary stream URL (for backward compatibility)
            "stream_url": sync_state.current_song.download_url if sync_state.current_song else None,
            
            "seek_position_seconds": sync_state.seek_position_seconds,
            "is_paused": sync_state.is_paused,
            "server_time": sync_state.server_time.isoformat(),
            "song_start_time": sync_state.song_start_time.isoformat() if sync_state.song_start_time else None,
            
            # Next 3-5 songs for seamless playback
            "next_songs": [s.model_dump() for s in sync_state.next_songs],
            
            # Queue info
            "queue": [s.model_dump() for s in room.queue],
            "queue_length": sync_state.queue_length,
        },
    )


@router.post(
    "/{room_code}/leave",
    response_model=APIResponse,
    summary="Leave a room",
    description="Leave a room.",
)
async def leave_room(
    room_code: str,
    user_id: str = Query(..., description="User ID"),
) -> APIResponse:
    """Leave a room."""
    left = room_manager.leave_room(room_code, user_id)
    
    return APIResponse(
        success=True,
        message="Left room" if left else "User not in room",
    )


# ==================== Stream Info ====================

@router.get(
    "/{room_code}/stream",
    response_model=APIResponse,
    summary="Get stream info",
    description="Get the current audio stream URL and playback position with next songs.",
)
async def get_stream_info(room_code: str) -> APIResponse:
    """
    Get current stream information.
    
    This is the primary endpoint for clients to get:
    - stream_url: Direct audio URL to play
    - all_stream_urls: All quality options
    - seek_position_seconds: Where to seek in the audio
    - is_paused: Whether playback is paused
    - thumbnails: All thumbnail sizes
    - next_songs: Next 3-5 songs for preloading
    
    Frontend should:
    1. Call this endpoint
    2. Load the stream_url in an audio player
    3. Seek to seek_position_seconds
    4. Poll /sync periodically to stay in sync
    """
    sync_state = room_manager.get_sync_state(room_code)
    
    if not sync_state.current_song:
        return APIResponse(
            success=True,
            message="No song currently playing",
            data={
                "stream_url": None,
                "current_song": None,
                "seek_position_seconds": 0,
                "is_paused": False,
                "next_songs": [s.model_dump() for s in sync_state.next_songs],
                "queue_length": sync_state.queue_length,
            },
        )
    
    return APIResponse(
        success=True,
        message="Stream ready",
        data={
            # Primary stream URL (highest quality)
            "stream_url": sync_state.current_song.download_url,
            
            # All quality options
            "all_stream_urls": [q.model_dump() for q in sync_state.current_song.download_urls],
            
            # Current song with all details
            "current_song": {
                "id": sync_state.current_song.id,
                "name": sync_state.current_song.name,
                "artists": sync_state.current_song.artists,
                "album": sync_state.current_song.album,
                
                # Image/thumbnail (legacy)
                "image_url": sync_state.current_song.image_url,
                
                # All thumbnail sizes
                "thumbnails": [t.model_dump() for t in sync_state.current_song.thumbnails],
                
                # Artist info
                "artists_simplified": [a.model_dump() for a in sync_state.current_song.artists_simplified],
                "artists_detailed": [a.model_dump() for a in sync_state.current_song.artists_detailed],
                
                "duration": sync_state.current_song.duration,
                "added_by": sync_state.current_song.added_by_username,
            },
            
            # Playback state
            "seek_position_seconds": sync_state.seek_position_seconds,
            "is_paused": sync_state.is_paused,
            "server_time": sync_state.server_time.isoformat(),
            
            # Next 3-5 songs for seamless playback
            "next_songs": [s.model_dump() for s in sync_state.next_songs],
            "queue_length": sync_state.queue_length,
        },
    )
