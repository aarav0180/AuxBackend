"""
Custom exceptions for VibeSync application.
"""

from fastapi import HTTPException, status


class VibesyncException(HTTPException):
    """Base exception for VibeSync application."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
    ):
        super().__init__(status_code=status_code, detail=detail)


class RoomNotFoundError(VibesyncException):
    """Raised when a room is not found."""
    
    def __init__(self, room_code: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with code '{room_code}' not found",
        )


class SongNotFoundError(VibesyncException):
    """Raised when a song is not found in the queue."""
    
    def __init__(self, song_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID '{song_id}' not found in queue",
        )


class PermissionDeniedError(VibesyncException):
    """Raised when user doesn't have permission for an action."""
    
    def __init__(self, message: str = "You don't have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )


class ExternalAPIError(VibesyncException):
    """Raised when external API call fails."""
    
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{service} API error: {message}",
        )


class QueueFullError(VibesyncException):
    """Raised when the queue is full."""
    
    def __init__(self, max_size: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Queue is full. Maximum {max_size} songs allowed.",
        )


class QueueEmptyError(VibesyncException):
    """Raised when trying to play from an empty queue."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue is empty. Add songs to start playing.",
        )


class UserQuotaExceededError(VibesyncException):
    """Raised when user tries to add more than allowed songs."""
    
    def __init__(self, max_songs: int = 3):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User quota exceeded. You can only have {max_songs} songs pending in the queue at one time. Wait for your songs to play.",
        )


class SongTooLongError(VibesyncException):
    """Raised when song duration exceeds maximum allowed."""
    
    def __init__(self, duration: int, max_duration: int = 480):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Song too long ({duration}s). Maximum allowed duration is {max_duration} seconds (8 minutes).",
        )


class DuplicateSongError(VibesyncException):
    """Raised when trying to add duplicate or recently played song."""
    
    def __init__(self, message: str = "This song is already in the queue or was recently played"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


class DefaultRoomProtectedError(VibesyncException):
    """Raised when trying to delete the default room."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The default room cannot be deleted. It is a permanent community room.",
        )
