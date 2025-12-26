"""
Room Manager Service for handling room state and operations.
"""

import secrets
import string
import logging
from datetime import datetime
from typing import Optional
import uuid

from src.core.config import settings
from src.core.exceptions import (
    RoomNotFoundError,
    SongNotFoundError,
    PermissionDeniedError,
    QueueFullError,
    QueueEmptyError,
    UserQuotaExceededError,
    SongTooLongError,
    DuplicateSongError,
    DefaultRoomProtectedError,
)
from src.models.schemas import (
    Room,
    RoomState,
    SyncState,
    QueuedSong,
    SongDetail,
)

logger = logging.getLogger(__name__)


class RoomManager:
    """
    Manages room state, queue operations, and playback synchronization.
    
    This is an in-memory implementation for MVP.
    State is lost on server restart.
    """
    
    def __init__(self):
        # In-memory storage: room_code -> Room
        self._rooms: dict[str, Room] = {}
        
        # Create the default room that always exists
        self._create_default_room()
    
    def _create_default_room(self) -> None:
        """Create the default community room that cannot be deleted."""
        default_room = Room(
            room_code=settings.DEFAULT_ROOM_CODE,
            host_user_id=settings.DEFAULT_ROOM_HOST_ID,
            host_username=settings.DEFAULT_ROOM_HOST_NAME,
            members={settings.DEFAULT_ROOM_HOST_ID: settings.DEFAULT_ROOM_HOST_NAME},
        )
        self._rooms[settings.DEFAULT_ROOM_CODE] = default_room
        logger.info(f"🎵 Default room '{settings.DEFAULT_ROOM_CODE}' created - Community music room")
    
    def _generate_room_code(self) -> str:
        """Generate a unique room code."""
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(characters) for _ in range(settings.ROOM_CODE_LENGTH))
            if code not in self._rooms:
                return code
    
    def _generate_queue_id(self) -> str:
        """Generate a unique queue entry ID."""
        return str(uuid.uuid4())[:8]
    
    # ==================== Room Operations ====================
    
    def create_room(self, user_id: str, username: str) -> Room:
        """
        Create a new room with the given user as host.
        
        Args:
            user_id: Host user ID
            username: Host username
            
        Returns:
            Created room
        """
        room_code = self._generate_room_code()
        
        room = Room(
            room_code=room_code,
            host_user_id=user_id,
            host_username=username,
            members={user_id: username},
        )
        
        self._rooms[room_code] = room
        logger.info(f"Room created: {room_code} by {username}")
        
        return room
    
    def get_room(self, room_code: str) -> Room:
        """
        Get a room by its code.
        
        Args:
            room_code: Room code
            
        Returns:
            Room instance
            
        Raises:
            RoomNotFoundError: If room doesn't exist
        """
        room = self._rooms.get(room_code.upper())
        if not room:
            raise RoomNotFoundError(room_code)
        return room
    
    def get_room_state(self, room_code: str) -> RoomState:
        """
        Get public room state for API response.
        
        Args:
            room_code: Room code
            
        Returns:
            Public room state
        """
        room = self.get_room(room_code)
        
        return RoomState(
            room_code=room.room_code,
            host_user_id=room.host_user_id,
            host_username=room.host_username,
            created_at=room.created_at,
            current_song=room.current_song,
            song_start_time=room.song_start_time,
            is_paused=room.is_paused,
            queue=room.queue,
            queue_length=len(room.queue),
            member_count=len(room.members),
        )
    
    def delete_room(self, room_code: str) -> bool:
        """
        Delete/close a room.
        
        Args:
            room_code: Room code
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DefaultRoomProtectedError: If trying to delete the default room
        """
        room_code = room_code.upper()
        
        # Protect the default room from deletion
        if room_code == settings.DEFAULT_ROOM_CODE:
            raise DefaultRoomProtectedError()
        
        if room_code in self._rooms:
            del self._rooms[room_code]
            logger.info(f"Room deleted: {room_code}")
            return True
        return False
    
    def room_exists(self, room_code: str) -> bool:
        """Check if a room exists."""
        return room_code.upper() in self._rooms
    
    # ==================== Moderation Helpers ====================
    
    def _is_song_similar(self, song1: QueuedSong, song2: QueuedSong) -> bool:
        """
        Fuzzy match songs by ID and normalized name/artist.
        
        Args:
            song1: First song to compare
            song2: Second song to compare
            
        Returns:
            True if songs are considered the same or very similar
        """
        # Exact ID match
        if song1.id == song2.id:
            return True
        
        # Normalize and compare name + artist
        def normalize(text: str) -> str:
            return text.lower().strip().replace(" ", "")
        
        name1 = normalize(song1.name)
        name2 = normalize(song2.name)
        artist1 = normalize(song1.artists)
        artist2 = normalize(song2.artists)
        
        # If name and artist match (fuzzy), consider it a duplicate
        if name1 == name2 and artist1 == artist2:
            return True
        
        return False
    
    def _increment_user_count(self, room: Room, user_id: str) -> None:
        """Increment pending song count for a user."""
        room.user_pending_counts[user_id] = room.user_pending_counts.get(user_id, 0) + 1
    
    def _decrement_user_count(self, room: Room, user_id: str) -> None:
        """Decrement pending song count for a user."""
        if user_id in room.user_pending_counts:
            room.user_pending_counts[user_id] = max(0, room.user_pending_counts[user_id] - 1)
            # Clean up if count is 0
            if room.user_pending_counts[user_id] == 0:
                del room.user_pending_counts[user_id]
    
    def _add_to_history(self, room: Room, song: QueuedSong) -> None:
        """Add song to recently played history (max 10 items)."""
        room.recently_played.append(song)
        # Keep only last 10
        if len(room.recently_played) > 10:
            room.recently_played.pop(0)
    
    # ==================== Queue Operations ====================
    
    def add_to_queue(
        self,
        room_code: str,
        song: SongDetail,
        user_id: str,
        username: str,
    ) -> tuple[QueuedSong, int]:
        """
        Add a song to the room's queue with strict moderation checks.
        
        Args:
            room_code: Room code
            song: Song details from JioSaavn
            user_id: ID of user adding the song
            username: Username of user adding the song
            
        Returns:
            Tuple of (queued song, position in queue)
            
        Raises:
            RoomNotFoundError: If room doesn't exist
            QueueFullError: If queue is at max capacity
            UserQuotaExceededError: If user has 3+ songs pending
            SongTooLongError: If song duration > 480 seconds
            DuplicateSongError: If song is already in the current queue
        """
        room = self.get_room(room_code)
        
        # Check 1: Queue capacity
        if len(room.queue) >= settings.MAX_QUEUE_SIZE:
            raise QueueFullError(settings.MAX_QUEUE_SIZE)
        
        # Check 2: User quota (max 3 songs per user)
        user_pending = room.user_pending_counts.get(user_id, 0)
        if user_pending >= 3:
            raise UserQuotaExceededError(max_songs=3)
        
        # Check 3: Song duration limit (max 480 seconds = 8 minutes)
        if song.duration > 480:
            raise SongTooLongError(duration=song.duration, max_duration=480)
        
        # Create temporary queued song for comparison
        temp_song = QueuedSong(
            queue_id=self._generate_queue_id(),
            id=song.id,
            name=song.name,
            artists=song.artists,
            album=song.album,
            image_url=song.image_url,
            duration=song.duration,
            download_url=song.download_url,
            download_urls=song.download_urls,
            thumbnails=song.thumbnails,
            artists_simplified=song.artists_simplified,
            artists_detailed=song.artists_detailed,
            added_by_user_id=user_id,
            added_by_username=username,
        )
        
        # Check 4: Duplicate in current queue (only check pending songs, not history)
        for queued_song in room.queue:
            if self._is_song_similar(queued_song, temp_song):
                raise DuplicateSongError(f"'{song.name}' is already in the queue")
        
        # All checks passed - add to queue
        room.queue.append(temp_song)
        position = len(room.queue)
        
        # Increment user's pending count
        self._increment_user_count(room, user_id)
        
        # Auto-start playback if this is the first song and nothing is playing
        if room.current_song is None and len(room.queue) == 1:
            self._start_next_song(room)
        
        logger.info(f"Song added to queue in room {room_code}: {song.name} by {username} (pending: {room.user_pending_counts.get(user_id, 0)})")
        
        return temp_song, position
    
    def remove_from_queue(
        self,
        room_code: str,
        queue_id: str,
        requesting_user_id: str,
    ) -> QueuedSong:
        """
        Remove a song from the queue with secure deletion.
        
        Args:
            room_code: Room code
            queue_id: Queue entry ID to remove
            requesting_user_id: User requesting the removal
            
        Returns:
            Removed song
            
        Raises:
            RoomNotFoundError: If room doesn't exist
            SongNotFoundError: If song not in queue
            PermissionDeniedError: If user can't remove this song
        """
        room = self.get_room(room_code)
        
        # Find the song in queue
        song_index = None
        song = None
        for i, queued_song in enumerate(room.queue):
            if queued_song.queue_id == queue_id:
                song_index = i
                song = queued_song
                break
        
        if song is None:
            raise SongNotFoundError(queue_id)
        
        # Check permission: must be the one who added it or the host
        if (song.added_by_user_id != requesting_user_id and 
            room.host_user_id != requesting_user_id):
            raise PermissionDeniedError(
                "Only the song adder or room host can remove this song"
            )
        
        # Remove from queue
        removed_song = room.queue.pop(song_index)
        
        # Decrement user's pending count
        self._decrement_user_count(room, removed_song.added_by_user_id)
        
        logger.info(f"Song removed from queue in room {room_code}: {removed_song.name} by user {requesting_user_id}")
        
        return removed_song
    
    # ==================== Playback Operations ====================
    
    def _start_next_song(self, room: Room) -> bool:
        """
        Start playing the next song in queue.
        Updates history and decrements user count for completed song.
        
        Args:
            room: Room instance
            
        Returns:
            True if a song was started, False if queue is empty
        """
        # If there was a current song, add it to history and decrement count
        if room.current_song is not None:
            self._add_to_history(room, room.current_song)
            self._decrement_user_count(room, room.current_song.added_by_user_id)
            logger.info(f"Song completed in room {room.room_code}: {room.current_song.name}")
        
        if not room.queue:
            room.current_song = None
            room.song_start_time = None
            room.is_paused = False
            room.pause_position = 0.0
            return False
        
        # Pop first song from queue
        next_song = room.queue.pop(0)
        room.current_song = next_song
        room.song_start_time = datetime.utcnow()
        room.is_paused = False
        room.pause_position = 0.0
        
        logger.info(f"Now playing in room {room.room_code}: {next_song.name}")
        return True
    
    def skip_current(self, room_code: str, requesting_user_id: str) -> Optional[QueuedSong]:
        """
        Skip to the next song.
        
        Args:
            room_code: Room code
            requesting_user_id: User requesting skip
            
        Returns:
            The new current song, or None if queue is empty
        """
        room = self.get_room(room_code)
        
        # Only host can skip (for MVP)
        if room.host_user_id != requesting_user_id:
            raise PermissionDeniedError("Only the host can skip songs")
        
        self._start_next_song(room)
        return room.current_song
    
    def toggle_pause(self, room_code: str, requesting_user_id: str) -> bool:
        """
        Toggle pause state.
        
        Args:
            room_code: Room code
            requesting_user_id: User requesting toggle
            
        Returns:
            New pause state (True = paused)
        """
        room = self.get_room(room_code)
        
        # Only host can pause (for MVP)
        if room.host_user_id != requesting_user_id:
            raise PermissionDeniedError("Only the host can pause/resume")
        
        if room.current_song is None:
            raise QueueEmptyError()
        
        if room.is_paused:
            # Resume: adjust start time to account for pause duration
            if room.song_start_time:
                pause_duration = room.pause_position
                room.song_start_time = datetime.utcnow()
                # Adjust start time backwards to maintain position
                from datetime import timedelta
                room.song_start_time = room.song_start_time - timedelta(seconds=pause_duration)
            room.is_paused = False
        else:
            # Pause: record current position
            room.pause_position = self._calculate_seek_position(room)
            room.is_paused = True
        
        logger.info(f"Room {room_code} pause state: {room.is_paused}")
        return room.is_paused
    
    def _calculate_seek_position(self, room: Room) -> float:
        """Calculate current seek position in seconds."""
        if room.is_paused:
            return room.pause_position
        
        if room.song_start_time is None or room.current_song is None:
            return 0.0
        
        elapsed = (datetime.utcnow() - room.song_start_time).total_seconds()
        
        # Cap at song duration
        if room.current_song.duration > 0:
            elapsed = min(elapsed, room.current_song.duration)
        
        return max(0.0, elapsed)
    
    def get_sync_state(self, room_code: str) -> SyncState:
        """
        Get synchronization state for clients.
        
        Args:
            room_code: Room code
            
        Returns:
            Current sync state with next 3-5 songs
        """
        room = self.get_room(room_code)
        
        # Check if current song has ended (auto-advance)
        if room.current_song and not room.is_paused:
            seek_pos = self._calculate_seek_position(room)
            if room.current_song.duration > 0 and seek_pos >= room.current_song.duration:
                self._start_next_song(room)
        
        seek_position = self._calculate_seek_position(room)
        
        # Get all songs from queue
        next_songs = room.queue
        
        return SyncState(
            current_song=room.current_song,
            server_time=datetime.utcnow(),
            song_start_time=room.song_start_time,
            is_paused=room.is_paused,
            seek_position_seconds=seek_position,
            next_songs=next_songs,
            queue_length=len(room.queue),
            member_count=len(room.members),
        )
    
    # ==================== Member Management ====================
    
    def join_room(self, room_code: str, user_id: str, username: str) -> Room:
        """Add a member to the room."""
        room = self.get_room(room_code)
        room.members[user_id] = username
        logger.info(f"User {username} joined room {room_code}")
        return room
    
    def leave_room(self, room_code: str, user_id: str) -> bool:
        """Remove a member from the room."""
        room = self.get_room(room_code)
        if user_id in room.members:
            del room.members[user_id]
            logger.info(f"User {user_id} left room {room_code}")
            return True
        return False
    
    # ==================== Stats ====================
    
    def get_active_rooms_count(self) -> int:
        """Get count of active rooms."""
        return len(self._rooms)
    
    def get_all_room_codes(self) -> list[str]:
        """Get all active room codes."""
        return list(self._rooms.keys())


# Global singleton instance
room_manager = RoomManager()
